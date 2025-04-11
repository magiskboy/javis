# Javis

## Getting Started

Javis is an AI assistant system that runs locally using Docker Compose.

### Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone this repository)
- uv (to manage Python environments and packages)

### System Components

The Javis system consists of the following services:

1. **PostgreSQL with pgvector** - Vector database for storing embeddings
   - Runs on port 5432
   - Uses pgvector extension for efficient vector operations
   - Data persisted in `.data/postgres` directory

2. **Redis Stack** - In-memory data store
   - Redis server runs on port 6379
   - Redis Insight (web UI) available on port 8001
   - Data persisted in `.data/redis` directory

3. **Ollama** - Local LLM server
   - Runs on port 11434
   - Models stored in `.data/ollama` directory

### Starting the System

To start all services, run:

```sh
$ docker compose up -d
```

Your data will stored in `.data` folder.

Install `uv` if need

```sh
# On macOS and Linux.
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

After that, let's set up javis

```sh
$ uv venv
$ source .venv/bin/activate
$ uv sync
$ export PYTHONPATH=.
$ uv run javis
```