import logging
import time
from pathlib import Path
import os
import zipfile
import argparse
import tempfile
import requests

from docling.document_converter import DocumentConverter, ExcelFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.msexcel_backend import MsExcelDocumentBackend


def download_file_from_url(url):
    try:
        logging.info(f"🌐 Downloading from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)

        logging.info(f"✅ Downloaded to temp file: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logging.error(f"❌ Failed to download file from URL: {e}")
        return None


def extract_images_from_xlsx(xlsx_path, images_dir, xlsx_stem):
    image_count = 0
    try:
        with zipfile.ZipFile(xlsx_path, 'r') as xlsx_zip:
            for file_info in xlsx_zip.filelist:
                if file_info.filename.startswith('xl/media/') and any(
                    file_info.filename.lower().endswith(ext)
                    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.emf', '.wmf']
                ):
                    image_data = xlsx_zip.read(file_info.filename)
                    ext = Path(file_info.filename).suffix
                    if ext.lower() in ['.emf', '.wmf']:
                        ext = '.png'
                    original_name = Path(file_info.filename).stem
                    image_filename = f"{xlsx_stem}_{original_name}_{image_count + 1}{ext}"
                    image_path = os.path.join(images_dir, image_filename)
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    image_count += 1
                    logging.info(f"🖼️ Extracted image: {image_filename}")

                elif file_info.filename.startswith('xl/charts/') and any(
                    file_info.filename.lower().endswith(ext)
                    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                ):
                    image_data = xlsx_zip.read(file_info.filename)
                    ext = Path(file_info.filename).suffix
                    chart_name = Path(file_info.filename).stem
                    image_filename = f"{xlsx_stem}_chart_{chart_name}_{image_count + 1}{ext}"
                    image_path = os.path.join(images_dir, image_filename)
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    image_count += 1
                    logging.info(f"📊 Extracted chart: {image_filename}")
    except Exception as e:
        logging.error(f"❌ Error extracting images from {xlsx_path}: {e}")
    return image_count


def extract_xlsx_to_markdown(input_path, output_dir="Output/Excel", extract_images=True):
    start = time.time()
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    if extract_images:
        os.makedirs(images_dir, exist_ok=True)

    converter = DocumentConverter(
        format_options={
            InputFormat.XLSX: ExcelFormatOption(
                pipeline_cls=SimplePipeline,
                backend=MsExcelDocumentBackend
            )
        }
    )

    temp_files = []

    # Handle URL input
    if isinstance(input_path, str) and input_path.startswith("http"):
        downloaded_path = download_file_from_url(input_path)
        if not downloaded_path:
            return
        input_path = Path(downloaded_path)
        temp_files.append(downloaded_path)
        files_to_process = [input_path]

    else:
        input_path = Path(input_path)
        if input_path.is_file() and input_path.suffix.lower() in ['.xlsx', '.xls']:
            files_to_process = [input_path]
        elif input_path.is_dir():
            files_to_process = list(input_path.glob("*.xlsx")) + list(input_path.glob("*.xls"))
        else:
            logging.error(f"❌ Invalid input path: {input_path}")
            return

    logging.info(f"📊 Found {len(files_to_process)} Excel files to process")

    for xlsx_file in files_to_process:
        try:
            logging.info(f"🚀 Processing {xlsx_file.name}")
            result = converter.convert(xlsx_file)
            markdown_content = result.document.export_to_markdown()

            output_md_path = os.path.join(output_dir, f"{xlsx_file.stem}.md")
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logging.info(f"✅ Saved markdown: {output_md_path}")

            image_count = 0
            if extract_images:
                image_count = extract_images_from_xlsx(xlsx_file, images_dir, xlsx_file.stem)

            if image_count > 0:
                with open(output_md_path, "a", encoding="utf-8") as f:
                    f.write("\n\n## Extracted Images\n\n")
                    f.write(f"*{image_count} images were extracted:*\n\n")
                    image_files = sorted([
                        img for img in os.listdir(images_dir)
                        if img.startswith(xlsx_file.stem)
                    ])
                    for img_file in image_files:
                        f.write(f"- ![{img_file}](images/{img_file})\n")
                    f.write("\n")
                logging.info(f"🖼️ Embedded {image_count} images into markdown")
        except Exception as e:
            logging.error(f"🔥 Error processing {xlsx_file.name}: {e}")

    for tf in temp_files:
        os.unlink(tf)  # Clean up downloaded temp file

    logging.info(f"⏱️ Finished in {time.time() - start:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(description="XLSX to Markdown converter with image support")
    parser.add_argument("input_file", help="Path to XLSX/XLS file or URL or folder")
    parser.add_argument("-o", "--output", default="Output/Excel", help="Output directory")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    extract_xlsx_to_markdown(args.input_file, args.output, extract_images=True)


if __name__ == "__main__":
    main()
