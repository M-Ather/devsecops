# INTENTIONALLY WEAK (Lab 4): old base image, runs as root, no pinned digest
FROM python:3.9-bullseye

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "app/app.py"]
