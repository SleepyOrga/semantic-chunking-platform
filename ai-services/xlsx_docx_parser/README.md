# XLSX/DOCX Parser Service

This service handles parsing of Microsoft Excel (.xlsx) and Word (.docx) documents using the Docling library, extracting text content, images, and metadata for the semantic chunking platform.

## Features

- **Excel File Parsing**: Extract text, charts, and images from .xlsx files using Docling
- **Word Document Parsing**: Extract text content, images, and formatting from .docx files
- **Image Extraction**: Automatically extract embedded images from both Excel and Word documents
- **Markdown Conversion**: Convert documents to structured markdown format
- **Robust Error Handling**: Graceful handling of corrupted or problematic files

## Quick Start

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Run parser (processes all files in Assets/)
python main.py
```

## Setup Environment

### 1. Navigate to the parser directory
```bash
cd ai-services\xlsx_docx_parser
```

### 2. Create and activate virtual environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Or for Command Prompt
.venv\Scripts\activate.bat
```

### 3. Install requirements
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

### 4. Verify installation
```bash
python -c "import docling; from docx import Document; print('All packages installed successfully!')"
```

## Usage

```bash
# Process all documents in Assets/ directory
python main.py
```

That's it! The parser will automatically:
- Find all DOCX and XLSX files in Assets/ (recursively)
- Convert them to markdown
- Extract all images
- Save results to Output/Docx/ and Output/Xlsx/

### Manual Processing (if needed)

### Excel Parser
```python
from xlsx.parser_xlsx import extract_images_from_xlsx

# Extract images from Excel file
image_count = extract_images_from_xlsx('path/to/file.xlsx', 'output/images', 'filename')
print(f"Extracted {image_count} images")
```

### Word Parser
```python
from docx.parser_docx import extract_docx_to_markdown

# Convert DOCX to markdown with image extraction
extract_docx_to_markdown('path/to/document.docx', 'output/directory', extract_images=True)
```

### Run the parsers
```bash
# Run Word document parser
cd docx
python parser_docx.py

# Run Excel parser  
cd xlsx
python parser_xlsx.py
```

## File Structure

```
xlsx_docx_parser/
├── main.py                 # Run this file!
├── requirements.txt        # Python dependencies  
├── README.md              # This file
├── Assets/                # Put your files here (auto-created)
│   ├── Docx/             # DOCX files
│   └── Xlsx/             # XLSX files  
├── Output/               # Results appear here (auto-created)
│   ├── Docx/            # DOCX markdown output
│   └── Xlsx/            # XLSX markdown output
├── xlsx/
│   └── parser_xlsx.py     # Excel parsing logic
└── docx/
    └── parser_docx.py     # Word parsing logic
```

## Supported File Formats

### Excel Files
- `.xlsx` - Modern Excel format with full support for images and charts

### Word Documents
- `.docx` - Modern Word format with full image extraction support

## Dependencies

### Required Packages
- **docling**: Advanced document parsing and conversion library
- **python-docx**: Additional Word document manipulation capabilities

### Built-in Libraries Used
- `zipfile`: For extracting images from XLSX archives
- `pathlib`: For cross-platform path handling
- `logging`: For structured logging output
- `time`: For performance timing
- `os`: For file system operations

## Key Functions

### Excel Parser (`xlsx/parser_xlsx.py`)
- `extract_images_from_xlsx()`: Extracts images from Excel files using zipfile
- Supports various image formats: PNG, JPG, GIF, BMP, TIFF, SVG, EMF, WMF

### Word Parser (`docx/parser_docx.py`)
- `extract_images_from_docx()`: Extracts images using python-docx relationships
- `extract_docx_to_markdown()`: Full document conversion to markdown
- `main()`: Batch processing of DOCX files from Assets/Docx directory

## Configuration

### Default Directories
- **Input**: `Assets/Docx` (for batch processing)
- **Output**: `Output/Docx` (markdown files)
- **Images**: `Output/Docx/images` (extracted images)

### Logging
- Uses Python's built-in logging module
- Default level: INFO
- Provides detailed processing information

## Troubleshooting

### Common Issues

1. **Docling installation fails**
   ```bash
   # Try upgrading pip first
   python -m pip install --upgrade pip
   pip install docling
   ```

2. **Permission errors on Windows**
   ```bash
   # Run PowerShell as administrator or use:
   pip install --user -r requirements.txt
   ```

3. **DOCX files not processing**
   - Ensure files are not password protected
   - Check file permissions
   - Verify file is not corrupted

### Testing the Setup

```bash
# Test Word parser
python -c "from docx.parser_docx import extract_docx_to_markdown; print('Word parser ready')"

# Test Excel parser
python -c "from xlsx.parser_xlsx import extract_images_from_xlsx; print('Excel parser ready')"
```

## Performance Notes

- Image extraction uses efficient zipfile operations
- Batch processing supported for multiple files
- Processing time logged for performance monitoring
- Memory-efficient streaming for large files

## Development

### Adding New Features
1. Both parsers use the Docling library as the primary engine
2. Add custom extraction logic to respective parser files
3. Update requirements.txt only if new dependencies are needed
4. Test with various document formats and sizes
