# ECS 162 Homework 3 - Web Application

This is a web application built for ECS 162 Homework 3. The application consists of a frontend and backend service, containerized using Docker.

## Project Structure

- `frontend/` - Frontend application
- `backend/` - Backend service
- `config/` - Configuration files
- `docker-compose.dev.yml` - Development Docker Compose configuration
- `docker-compose.prod.yml` - Production Docker Compose configuration

## Prerequisites

- Docker
- Docker Compose
- Node.js (for local development)
- Python (for local development)

## Getting Started

### Development Environment

1. Clone the repository:
   ```bash
   git clone [your-repo-url]
   cd [repo-name]
   ```

2. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

### Production Environment

1. Set up your environment variables:
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with your production values
   ```

2. Start the production environment:
   ```bash
   docker-compose -f docker-compose.prod.yml up
   ```

## Environment Variables

Create a `.env` file based on `.env.example` with the following variables:

- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET`: Secret key for JWT authentication
- Other environment-specific variables

## License

This project is part of ECS 162 coursework. 