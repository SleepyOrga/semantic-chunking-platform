from pathlib import Path
from huggingface_hub import snapshot_download
from docling_core.types.doc import ImageRefMode, TableItem, PictureItem
import os
import tempfile
import requests
import argparse

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 2.0


def download_file_from_url(url):
    try:
        print(f"🌐 Downloading from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)

        print(f"✅ Downloaded to: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        print(f"❌ Failed to download file: {e}")
        return None


def process_document(input_file, output_dir):
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

    print("Downloading RapidOCR models")
    download_path = snapshot_download(repo_id="SWHL/RapidOCR")

    det_model_path = os.path.join(download_path, "PP-OCRv4", "en_PP-OCRv4_det_infer.onnx")

    ocr_options = RapidOcrOptions(
        det_model_path=det_model_path,
        # rec_model_path and cls_model_path can be added if needed
    )

    pipeline_options = PdfPipelineOptions(
        ocr_options=ocr_options,
        accelerator_options=AcceleratorOptions(num_threads=8, device=AcceleratorDevice.CPU),
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

    print("Converting document...")
    conv_res = converter.convert(input_doc_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = conv_res.input.file.stem

    # Save full-page images
    for page_no, page in conv_res.document.pages.items():
        image_path = output_dir / f"{doc_filename}-{page_no}.png"
        with image_path.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")

    # Save tables and figures
    table_counter = 0
    picture_counter = 0
    for element, _ in conv_res.document.iterate_items():
        if isinstance(element, TableItem):
            table_counter += 1
            image_path = output_dir / f"{doc_filename}-table-{table_counter}.png"
            with image_path.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")
        elif isinstance(element, PictureItem):
            picture_counter += 1
            image_path = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
            with image_path.open("wb") as fp:
                element.get_image(conv_res.document).save(fp, "PNG")

    # Save markdown
    output_md_path = output_dir / f"{doc_filename}.md"
    conv_res.document.save_as_markdown(output_md_path, image_mode=ImageRefMode.REFERENCED)
    print(f"Markdown saved to: {output_md_path}")
    print(f"Conversion time: {conv_res.timings['pipeline_total'].times:.2f}s")

    # Clean up downloaded file if needed
    if temp_file:
        os.unlink(temp_file)
        print(f"🧹 Temp file deleted: {temp_file}")


def main():
    parser = argparse.ArgumentParser(description="OCR PDF processor using Docling")
    parser.add_argument("input_file", help="Path to PDF file or URL")
    parser.add_argument("-o", "--output", default="All_pages_to_images", help="Output directory")
    args = parser.parse_args()

    process_document(args.input_file, args.output)


if __name__ == "__main__":
    main()
