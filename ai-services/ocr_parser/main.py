import os
import tempfile
import argparse
import boto3
import json
from pathlib import Path
from huggingface_hub import snapshot_download
from docling_core.types.doc import ImageRefMode, TableItem, PictureItem
import requests
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 2.0

def download_file_from_url(url):
    try:
        logging.info(f"Downloading from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        logging.info(f"Downloaded to: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logging.info(f"Failed to download file: {e}")
        return None

def upload_to_s3(local_path, bucket, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(str(local_path), bucket, s3_key)
    logging.info(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")

def process_document(input_file, output_dir, s3_bucket=None, s3_prefix=None):
    temp_file = None
    # If input_file is a URL, download it
    if isinstance(input_file, str) and input_file.startswith("http"):
        downloaded = download_file_from_url(input_file)
        if not downloaded:
            return
        temp_file = downloaded
        input_file = downloaded
    input_doc_path = Path(input_file)
    output_dir = Path(output_dir)
    logging.info("Downloading RapidOCR models")
    download_path = snapshot_download(repo_id="SWHL/RapidOCR")
    det_model_path = os.path.join(download_path, "PP-OCRv4", "en_PP-OCRv3_det_infer.onnx")
    ocr_options = RapidOcrOptions(
        det_model_path=det_model_path,
    )
    pipeline_options = PdfPipelineOptions(
        ocr_options=ocr_options,
        accelerator_options=AcceleratorOptions(num_threads=10, device=AcceleratorDevice.CPU),
        do_ocr=True,
        do_table_structure=True,
        images_scale=IMAGE_RESOLUTION_SCALE,
        generate_page_images=True,
        generate_picture_images=True,
        generate_table_images=True,
    )
    pipeline_options.table_structure_options.do_cell_matching = True
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    settings.debug.profile_pipeline_timings = True
    logging.info("Converting document...")
    conv_res = converter.convert(input_doc_path)
    doc_filename = conv_res.input.file.stem
    # Save full-page images
    for page_no, page in conv_res.document.pages.items():
        image_path = output_dir / f"{doc_filename}-{page_no}.png"
        with image_path.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")
        if s3_bucket and s3_prefix:
            upload_to_s3(image_path, s3_bucket, f"{s3_prefix}{image_path.name}")
    # Save tables and figures
    table_counter = 0
    picture_counter = 0
    for element, _ in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            table_counter += 1
            image_path = output_dir / f"{doc_filename}-table-{table_counter}.png"
            with image_path.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
            if s3_bucket and s3_prefix:
                upload_to_s3(image_path, s3_bucket, f"{s3_prefix}{image_path.name}")
        elif isinstance(element, PictureItem):
            picture_counter += 1
            image_path = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            with image_path.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
            if s3_bucket and s3_prefix:
                upload_to_s3(image_path, s3_bucket, f"{s3_prefix}{image_path.name}")
    # Save markdown
    output_md_path = output_dir / f"{doc_filename}.md"
    conv_res.document.save_as_markdown(output_md_path, image_mode=ImageRefMode.REFERENCED)
    if s3_bucket and s3_prefix:
        upload_to_s3(output_md_path, s3_bucket, f"{s3_prefix}{output_md_path.name}")
        logging.info(f"Markdown saved to: s3://{s3_bucket}/{s3_prefix}{output_md_path.name}")
        print(json.dumps({"md_s3_key": f"{s3_prefix}{output_md_path.name}"}))
    else:
        logging.info(f"Markdown saved to: {output_md_path}")
    logging.info(f"Conversion time: {conv_res.timings['pipeline_total'].times:.2f}s")
    # Clean up downloaded file if needed
    if temp_file:
        os.unlink(temp_file)
        logging.info(f"Temp file deleted: {temp_file}")

def main():
    parser = argparse.ArgumentParser(description="OCR PDF processor using Docling")
    parser.add_argument("input_path", help="Path to PDF file, image, directory, or URL")
    parser.add_argument("-o", "--output", default=None, help="Output directory (default: temp if S3, else current dir)")
    parser.add_argument("--s3-bucket", required=False, help="S3 bucket to upload results")
    parser.add_argument("--s3-prefix", required=False, help="S3 prefix (folder) for results")
    args = parser.parse_args()
    # Determine output directory
    if args.s3_bucket and args.s3_prefix:
        temp_dir = tempfile.TemporaryDirectory()
        output_dir = temp_dir.name
    elif args.output:
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.getcwd()
    # Collect files to process
    input_path = args.input_path
    files_to_process = []
    if os.path.isdir(input_path):
        # Support both PDF and image files
        file_extensions = [".pdf", ".PDF", ".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]
        for ext in file_extensions:
            files_to_process.extend(Path(input_path).glob(f"*{ext}"))
        files_to_process = sorted(files_to_process)
    else:
        if input_path.startswith("http://") or input_path.startswith("https://"):
            files_to_process = [input_path]
        elif os.path.isfile(input_path):
            files_to_process = [input_path]
        else:
            logging.info(f"Input path {input_path} does not exist or is not a file/directory/URL")
            return
    logging.info(f"Found {len(files_to_process)} file(s) to process.")
    for file_path in files_to_process:
        logging.info(f"\nProcessing {file_path}")
        try:
            process_document(str(file_path), output_dir, args.s3_bucket, args.s3_prefix)
        except Exception as e:
            logging.info(f"Error processing {file_path}: {str(e)}")
            continue
if __name__ == "__main__":
    main()
