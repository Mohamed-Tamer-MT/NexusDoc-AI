# NexusDoc AI

Intelligent document conversation platform powered by RAG (Retrieval-Augmented Generation).

## Overview

NexusDoc AI is a multi-document chat application that enables users to upload PDF, DOCX, and TXT files, index them using FAISS vector storage with MMR (Maximal Marginal Relevance) retrieval, and engage in conversational question-answering over the uploaded documents using LLMs.

The system uses Google Generative AI embeddings for vectorization and supports Google Gemini or Groq LLMs for answer generation.

## Key Features

- **Multi-format document support**: PDF, DOCX, TXT
- **MMR retrieval**: Maximal Marginal Relevance for diverse, relevant results
- **Conversational context**: Chat history-aware question reformulation
- **Session-based conversations**: Each upload creates an isolated session
- **LCEL chains**: Composable LangChain Expression Language pipeline
- **Structured logging**: JSON logs with structlog for observability
- **Containerized deployment**: Docker with AWS ECS Fargate production setup

## Architecture

```mermaid
flowchart TB
    A[Client Browser] --> B[FastAPI App]
    B --> C[/upload]
    B --> D[/chat]
    
    C --> E[ChatIngestor]
    E --> F[Document Loader]
    E --> G[Text Splitter]
    G --> H[Google Embeddings]
    H --> I[FAISS Vector Store]
    
    D --> J[ConversationalRAG]
    J --> K[Question Contextualizer]
    K --> L[MMR Retriever]
    L --> I
    L --> M[QA Prompt]
    M --> N[LLM Gemini/Groq]
    N --> O[Answer]
    
    I --> P[Persisted FAISS Index]
```

## Tech Stack

| Category       | Technology                     |
| -------------- | ------------------------------ |
| Language       | Python 3.12+                   |
| Framework      | FastAPI 0.115.6                |
| AI/ML          | LangChain 0.3.27               |
| Embeddings     | Google text-embedding-004      |
| LLMs           | Google Gemini 2.0 Flash, Groq  |
| Vector Store   | FAISS (faiss-cpu)              |
| Frontend       | Jinja2, Vanilla JavaScript      |
| Logging        | Structlog                      |
| Testing        | Pytest                         |
| Container      | Docker                         |
| Deployment     | AWS ECS Fargate                |
| CI/CD          | GitHub Actions                 |
| Package Mgr    | uv                             |

## Project Structure

```text
LLMops/
├── main.py                          # FastAPI application entry point
├── multi_doc_chat/
│   ├── src/
│   │   ├── document_ingestion/
│   │   │   └── data_ingestion.py    # ChatIngestor, FaissManager
│   │   └── document_chat/
│   │       └── retrieval.py         # ConversationalRAG class
│   ├── utils/
│   │   ├── model_loader.py          # LLM/embedding model loader
│   │   ├── config_loader.py         # YAML config management
│   │   ├── document_ops.py          # Document loading utilities
│   │   └── file_io.py               # File saving utilities
│   ├── prompts/
│   │   └── prompt_library.py        # RAG prompt templates
│   ├── logger/
│   │   └── cutom_logger.py          # Structured logging setup
│   ├── exception/
│   │   └── custom_exception.py       # Rich exception handling
│   ├── model/
│   │   └── models.py                # Pydantic models
│   └── config/
│       └── config.yaml               # LLM/embedding configuration
├── test/
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── test_retrieval.py
│   │   └── test_data_ingestion.py
│   └── integration/
│       ├── test_upload_route.py
│       └── test_chat_route.py
├── notebook/
│   ├── RAG.ipynb                    # RAG experimentation
│   └── Evaluations.ipynb            # LangSmith evaluation
├── templates/
│   └── index.html                   # Web UI
├── static/
│   └── style.css                    # Dark theme styling
├── .github/
│   └── workflows/
│       ├── ci.yml                   # GitHub Actions CI
│       ├── aws.yml                  # ECS deployment
│       └── task_defination.json     # ECS task definition
├── Dockerfile                       # Container definition
├── requirements.txt                 # Pip dependencies
├── pyproject.toml                   # uv project config
└── .env                            # Environment variables template
```

## Requirements

- Python 3.12+
- `uv` package manager (recommended) or `pip`
- API keys:
  - `GOOGLE_API_KEY` (for embeddings + Gemini)
  - `GROQ_API_KEY` (for Groq LLM, optional)

## Installation

```bash
# Clone the repository
git clone https://github.com/Mohamed-Tamer-MT/LLMops.git
cd LLMops

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=google  # Options: google, groq
ENV=local            # Options: local, production
PORT=8000            # Server port
```

The LLM and embedding models are configured in `multi_doc_chat/config/config.yaml`:

```yaml
embedding_model:
  provider: "google"
  model_name: "models/text-embedding-004"

llm:
  groq:
    provider: "groq"
    model_name: "openai/gpt-oss-20b"
    temperature: 0
    max_output_tokens: 2048
  google:
    provider: "google"
    model_name: "gemini-2.0-flash"
    temperature: 0
    max_output_tokens: 2048
```

## Running the Project

### Local Development

```bash
# Start the FastAPI development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The web UI will be available at `http://localhost:8000`.

### Production (Docker)

```bash
# Build the Docker image
docker build -t nexusdoc-ai .

# Run the container
docker run -d -p 8080:8080 \
  -e ENV=production \
  -e GOOGLE_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  nexusdoc-ai
```

### Programmatic Usage

```python
from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG

# Initialize RAG with a session
rag = ConversationalRAG(session_id="my-session")

# Load the persisted FAISS index
rag.load_retriever_from_faiss(
    index_path="faiss_index/my-session",
    search_type="mmr",
    fetch_k=20,
    lambda_mult=0.5
)

# Query the documents
answer = rag.invoke(
    "What is the main topic of the documents?",
    chat_history=[]
)
print(answer)
```

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{"status": "ok"}
```

### Upload Documents

```bash
POST /upload
Content-Type: multipart/form-data

files: <PDF, DOCX, or TXT files>
```

Response:
```json
{
  "session_id": "session_20260825_083000_a1b2c3d4",
  "indexed": true,
  "message": "Indexing complete with MMR"
}
```

### Chat

```bash
POST /chat
Content-Type: application/json

{
  "session_id": "session_20260825_083000_a1b2c3d4",
  "message": "What are the key findings?"
}
```

Response:
```json
{
  "answer": "The key findings indicate that..."
}
```

### Session Status

```bash
GET /session/{session_id}
```

Response:
```json
{"valid": true}
```

## Testing

```bash
# Run all tests
pytest -q

# Run with verbose output
pytest -v

# Run specific test files
pytest test/unit/ -v
pytest test/integration/ -v
```

## Code Quality

```bash
# Lint with ruff
ruff check .

# Format with ruff (if configured)
ruff format .
```

Type checking is configured via `basedpyright` in `pyproject.toml` but requires installation:

```bash
uv add --group dev basedpyright
basedpyright multi_doc_chat/
```

## CI/CD

The project uses GitHub Actions with two workflows:

1. **CI** (`.github/workflows/ci.yml`): Runs on every push/PR to main
   - Checks out code
   - Sets up Python 3.11
   - Installs dependencies with uv
   - Runs pytest

2. **AWS Deployment** (`.github/workflows/aws.yml`): Runs after CI passes on main
   - Builds Docker image
   - Pushes to Amazon ECR
   - Deploys to ECS Fargate

## Deployment

The application is designed for AWS ECS Fargate deployment:

1. Docker image pushed to ECR
2. ECS task definition uses Fargate (1 vCPU, 8GB memory)
3. API keys stored in AWS Secrets Manager
4. Container listens on port 8080

Environment variables in production:
- `ENV=production`
- `apikeyliveclass` (JSON containing `GROQ_API_KEY` and `GOOGLE_API_KEY`)

## Security

- API keys loaded from environment variables or AWS Secrets Manager
- File uploads validated by extension whitelist (`.pdf`, `.docx`, `.txt`)
- No persistent session storage (in-memory only)
- CORS configured for all origins in development
- `allow_dangerous_deserialization=True` for FAISS (only use with trusted indices)

## Performance

- FAISS CPU vector search is fast for datasets up to millions of vectors
- MMR retrieval (`fetch_k=20`, `lambda_mult=0.5`) balances relevance and diversity
- Session-scoped FAISS indices isolate data between conversations
- Chunk size (1000) and overlap (200) optimized for document coherence

For very large datasets, consider:
- FAISS GPU index
- Distributed vector stores (Pinecone, Qdrant)
- Embedding model quantization

## Roadmap

The following features are potential extensions based on project structure:

- [ ] Persistent session storage (Redis/database)
- [ ] User authentication and authorization
- [ ] Rate limiting
- [ ] Additional document formats (PPTX, MD, CSV, XLSX)
- [ ] Hybrid search (keyword + vector)
- [ ] Re-ranking models
- [ ] Streaming responses
- [ ] Multi-modal document support

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dev dependencies: `uv sync --group dev`
4. Make changes and add tests
5. Run tests: `pytest -q`
6. Lint: `ruff check .`
7. Commit: `git commit -m "Add my feature"`
8. Push: `git push origin feature/my-feature`
9. Open a Pull Request

## License

MIT License

## Author / Contact

**Mohamed Tamer Nassr**

- GitHub: [Mohamed-Tamer-MT](https://github.com/Mohamed-Tamer-MT)
- GitLab: [mohamed-MTN](https://gitlab.com/mohamed-MTN)
- Email: [mohamed.tamer.nassr@gmail.com](mailto:mohamed.tamer.nassr@gmail.com)
