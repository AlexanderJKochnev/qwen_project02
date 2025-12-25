#!/bin/bash

# Script to generate self-signed SSL certificates for IP address 83.167.126.4

echo "Creating SSL certificates for IP address 83.167.126.4..."

# Create the SSL directory if it doesn't exist
mkdir -p /workspace/ssl

# Create a temporary configuration file for the certificate with IP SAN
cat > /workspace/ssl/ssl_config.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=Organization
OU=Unit
CN=83.167.126.4

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
IP.1 = 83.167.126.4
IP.2 = 127.0.0.1
DNS.1 = localhost
EOF

# Generate private key and certificate
openssl req -new -x509 -keyout /workspace/ssl/nginx.key -out /workspace/ssl/nginx.crt -days 365 -nodes -config /workspace/ssl/ssl_config.conf -batch

# Set appropriate permissions
chmod 600 /workspace/ssl/nginx.key
chmod 644 /workspace/ssl/nginx.crt

echo "SSL certificates generated successfully!"
echo "Certificate: /workspace/ssl/nginx.crt"
echo "Private Key: /workspace/ssl/nginx.key"

# Clean up the temporary config file
rm -f /workspace/ssl/ssl_config.conf

echo "SSL certificate generation completed."