import logging
import time
from pathlib import Path

from docling.document_converter import DocumentConverter, WordFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.msword_backend import MsWordDocumentBackend

from docx import Document
from docx.document import Document as DocumentType
import os

def extract_images_from_docx(docx_path, images_dir, docx_stem):
    """
    Extract images from DOCX file and return image mapping
    
    Args:
        docx_path: Path to the DOCX file
        images_dir: Directory to save images
        docx_stem: Stem name of the DOCX file for naming images
    
    Returns:
        dict: Mapping of image relationship IDs to filenames
    """
    image_mapping = {}
    image_count = 0
    
    try:
        doc = Document(docx_path)
        
        # Extract images from document relationships
        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.target_ref:
                try:
                    # Get image data
                    image_data = rel.target_part.blob
                    
                    # Determine file extension based on content type
                    content_type = rel.target_part.content_type
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'bmp' in content_type:
                        ext = '.bmp'
                    else:
                        ext = '.png'  # default
                    
                    # Generate unique filename
                    image_filename = f"{docx_stem}_image_{image_count + 1}{ext}"
                    image_path = os.path.join(images_dir, image_filename)
                    
                    # Save image
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    # Store mapping
                    image_mapping[rel_id] = image_filename
                    image_count += 1
                    print(f"Extracted image: {image_filename}")
                
                except Exception as e:
                    print(f"Warning: Could not extract image: {e}")
    
    except Exception as e:
        print(f"Warning: python-docx extraction failed: {e}")
    
    return image_mapping

def process_markdown_with_images(markdown_content, image_mapping):
    """
    Process markdown content and insert image references in correct positions
    
    Args:
        markdown_content: Original markdown content from docling
        image_mapping: Dictionary mapping image IDs to filenames
    
    Returns:
        str: Modified markdown with image references
    """
    if not image_mapping:
        return markdown_content
    
    modified_content = markdown_content
    image_list = list(image_mapping.values())
    
    # Replace <!-- image --> comments with actual image references
    for i, image_filename in enumerate(image_list):
        image_ref = f"![{image_filename}](images/{image_filename})"
        
        # Replace the first occurrence of <!-- image --> with the actual image
        if "<!-- image -->" in modified_content:
            modified_content = modified_content.replace("<!-- image -->", image_ref, 1)
    
    # If there are still <!-- image --> comments but no more images, remove them
    modified_content = modified_content.replace("<!-- image -->", "")
    
    # If there are remaining images that weren't placed, add them at the end
    remaining_images = image_list[modified_content.count("!["):]
    if remaining_images:
        modified_content += "\n\n## Additional Extracted Images\n\n"
        for img_file in remaining_images:
            modified_content += f"![{img_file}](images/{img_file})\n\n"
    
    return modified_content

def extract_docx_to_markdown(input_path, output_dir="Output/Docx", extract_images=True):
    """
    Extract DOCX files using docling and convert to markdown with image extraction
    
    Args:
        input_path: Path to DOCX file or directory containing DOCX files
        output_dir: Directory to save markdown files and images
        extract_images: Whether to extract images from the document
    """
    start = time.time()
    
    # Get logger (don't reconfigure if already set up)
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    if extract_images:
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
    
    # Configure document converter with image extraction options
    converter = DocumentConverter(
        format_options={
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline, 
                backend=MsWordDocumentBackend
            )
        }
    )
    
    input_path = Path(input_path)
    
    # Process single file or directory
    if input_path.is_file() and input_path.suffix.lower() == '.docx':
        files_to_process = [input_path]
    elif input_path.is_dir():
        files_to_process = list(input_path.glob("*.docx"))
    else:
        # If it's a single file path passed from main.py, just process it
        if str(input_path).endswith('.docx'):
            files_to_process = [input_path]
        else:
            logger.error(f"Invalid input path: {input_path}")
            return
    
    logger.info(f"Found {len(files_to_process)} DOCX files to process")
    
    for docx_file in files_to_process:
        try:
            logger.info(f"Processing: {docx_file.name}")
            
            # Convert the DOCX file
            result = converter.convert(docx_file)
            
            # Generate output filename
            output_name = docx_file.stem + ".md"
            output_path = os.path.join(output_dir, output_name)
            
            # Extract markdown content
            markdown_content = result.document.export_to_markdown()
            
            # Extract images and get mapping
            image_mapping = {}
            if extract_images:
                image_mapping = extract_images_from_docx(docx_file, images_dir, docx_file.stem)
                logger.info(f"Extracted {len(image_mapping)} images from {docx_file.name}")
            
            # Process markdown with image references in correct positions
            final_markdown = process_markdown_with_images(markdown_content, image_mapping)
            
            # Save markdown file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)
            
            logger.info(f"Saved markdown: {output_path}")
            if image_mapping:
                logger.info(f"Images embedded in correct positions within markdown")
        except Exception as e:
            logger.error(f"Error processing {docx_file.name}: {e}")
    
    duration = time.time() - start
    logger.info(f"Processing completed in {duration:.2f} seconds")

def main():
    """Main function to process DOCX files"""
    # Process all DOCX files in the Assets/Docx directory
    assets_path = Path("Assets/Docx")
    
    if not assets_path.exists():
        print(f"Assets directory not found: {assets_path}")
        return
    
    print("Starting DOCX extraction with image extraction...")
    extract_docx_to_markdown(assets_path, extract_images=True)
    print("DOCX extraction completed!")

if __name__ == "__main__":
    main()
