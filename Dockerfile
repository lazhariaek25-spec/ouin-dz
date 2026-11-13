FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PROD=1 OUIN_DB=/data/ouin.db
CMD ["sh","-c","gunicorn --chdir backend -b 0.0.0.0:${PORT:-8080} -w 2 app:app"]
