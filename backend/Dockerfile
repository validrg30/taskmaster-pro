FROM python:3.9-slim

WORKDIR /app

# Copiem cerintele
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem codul
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
