# Multi-stage build to get the Preact build and serve it with nginx
FROM node:20-alpine AS preact-builder
WORKDIR /app
COPY preact_front/package*.json ./
RUN npm ci
COPY preact_front/ ./
RUN npm run build

# Production nginx server
FROM nginx:stable-alpine
# Copy the built Preact app from the previous stage
COPY --from=preact-builder /app/dist /usr/share/nginx/html
# Copy our custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
# Create directory for SSL certificates
RUN mkdir -p /etc/nginx/ssl
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]