#!/bin/bash

# Script to obtain SSL certificates using certbot and Let's Encrypt
# Usage: ./get_ssl_cert.sh <validity_period_in_days>  # Note: This is informational only as Let's Encrypt uses 90-day validity
# Example: ./get_ssl_cert.sh 365

set -e  # Exit on any error

# Check if argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <validity_period_in_days>"
    echo "Example: $0 365"
    exit 1
fi

VALIDITY_PERIOD=$1
DOMAIN="abc8888.ru"
SUBDOMAIN="api.abc8888.ru"

# Validate that the argument is a number
if ! [[ "$VALIDITY_PERIOD" =~ ^[0-9]+$ ]]; then
    echo "Error: Validity period must be a positive integer"
    exit 1
fi

echo "Obtaining SSL certificates for domain: $DOMAIN and subdomain: $SUBDOMAIN"
echo "Note: Let's Encrypt certificates have a fixed 90-day validity period by policy"
echo "The validity period argument is for informational purposes only"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "Certbot is not installed. Installing certbot..."
    
    # Detect OS and install certbot accordingly
    if [ -f /etc/debian_version ] || [ -f /etc/debian_release ]; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y certbot python3-certbot-nginx
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        sudo yum install -y certbot python3-certbot-nginx
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        sudo pacman -S certbot python-certbot-nginx
    else
        echo "Unsupported OS. Please install certbot manually."
        exit 1
    fi
fi

# Check if nginx is installed and running
if command -v nginx &> /dev/null; then
    # Stop nginx temporarily if it's running to allow certbot to bind to port 80
    NGINX_RUNNING=$(sudo systemctl is-active nginx)
    if [ "$NGINX_RUNNING" = "active" ]; then
        echo "Stopping nginx temporarily..."
        sudo systemctl stop nginx
    fi
fi

# Obtain certificate using standalone method (binds to port 80)
echo "Obtaining certificate using standalone method..."
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email admin@abc8888.ru \
    --domains $DOMAIN,$SUBDOMAIN \
    --cert-name abc8888.ru

# If nginx was running, restart it
if command -v nginx &> /dev/null; then
    if [ "$NGINX_RUNNING" = "active" ]; then
        echo "Restarting nginx..."
        sudo systemctl start nginx
    fi
fi

# Verify the certificate was created
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
if [ -d "$CERT_PATH" ]; then
    echo "SSL certificate successfully obtained!"
    echo "Certificate location: $CERT_PATH"
    echo "Certificate files:"
    ls -la "$CERT_PATH"
    
    # Set up auto-renewal
    echo "Setting up auto-renewal..."
    (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
    echo "Auto-renewal cron job added."
    
    # Calculate expiration date
    EXPIRY_DATE=$(sudo openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -enddate | cut -d= -f2)
    echo "Certificate will expire on: $EXPIRY_DATE"
    
    # Check if the certificate validity matches the requested period (approximately)
    CERT_START_DATE=$(sudo openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -startdate | cut -d= -f2)
    START_TIMESTAMP=$(date -d "$CERT_START_DATE" +%s)
    END_TIMESTAMP=$(date -d "$EXPIRY_DATE" +%s)
    ACTUAL_DAYS=$(((END_TIMESTAMP - START_TIMESTAMP) / 86400))
    
    echo "Actual certificate validity: $ACTUAL_DAYS days"
    
    echo "Note: Let's Encrypt certificates have a fixed 90-day validity period by policy"
    
else
    echo "Failed to obtain SSL certificate."
    exit 1
fi

echo "SSL certificate setup completed successfully!"