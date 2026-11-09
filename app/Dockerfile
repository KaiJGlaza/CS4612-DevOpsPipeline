# Packages the app into a container image.

# Start from a small, official Python image
FROM python:3.13-slim

# Install Debian's security fixes, so we don't wait for the official image to be rebuilt.
# Added after Trivy flagged zlib (CVE-2026-85091, CVE-2026-76844) on Nov 9, 2026.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the libraries the app needs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove pip once the libraries are installed. Carries outdated copies of other libraries (flagged by Trivy).
RUN pip uninstall -y pip

# Copy in the app's code
COPY . .

# Run as a normal user instead of root (safer if the app is ever hacked)
RUN useradd --create-home appuser
USER appuser

# Keep the notes database in appuser's home, since /app belongs to root
ENV NOTES_DB=/home/appuser/notes.db

EXPOSE 5000
CMD ["python", "app.py"]
