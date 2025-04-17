# PassMint

A LINE ミニアプリ + Apple/Google Wallet パス発行サービス.

## Features

- Create and issue digital wallet passes for Apple Wallet and Google Wallet
- Customize pass designs with a template system
- QR code generation for easy pass distribution
- LINE login integration
- Statistics dashboard for organizations

## Technology Stack

- **Backend**: FastAPI 0.110, Python 3.11
- **Database**: PostgreSQL 15
- **Storage**: S3 compatible (MinIO / AWS S3)
- **Frontend**: React 18 + TypeScript + LIFF v2 (separate repository)

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- MinIO or S3-compatible storage

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/passmint.git
cd passmint
```

2. Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:

```bash
# Make sure your PostgreSQL server is running
python -m alembic upgrade head
```

### Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000/

## API Documentation

After starting the server, documentation is available at:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Development

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

## License

MIT License