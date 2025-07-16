import logging
import time
from pathlib import Path
import os
import argparse
import tempfile
import urllib.request

from docx import Document
from docx.document import Document as DocumentType

from docling.document_converter import DocumentConverter, WordFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.msword_backend import MsWordDocumentBackend


def extract_images_from_docx(docx_path, images_dir, docx_stem):
    image_mapping = {}
    image_count = 0
    try:
        doc = Document(docx_path)
        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.target_ref:
                try:
                    image_data = rel.target_part.blob
                    content_type = rel.target_part.content_type
                    ext = ".png"
                    if "jpeg" in content_type or "jpg" in content_type:
                        ext = ".jpg"
                    elif "gif" in content_type:
                        ext = ".gif"
                    elif "bmp" in content_type:
                        ext = ".bmp"

                    image_filename = f"{docx_stem}_image_{image_count + 1}{ext}"
                    image_path = os.path.join(images_dir, image_filename)

                    with open(image_path, "wb") as img_file:
                        img_file.write(image_data)

                    image_mapping[rel_id] = image_filename
                    image_count += 1
                    logging.info(f"🖼️ Extracted image: {image_filename}")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to extract image: {e}")
    except Exception as e:
        logging.warning(f"⚠️ python-docx error: {e}")
    return image_mapping


def process_markdown_with_images(markdown_content, image_mapping):
    if not image_mapping:
        return markdown_content

    modified_content = markdown_content
    image_list = list(image_mapping.values())

    for i, image_filename in enumerate(image_list):
        image_ref = f"![{image_filename}](images/{image_filename})"
        modified_content = modified_content.replace("<!-- image -->", image_ref, 1)

    modified_content = modified_content.replace("<!-- image -->", "")

    remaining_images = image_list[modified_content.count("!["):]
    if remaining_images:
        modified_content += "\n\n## Additional Extracted Images\n\n"
        for img_file in remaining_images:
            modified_content += f"![{img_file}](images/{img_file})\n\n"

    return modified_content


def extract_docx_to_markdown(input_path, output_dir="Output/Docx", extract_images=True):
    start = time.time()
    os.makedirs(output_dir, exist_ok=True)
    if extract_images:
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

    converter = DocumentConverter(
        format_options={
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline,
                backend=MsWordDocumentBackend
            )
        }
    )

    input_path = Path(input_path)
    if input_path.is_file() and input_path.suffix.lower() == ".docx":
        files_to_process = [input_path]
    elif input_path.is_dir():
        files_to_process = list(input_path.glob("*.docx"))
    else:
        logging.error(f"❌ Invalid input path: {input_path}")
        return

    logging.info(f"📄 Found {len(files_to_process)} DOCX files")

    for docx_file in files_to_process:
        try:
            logging.info(f"🚀 Processing {docx_file.name}")
            result = converter.convert(docx_file)

            output_name = docx_file.stem + ".md"
            output_path = os.path.join(output_dir, output_name)

            markdown_content = result.document.export_to_markdown()

            image_mapping = {}
            if extract_images:
                image_mapping = extract_images_from_docx(docx_file, images_dir, docx_file.stem)

            final_markdown = process_markdown_with_images(markdown_content, image_mapping)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)

            logging.info(f"✅ Saved markdown: {output_path}")
        except Exception as e:
            logging.error(f"🔥 Error processing {docx_file.name}: {e}")

    logging.info(f"⏱️ Completed in {time.time() - start:.2f} seconds")

def download_file_from_url(url):
    # Tạo file tạm
    temp_fd, temp_path = tempfile.mkstemp(suffix=".docx")
    os.close(temp_fd)  # Đóng file descriptor
    logging.info(f"🌐 Downloading from URL: {url}")
    urllib.request.urlretrieve(url, temp_path)
    return temp_path

def main():
    parser = argparse.ArgumentParser(description="DOCX to Markdown converter with image support")
    parser.add_argument("input_file", help="Path to DOCX file or folder or URL")
    parser.add_argument("-o", "--output", default="Output/Docx", help="Output directory")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Nếu input là URL thì tải file về trước
    input_arg = args.input_file
    if input_arg.startswith("http://") or input_arg.startswith("https://"):
        input_arg = download_file_from_url(input_arg)

    extract_docx_to_markdown(input_arg, args.output, extract_images=True)

if __name__ == "__main__":
    main()
