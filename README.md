# 📄 Document Processing Platform

A scalable and modular platform for **multi-format document upload**, **semantic chunking**, **AI-powered tagging**, and **intelligent search** using advanced AI and event-driven architecture.

## 🎯 Key Features

- 📋 **Multi-Format Document Processing** - Excel, Word, PDF, scanned images, and more
- 🧠 **AI-Powered Semantic Chunking** - Intelligent content segmentation using LLMs
- 🏷️ **Automated Tagging & Classification** - Smart document categorization
- 🔍 **Advanced Search & Retrieval** - Vector-based semantic search
- ⚡ **Real-time Processing** - Event-driven architecture with RabbitMQ
- 🐳 **Containerized & Scalable** - Docker-based microservices architecture

---

## 📚 Supported Document Formats

Our platform supports comprehensive document processing across multiple formats:

### 📊 **Spreadsheet Documents**
- **Excel Files** (.xlsx, .xls) - Complete sheet processing with cell-level extraction
- **CSV Files** (.csv) - Structured data parsing and semantic chunking
- **Google Sheets** - Via export/import functionality

### 📝 **Text Documents**
- **Word Documents** (.docx, .doc) - Full text extraction with formatting preservation
- **Plain Text** (.txt, .md) - Direct processing with semantic segmentation
- **Rich Text Format** (.rtf) - Advanced text formatting support

### 📄 **PDF Documents**
- **Text-based PDFs** - Direct text extraction and processing
- **Scanned PDFs** - OCR processing for digitized content
- **Complex Layouts** - Table and image extraction capabilities
- **Multi-page Processing** - Batch processing with page-level chunking

### 🖼️ **Image Documents (OCR)**
- **Scanned Documents** (.jpg, .jpeg, .png, .tiff, .bmp)
- **Screenshots** - Text extraction from application screenshots
- **Handwritten Notes** - Advanced OCR for handwriting recognition
- **Multi-language Support** - OCR processing in multiple languages

### 🌐 **Web Content**
- **HTML Pages** - Web scraping and content extraction
- **Markdown Files** (.md) - Direct parsing with structure preservation

### 📋 **Structured Data**
- **JSON Files** - Structured data processing and chunking
- **XML Documents** - Hierarchical data extraction
- **YAML Files** - Configuration and data file processing

---

## 🏗️ Architecture Overview

### **Processing Pipeline**
```
Document Upload → Format Detection → Parser Selection → Content Extraction → 
Semantic Chunking → AI Tagging → Embedding Generation → Vector Storage → Search Index
```

### **Microservices**

This monorepo includes:

| Service                       | Technology | Description                                 |
|-------------------------------|------------|---------------------------------------------|
| **Frontend**                  | React + MUI| User interface for document management      |
| **Backend API**               | NestJS     | REST API with PostgreSQL & S3 integration  |
| **Chunking Agent**            | Python/LLM | Semantic document segmentation              |
| **Tagging Agent**             | Python/LLM | AI-powered content classification           |
| **Embedding Service**         | Python     | Vector embedding generation                 |
| **OCR Parser**                | Python/OCR | Image and scanned document processing       |
| **XLSX/DOCX Parser**          | Python     | Microsoft Office document processing        |
| **Retrieval Service**         | Python     | Semantic search and ranking                 |

### **Core Components**

| Path                          | Purpose                                     |
|-------------------------------|---------------------------------------------|
| `frontend/`                   | React application with Material-UI         |
| `backend/`                    | NestJS API server                          |
| `ai-services/chunking_agent/` | LLM-powered semantic chunking              |
| `ai-services/tagging_agent/`  | Document classification and tagging        |
| `ai-services/embedding_agent/`| Vector embedding generation                |
| `ai-services/ocr_parser/`     | OCR processing for images and scanned docs |
| `ai-services/xlsx_docx_parser/`| Office document format parsing           |
| `ai-services/retrieval_service/`| Search and retrieval functionality      |

---

## 🔧 Technology Stack

### **Backend Technologies**
- **API Framework**: NestJS with TypeScript
- **Database**: PostgreSQL with pgVector for embeddings
- **Object Storage**: AWS S3 for document storage
- **Message Queue**: RabbitMQ for event-driven processing
- **Authentication**: JWT-based authentication system

### **AI & Machine Learning**
- **Language Models**: Integration with modern LLMs for chunking and tagging
- **Vector Embeddings**: Advanced embedding models for semantic search
- **OCR Engine**: Optical character recognition for image processing
- **Document Processing**: Specialized parsers for each document format

### **Frontend Technologies**
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) for modern interface
- **State Management**: React hooks and context
- **Routing**: React Router for navigation

### **Infrastructure**
- **Containerization**: Docker and Docker Compose
- **Development**: Hot reloading and development containers
- **Monitoring**: Built-in health checks and logging

---

## ⚙️ Getting Started

### **Prerequisites**
- Node.js 18+ and npm
- Python 3.9+
- Docker and Docker Compose
- PostgreSQL (via Docker)
- RabbitMQ (via Docker)

### **Quick Start with Docker** 🐳
```bash
# Clone the repository
git clone <repository-url>
cd semantic-chunking-platform

# Set up environment variables
./setup-env.bat  # Windows
# or
./setup-env.sh   # Linux/Mac

# Edit .env files with your actual values

# Start all services
docker compose up --build
```

### **Manual Setup** 🔧


### 1. **Environment Setup**

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
cp backend/.env.development.example backend/.env.development

# Edit the .env files with your actual values
```

### 2. **Database Setup**

```bash
# Start PostgreSQL and RabbitMQ
docker compose up postgres rabbitmq pgadmin -d

# Run database migrations
cd backend
npm run db:migrate
npm run db:seed  # Optional: add test data
```

---

## 🚀 Running the Platform

### **Option 1: Docker Compose (Recommended)** 🐳
```bash
# Start all services at once
docker compose up --build

# Or start services individually
docker compose up postgres rabbitmq pgadmin -d  # Infrastructure
docker compose up backend frontend -d            # Core services
docker compose up chunking-agent tagging-agent -d # AI services
```

### **Option 2: Manual Development Setup** 🔧

#### **Core Services**

**Backend API:**
```bash
cd backend
npm run db:migrate     # Run database migrations
npm run dev           # Start in development mode
# API available at: http://localhost:4000
```

**Frontend Application:**
```bash
cd frontend
npm start             # Start React development server
# UI available at: http://localhost:3000
```

#### **AI Processing Services**

**Semantic Chunking Agent:**
```bash
cd ai-services/chunking_agent
pip install -r requirements.txt
python chunking_worker.py
# Processes documents for semantic segmentation
```

**Document Tagging Agent:**
```bash
cd ai-services/tagging_agent
pip install -r requirements.txt
python main.py
# Generates AI-powered tags and classifications
```

**Embedding & Search Service:**
```bash
cd ai-services/embedding_agent
pip install -r requirements.txt
python main.py
# Generates vector embeddings for semantic search
```

**Retrieval Service:**
```bash
cd ai-services/retrieval_service
pip install -r requirements.txt
python main.py
# Handles search queries and ranking
```

#### **Document Parsers**

**Office Document Parser (Excel/Word):**
```bash
cd ai-services/xlsx_docx_parser
pip install -r requirements.txt

# Start Excel parser
python xlsx_worker.py

# Start Word document parser  
python docx_worker.py
```

**OCR Parser (Images/Scanned PDFs):**
```bash
cd ai-services/ocr_parser
pip install -r requirements.txt
python main.py
# Processes images and scanned documents with OCR
```

---

## 📊 Document Processing Workflow

### **1. Document Upload**
- Users upload documents through the web interface
- Files are stored in AWS S3 with metadata in PostgreSQL
- Upload events are published to RabbitMQ queues

### **2. Format Detection & Parsing**
```
Excel/CSV → xlsx_docx_parser → Structured data extraction
Word/RTF → xlsx_docx_parser → Text and formatting extraction  
PDF/Images → ocr_parser → OCR text extraction
Text/MD → Direct processing → Content parsing
```

### **3. Semantic Chunking**
- **Chunking Agent** receives parsed content
- Uses LLM to create semantically meaningful segments
- Considers document structure, context, and content type
- Generates chunks optimized for retrieval and comprehension

### **4. AI-Powered Tagging**
- **Tagging Agent** analyzes each chunk
- Generates relevant tags and categories
- Extracts key propositions and concepts
- Creates hierarchical tag structures

### **5. Vector Embedding**
- **Embedding Service** converts chunks to vectors
- Uses advanced embedding models
- Stores vectors in PostgreSQL with pgVector
- Enables semantic similarity search

### **6. Search & Retrieval**
- **Retrieval Service** handles search queries
- Performs vector similarity matching
- Ranks results by relevance and context
- Returns semantically relevant chunks

---

## 🎛️ Service Management & Monitoring

### **RabbitMQ Management Dashboard**
Monitor message queues and processing status:
- 🌐 **URL**: http://localhost:15672
- 📊 **Queues**: document_input, chunking_output, tagging_queue, embedding_queue
- 📈 **Metrics**: Message rates, queue depths, processing times

### **Database Administration (pgAdmin)**
Manage PostgreSQL database and view processed data:
- 🌐 **URL**: http://localhost:5050
- 🗄️ **Features**: Query editor, table browser, performance monitoring
- 📊 **Tables**: documents, chunks, embeddings, tags, users

### **Application URLs**
- 🖥️ **Frontend**: http://localhost:3000
- 🔌 **Backend API**: http://localhost:4000
- 📖 **API Documentation**: http://localhost:4000/api (Swagger)

---

## 🔍 Usage Examples

### **Processing Different Document Types**

#### **Excel Spreadsheet Processing**
```bash
# Upload a complex Excel file with multiple sheets
# System automatically:
# 1. Detects Excel format (.xlsx)
# 2. Extracts data from all sheets
# 3. Creates semantic chunks per sheet/section
# 4. Tags with spreadsheet-specific metadata
# 5. Generates searchable content
```

#### **Scanned Document Processing**
```bash
# Upload a scanned PDF or image
# System automatically:
# 1. Detects image/PDF format
# 2. Performs OCR text extraction
# 3. Cleans and processes extracted text
# 4. Creates semantic chunks
# 5. Tags with document type and content themes
```

#### **Word Document Processing**
```bash
# Upload a Word document with complex formatting
# System automatically:
# 1. Extracts text while preserving structure
# 2. Identifies headers, sections, tables
# 3. Creates hierarchical chunks
# 4. Maintains formatting context in tags
```

### **Search Capabilities**
- **Semantic Search**: Find documents by meaning, not just keywords
- **Multi-format Results**: Search across all document types simultaneously  
- **Contextual Ranking**: Results ranked by semantic relevance
- **Tag Filtering**: Filter by auto-generated tags and categories

---

## 🛠️ Development & Customization

### **Adding New Document Formats**
1. Create a new parser in `ai-services/`
2. Implement the document processing interface
3. Add format detection logic
4. Configure RabbitMQ queue routing
5. Update the frontend upload component

### **Custom AI Models**
- **Chunking**: Modify `chunking_agent/model_manager.py`
- **Tagging**: Update `tagging_agent/main.py`
- **Embeddings**: Configure `embedding_agent/main.py`

### **API Extensions**
- Add new endpoints in `backend/src/`
- Implement custom document metadata
- Create specialized search endpoints

---

## � Performance & Scaling

### **Horizontal Scaling**
- Multiple AI service instances can run simultaneously
- RabbitMQ handles load balancing across workers
- Database supports read replicas for high-load scenarios

### **Optimization Tips**
- Batch process similar document types together
- Use appropriate chunk sizes for your use case
- Monitor RabbitMQ queue depths for bottlenecks
- Consider GPU acceleration for large-scale OCR processing

---


### **Quality Metrics**
- Document processing accuracy
- Chunking semantic coherence  
- Search result relevance
- Processing throughput benchmarks

---

## 🌟 Advanced Features

### **Batch Processing**
- Process multiple documents simultaneously
- Progress tracking and status updates
- Error handling and retry mechanisms

### **Content Analytics**
- Document similarity analysis
- Content trend identification
- Automated content categorization

### **API Integration**
- RESTful API for external integrations
- Webhook support for processing notifications
- Bulk import/export capabilities

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support & Documentation

- 📖 **API Documentation**: Available at `/api` endpoint when backend is running
- 🔒 **Security Guide**: See `SECURITY.md`
- 🐛 **Issue Tracking**: Use GitHub Issues
- 💬 **Discussions**: GitHub Discussions for questions and ideas

---
