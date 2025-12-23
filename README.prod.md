# Production Deployment

This document describes how to deploy the application in production using Docker Compose with nginx as a reverse proxy.

## Overview

The production setup includes:
- PostgreSQL database
- MongoDB
- Redis for ARQ task queue
- FastAPI backend
- Preact frontend served by nginx
- Nginx as a reverse proxy with HTTPS support

## SSL Certificates

To enable HTTPS, you need to provide SSL certificates. Create a `ssl` directory in the project root and add your certificates:

```bash
mkdir -p ssl
# Copy your certificate files to the ssl directory
cp your_certificate.pem ssl/cert.pem
cp your_private_key.pem ssl/key.pem
```

For testing purposes, you can generate self-signed certificates:

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## Environment Variables

Make sure to update the `.env` file with production settings:

```env
# Change BASE_URL to your production domain
BASE_URL=https://yourdomain.com

# Production settings
DEV=0
DEBUG=0
DB_ECHO=0

# Security - change this in production!
SECRET_KEY=generate_a_strong_secret_key_here
```

## Deployment

To deploy the application:

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yaml up --build -d

# View logs
docker-compose -f docker-compose.prod.yaml logs -f

# Stop the services
docker-compose -f docker-compose.prod.yaml down
```

## Architecture

- **nginx**: Serves the Preact frontend static files and acts as a reverse proxy for the FastAPI backend
- **app**: FastAPI application serving API requests
- **wine_host**: PostgreSQL database
- **mongo**: MongoDB database
- **redis**: Redis for ARQ task queue

## API Endpoints

All API endpoints are accessible through nginx:
- `/api/*` → FastAPI backend
- `/auth/*` → Authentication endpoints
- `/users/*` → User management
- `/images/*` → Image handling
- `/files/*` → File handling
- `/mongodb/*` → MongoDB endpoints
- `/handbooks/*` → Handbook endpoints
- `/health` → Health check

## Frontend

The Preact frontend is built and served from the root path (`/`).

## SSL Configuration

The nginx configuration includes:
- SSL/TLS termination
- HTTP/2 support
- Security headers
- Gzip compression
- Proper proxy headers for the backend