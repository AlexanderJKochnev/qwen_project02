# Nginx Reverse Proxy Setup for Production

This document describes how to set up and run the production version of the application with Nginx as a reverse proxy supporting both HTTP and HTTPS.

## 1. Order of Actions

### 1.1 Prerequisites
- Ensure Docker and Docker Compose are installed on your system
- Make sure you have the `.env` file properly configured in the root directory

### 1.2 Generate SSL Certificates
1. Run the SSL certificate generation script:
   ```bash
   ./generate_ssl_cert.sh
   ```
   This will create self-signed SSL certificates for IP address 83.167.126.4 in the `/workspace/ssl` directory.

### 1.3 Run the Production Environment
1. Start the services using the production docker-compose file:
   ```bash
   docker-compose -f docker-compose.prod.yaml up -d
   ```

## 2. Service Access URLs

### HTTP Access (port 80):
- **Preact Frontend**: `http://83.167.126.4/`
- **FastAPI API**: `http://83.167.126.4/api`
- **Auth Routes**: `http://83.167.126.4/auth`
- **Users Routes**: `http://83.167.126.4/users`
- **Images Routes**: `http://83.167.126.4/images`
- **Files Routes**: `http://83.167.126.4/files`
- **MongoDB Routes**: `http://83.167.126.4/mongodb`
- **Adminer**: `http://83.167.126.4/adminer`
- **Mongo Express**: `http://83.167.126.4/mongo-express`
- **Handbooks Routes**: `http://83.167.126.4/handbooks`

### HTTPS Access (port 443):
- **Preact Frontend**: `https://83.167.126.4/`
- **FastAPI API**: `https://83.167.126.4/api`
- **Auth Routes**: `https://83.167.126.4/auth`
- **Users Routes**: `https://83.167.126.4/users`
- **Images Routes**: `https://83.167.126.4/images`
- **Files Routes**: `https://83.167.126.4/files`
- **MongoDB Routes**: `https://83.167.126.4/mongodb`
- **Adminer**: `https://83.167.126.4/adminer`
- **Mongo Express**: `https://83.167.126.4/mongo-express`
- **Handbooks Routes**: `https://83.167.126.4/handbooks`

## 3. Nginx Configuration Details

### 3.1 Upstream Definitions
- `fastapi_backend`: Points to the FastAPI application container (`app:${API_PORT}`)
- `preact_backend`: Points to the production Preact container (`preact_front:80`)
- `adminer_backend`: Points to the Adminer container (`adminer:8080`)
- `mongo_express_backend`: Points to the Mongo Express container (`mongo-express:8081`)

### 3.2 SSL Configuration
- SSL protocols: TLSv1.2 and TLSv1.3
- SSL ciphers: HIGH security ciphers excluding weak ones
- Certificate location: `/etc/nginx/ssl/nginx.crt`
- Private key location: `/etc/nginx/ssl/nginx.key`

### 3.3 Proxy Headers
The following headers are set for all proxy passes to ensure proper request forwarding:
- `Host`: Original host header
- `X-Real-IP`: Real client IP address
- `X-Forwarded-For`: List of IP addresses in the forwarding chain
- `X-Forwarded-Proto`: Original protocol (HTTP or HTTPS)

### 3.4 Service Routing
- Root path (`/`) routes to the Preact frontend
- All API routes (`/api`, `/auth`, `/users`, `/images`, `/files`, `/mongodb`, `/handbooks`) route to the FastAPI backend
- `/adminer` routes to Adminer service
- `/mongo-express` routes to Mongo Express service

## 4. Notes
- The preact application uses multi-stage Docker build with the `production` target
- All services are configured with proper health checks and resource limits
- Adminer and Mongo Express are included in production for debugging purposes and can be removed later
- The application preserves all original FastAPI router paths
- Both HTTP and HTTPS access are available simultaneously