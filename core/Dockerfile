FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /core

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership to the non-root user
RUN chown -R appuser:appuser /core

# Copy and make executable the entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /core/entrypoint.sh
RUN chmod +x /core/entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE $PORT

CMD ["/core/entrypoint.sh"]
