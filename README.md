Here’s a streamlined version that merges both parts and removes duplicates:

# NYT Homepage Recreation

A containerized web app that recreates the New York Times homepage with real-time news, user authentication, and comments.

## Project Structure

- `frontend/` – Svelte + Vite app  
- `backend/` – Express API (Node.js + Python)  
- `config/` – config files  
- `docker-compose.dev.yml` – dev setup  
- `docker-compose.prod.yml` – prod setup  

## Features

- Responsive NYT-style layout  
- Live news updates  
- JWT-based auth and comment system  

## Prerequisites

- Docker & Docker Compose  
- Node.js (for local dev)  
- Python (for local dev)  

## Getting Started

1. **Clone**  
   ```bash
   git clone [your-repo-url]
   cd [repo-name]
````

2. **Dev mode**

   docker-compose -f docker-compose.dev.yml up

   * Frontend → [http://localhost:3000](http://localhost:3000)
   * Backend  → [http://localhost:8000](http://localhost:8000)

3. **Prod mode**

   cp .env.example .env.prod
   # edit .env.prod…
   docker-compose -f docker-compose.prod.yml up

## Environment Variables

Copy `.env.example` to `.env` (or `.env.prod`) and set:

* `MONGODB_URI`
* `JWT_SECRET`
* any other service-specific vars

## Tech Stack

* **Frontend:** Svelte, Vite
* **Backend:** Node.js, Express
* **Database:** MongoDB
* **Containerization:** Docker, Docker Compose
