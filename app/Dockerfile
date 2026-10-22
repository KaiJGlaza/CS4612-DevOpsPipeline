# Packages the app into a container image.

# Start from a small, official Python image
FROM python:3.13-slim

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

EXPOSE 5000
CMD ["python", "app.py"]
