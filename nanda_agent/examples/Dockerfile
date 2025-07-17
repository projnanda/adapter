FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY langchain_pirate.py .

# Create directory for conversation logs
RUN mkdir -p conversation_logs

# Set environment variables with defaults
ENV ANTHROPIC_API_KEY=""
ENV DOMAIN_NAME="localhost"
ENV PORT=6000
ENV TERMINAL_PORT=6010
ENV IMPROVE_MESSAGES=true
ENV UI_MODE=true

# Expose the port
EXPOSE 6000

# Set the entrypoint
ENTRYPOINT ["python", "langchain_pirate.py"]