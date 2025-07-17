import os
import tempfile
import argparse
import boto3
from pathlib import Path
import requests
import logging
import json

# Assume you have a function extract_xlsx_to_markdown similar to extract_docx_to_markdown
from docling.document_converter import DocumentConverter, ExcelFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.msexcel_backend import MsExcelDocumentBackend

def download_file_from_url(url):
    try:
        logging.info(f"Downloading from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
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

def extract_xlsx_to_markdown(input_path, output_dir, s3_bucket=None, s3_prefix=None):
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    converter = DocumentConverter(
        format_options={
            InputFormat.XLSX: ExcelFormatOption(
                pipeline_cls=SimplePipeline,
                backend=MsExcelDocumentBackend
            )
        }
    )
    input_path = Path(input_path)
    if input_path.is_file() and input_path.suffix.lower() == ".xlsx":
        files_to_process = [input_path]
    elif input_path.is_dir():
        files_to_process = list(input_path.glob("*.xlsx"))
    else:
        logging.info(f"Invalid input path: {input_path}")
        return
    logging.info(f"Found {len(files_to_process)} XLSX files")
    for xlsx_file in files_to_process:
        try:
            logging.info(f"Processing {xlsx_file.name}")
            result = converter.convert(xlsx_file)
            output_name = xlsx_file.stem + ".md"
            output_path = os.path.join(output_dir, output_name)
            markdown_content = result.document.export_to_markdown()
            # Save markdown
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logging.info(f"✅ Saved markdown: {output_path}")
            # S3 upload logic
            if s3_bucket and s3_prefix:
                upload_to_s3(output_path, s3_bucket, f"{s3_prefix}{Path(output_path).name}")
                # Upload images if any
                if os.path.isdir(images_dir):
                    for img_file in os.listdir(images_dir):
                        img_path = os.path.join(images_dir, img_file)
                        if os.path.isfile(img_path):
                            upload_to_s3(img_path, s3_bucket, f"{s3_prefix}images/{img_file}")
                print(json.dumps({"md_s3_key": f"{s3_prefix}{Path(output_path).name}"}))
        except Exception as e:
            logging.info(f"Error processing {xlsx_file.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="XLSX to Markdown converter with image support")
    parser.add_argument("input_path", help="Path to XLSX file, folder, or URL")
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
        files_to_process = list(Path(input_path).glob("*.xlsx"))
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
            # If file_path is a URL, download first
            local_path = file_path
            if isinstance(file_path, str) and (file_path.startswith("http://") or file_path.startswith("https://")):
                local_path = download_file_from_url(file_path)
            extract_xlsx_to_markdown(str(local_path), output_dir, args.s3_bucket, args.s3_prefix)
        except Exception as e:
            logging.info(f"Error processing {file_path}: {str(e)}")
            continue
if __name__ == "__main__":
    main()
