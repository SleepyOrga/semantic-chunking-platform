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

# 2. Run parsers individually
python parser_docx.py    # Process DOCX files
python parser_xlsx.py    # Process XLSX files
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
# Process DOCX files (looks in Assets/Docx/ directory)
python parser_docx.py

# Process XLSX files (looks in Assets/Xlsx/ directory)  
python parser_xlsx.py
```

Each parser will automatically:
- Find files in their respective Assets/ subdirectory
- Convert them to markdown
- Extract all images
- Save results to Output/Docx/ or Output/Xlsx/

### Manual Processing (advanced usage)

### Excel Parser
```python
from parser_xlsx import extract_xlsx_to_markdown

# Convert XLSX to markdown with image extraction
extract_xlsx_to_markdown('path/to/file.xlsx', 'output/directory', extract_images=True)
```

### Word Parser
```python
from parser_docx import extract_docx_to_markdown

# Convert DOCX to markdown with image extraction
extract_docx_to_markdown('path/to/document.docx', 'output/directory', extract_images=True)
```

### Run the parsers
```bash
# Run Word document parser
python parser_docx.py

# Run Excel parser
python parser_xlsx.py
```

## File Structure

```
xlsx_docx_parser/
├── parser_docx.py          # DOCX parser - run this for Word files
├── parser_xlsx.py          # XLSX parser - run this for Excel files
├── requirements.txt        # Python dependencies  
├── README.md              # This file
├── Assets/                # Put your files here (auto-created)
│   ├── Docx/             # Place DOCX files here
│   └── Xlsx/             # Place XLSX files here
└── Output/               # Results appear here (auto-created)
    ├── Docx/            # DOCX markdown output
    │   └── images/      # Extracted DOCX images
    └── Xlsx/            # XLSX markdown output
        └── images/      # Extracted XLSX images
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

### Excel Parser (`parser_xlsx.py`)
- `extract_images_from_xlsx()`: Extracts images from Excel files using zipfile
- `extract_xlsx_to_markdown()`: Full Excel to markdown conversion
- `main()`: Batch processing of XLSX files from Assets/Xlsx directory
- Supports various image formats: PNG, JPG, GIF, BMP, TIFF, SVG, EMF, WMF

### Word Parser (`parser_docx.py`)
- `extract_images_from_docx()`: Extracts images using python-docx relationships
- `extract_docx_to_markdown()`: Full document conversion to markdown
- `main()`: Batch processing of DOCX files from Assets/Docx directory

## Configuration

### Default Directories
- **Input**: `Assets/Docx` and `Assets/Xlsx` (for respective file types)
- **Output**: `Output/Docx` and `Output/Xlsx` (markdown files)
- **Images**: `Output/*/images` (extracted images)

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
python -c "from parser_docx import extract_docx_to_markdown; print('Word parser ready')"

# Test Excel parser
python -c "from parser_xlsx import extract_xlsx_to_markdown; print('Excel parser ready')"
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

### Workflow
1. Place your DOCX files in `Assets/Docx/`
2. Place your XLSX files in `Assets/Xlsx/`
3. Run `python parser_docx.py` for Word documents
4. Run `python parser_xlsx.py` for Excel documents
5. Check results in `Output/Docx/` and `Output/Xlsx/`
