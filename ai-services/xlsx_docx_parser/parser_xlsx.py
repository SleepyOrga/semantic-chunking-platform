import logging
import time
from pathlib import Path
import os
import zipfile
from docling.document_converter import DocumentConverter
from docling.document_converter import DocumentConverter, ExcelFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.msexcel_backend import MsExcelDocumentBackend

def extract_images_from_xlsx(xlsx_path, images_dir, xlsx_stem):
    """
    Extract images from XLSX file using zipfile (built-in library)
    
    Args:
        xlsx_path: Path to the XLSX file
        images_dir: Directory to save images
        xlsx_stem: Stem name of the XLSX file for naming images
    
    Returns:
        int: Number of images extracted
    """
    image_count = 0
    
    try:
        # XLSX files are ZIP archives - extract images from xl/media/ folder
        with zipfile.ZipFile(xlsx_path, 'r') as xlsx_zip:
            # List all files in the XLSX archive
            for file_info in xlsx_zip.filelist:
                # Check if file is in media folder and is an image
                if file_info.filename.startswith('xl/media/') and any(
                    file_info.filename.lower().endswith(ext) 
                    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.emf', '.wmf']
                ):
                    # Extract the image
                    image_data = xlsx_zip.read(file_info.filename)
                    
                    # Get file extension
                    file_ext = Path(file_info.filename).suffix
                    if file_ext.lower() in ['.emf', '.wmf']:
                        file_ext = '.png'  # Convert vector formats to PNG for compatibility
                    
                    # Generate image filename
                    original_name = Path(file_info.filename).stem
                    image_filename = f"{xlsx_stem}_{original_name}_{image_count + 1}{file_ext}"
                    image_path = os.path.join(images_dir, image_filename)
                    
                    # Save image
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    image_count += 1
                    print(f"Extracted image: {image_filename}")
                
                # Also check for chart images in xl/charts/ folder
                elif file_info.filename.startswith('xl/charts/') and any(
                    file_info.filename.lower().endswith(ext) 
                    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                ):
                    # Extract chart image
                    image_data = xlsx_zip.read(file_info.filename)
                    file_ext = Path(file_info.filename).suffix
                    
                    # Generate chart filename
                    chart_name = Path(file_info.filename).stem
                    image_filename = f"{xlsx_stem}_chart_{chart_name}_{image_count + 1}{file_ext}"
                    image_path = os.path.join(images_dir, image_filename)
                    
                    # Save chart image
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    image_count += 1
                    print(f"Extracted chart: {image_filename}")
    
    except Exception as e:
        print(f"Error extracting images from {xlsx_path}: {e}")
    
    return image_count

def extract_xlsx_to_markdown(input_path, output_dir="Output/Excel", extract_images=True):
    """
    Extract XLSX files using docling and convert to markdown with image extraction
    
    Args:
        input_path: Path to XLSX file or directory containing XLSX files
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
    
    # Configure document converter
    converter = DocumentConverter(
        format_options={
            InputFormat.XLSX: ExcelFormatOption(
                pipeline_cls=SimplePipeline, 
                backend=MsExcelDocumentBackend
            )
        }
    )
    
    input_path = Path(input_path)
    
    # Process single file or directory
    if input_path.is_file() and input_path.suffix.lower() in ['.xlsx', '.xls']:
        files_to_process = [input_path]
    elif input_path.is_dir():
        files_to_process = list(input_path.glob("*.xlsx")) + list(input_path.glob("*.xls"))
    else:
        # If it's a single file path passed from main.py, just process it
        if str(input_path).endswith(('.xlsx', '.xls')):
            files_to_process = [input_path]
        else:
            logger.error(f"Invalid input path: {input_path}")
            return
    
    logger.info(f"Found {len(files_to_process)} Excel files to process")
    
    for xlsx_file in files_to_process:
        try:
            logger.info(f"Processing: {xlsx_file.name}")
            
            # Use docling for conversion to markdown
            result = converter.convert(xlsx_file)
            
            # Generate output filename
            output_name = xlsx_file.stem + ".md"
            output_path = os.path.join(output_dir, output_name)
            
            # Extract markdown content from docling
            markdown_content = result.document.export_to_markdown()
            
            
            # Save markdown file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            logger.info(f"Saved markdown: {output_path}")
            
            # Extract images using zipfile
            if extract_images:
                image_count = extract_images_from_xlsx(xlsx_file, images_dir, xlsx_file.stem)
                logger.info(f"Extracted {image_count} images from {xlsx_file.name}")
                
                # Add image references to markdown if images were found
                if image_count > 0:
                    # Append image section to markdown
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.write(f"\n## Extracted Images\n\n")
                        f.write(f"*{image_count} images were extracted and saved to the images folder.*\n\n")
                        
                        # List extracted images
                        image_files = [f for f in os.listdir(images_dir) if f.startswith(xlsx_file.stem)]
                        for img_file in image_files:
                            f.write(f"- ![{img_file}](images/{img_file})\n")
                        f.write("\n")
                
        except Exception as e:
            logger.error(f"Error processing {xlsx_file.name}: {e}")
    
    duration = time.time() - start
    logger.info(f"Processing completed in {duration:.2f} seconds")

def main():
    """Main function to process XLSX files"""
    # Process all XLSX files in the Assets/Excel directory
    assets_path = Path("Assets/Xlsx")
    print("Starting Excel extraction with image extraction...")
    extract_xlsx_to_markdown(assets_path, extract_images=True)
    print("Excel extraction completed!")

if __name__ == "__main__":
    main()
