FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home lignet && mkdir -p /app/staticfiles && chown lignet:lignet /app/staticfiles
COPY . .
USER lignet
EXPOSE 8000
CMD ["gunicorn", "lignet.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "45"]
