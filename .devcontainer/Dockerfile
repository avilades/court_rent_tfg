FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye

ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
