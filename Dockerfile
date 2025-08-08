FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# use gunicorn (production) to serve the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app", "--workers", "2", "--threads", "4"]
