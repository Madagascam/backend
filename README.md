# ♟️ Chess Analysis Backend

Backend service for uploading, processing and analyzing chess games.

The system allows users to upload PGN files, run asynchronous analysis and retrieve structured insights about the game.



## 🚀 Features

* Upload and parse chess games (PGN format)
* Asynchronous game analysis
* Multiple analysis strategies (pluggable)
* Background task processing
* Optional video generation
* REST API for managing games and results



## 🧠 Architecture

The project is structured as a layered backend application:

* **API layer** — request handling (FastAPI routers)
* **Core / domain layer** — analysis logic and strategies
* **Infrastructure layer** — database, tasks, integrations

Key concepts used in the project:

* **Strategy pattern** — switch between different analysis implementations
* **Unit of Work** — manage database transactions
* **Background tasks** — handle long-running operations
* **Separation of concerns** — clear boundaries between layers



## ⚙️ How It Works

1. User uploads a PGN file
2. Game is parsed and stored
3. Analysis task is created
4. Background worker processes the game
5. Results are saved and exposed via API



## 🛠 Tech Stack

* Python 3.12
* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis
* Celery
* Docker



## 📌 Example Flow

```text
Upload PGN → Create Game → Run Analysis → Get Results
```



## 📦 Project Structure

```text
app/
  api/          # routes
  core/         # domain logic
  services/     # business logic
  models/       # database models
```



## ⚙️ Run Locally

```bash
docker-compose up --build
```



## 🎯 Purpose

* Practice backend architecture design
* Work with async processing and task queues
* Build a system that handles non-trivial workflows



