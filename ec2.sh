#!/bin/bash

# Usage: bash ec2_setup.sh <DOMAIN_NAME> <ANTHROPIC_API_KEY>
set -e

DOMAIN_NAME=$1
ANTHROPIC_API_KEY=$2

if [ -z "$DOMAIN_NAME" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Usage: bash ec2_setup.sh <DOMAIN_NAME> <ANTHROPIC_API_KEY>"
  exit 1
fi

echo "[1/8] Updating system and installing dependencies"
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip certbot git

echo "[2/8] Cloning NANDA Adapter repo"
cd "$HOME"
if [ ! -d nanda_adapter ]; then
  git clone https://github.com/projnanda/adapter.git nanda_adapter
else
  echo "Repo already exists. Skipping clone."
fi
cd nanda_adapter/nanda_adapter

echo "[3/8] Creating Python virtual environment"
python3.11 -m venv env
source env/bin/activate

echo "[3b] Adding local package directory to PYTHONPATH"
export PYTHONPATH=$HOME/nanda_adapter:$PYTHONPATH

echo "[4/8] Installing Python requirements"
pip install --upgrade pip
pip install langchain-core langchain-anthropic python-dotenv nanda-adapter
pip install crewai crewai-tools --timeout 100 --retries 10 || echo "  CrewAI install had issues, continuing..."
pip install -r ../requirements.txt --timeout 100 --retries 10

echo "[5/8] Generating SSL certificates for: $DOMAIN_NAME"
sudo certbot certonly --standalone -d "$DOMAIN_NAME" --non-interactive --agree-tos -m admin@$DOMAIN_NAME

echo "[6/8] Move certificates to current folder for access and provide required access"
echo "Ensure the domain has to be changed"

sudo cp -L /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem .
sudo cp -L /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem .
sudo chown $USER:$USER fullchain.pem privkey.pem
chmod 600 fullchain.pem privkey.pem

echo "[7/8] Exporting environment variables"
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
export DOMAIN_NAME=$DOMAIN_NAME

echo "[8/8] Launching agent in background"
nohup python3 "$HOME/nanda_adapter/nanda_adapter/examples/langchain_pirate.py" > "$HOME/out.log" 2>&1 &

echo ""
echo "NANDA Agent launched!"
echo "Check your log with:"
echo "cat out.log"