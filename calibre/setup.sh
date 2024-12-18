#!/bin/bash

# Installazione
apt-get update && apt-get install -y build-essential python3-pip && rm -rf /var/lib/apt/lists/*

pip install --no-cache-dir -r requirements.txt --break-system-packages
