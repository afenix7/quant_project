#!/bin/bash

# Quant Project Frontend Deploy Script
# Usage: ./deploy.sh

set -e

echo "Deploying Quant Frontend..."

sudo rm -rf /var/www/quant
sudo mkdir -p /var/www/quant
sudo tar -xf /root/build-package/build.tar -C /var/www/quant/

echo "Deploy complete!"
