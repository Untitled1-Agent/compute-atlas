FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ATLAS_DB=/app/var/atlas.sqlite3
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 atlas
COPY server ./server
COPY src ./src
COPY data ./data
COPY originals ./originals
COPY index.html compute_atlas.html ./
RUN mkdir -p /app/var && chown atlas:atlas /app/var
USER atlas
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3)"
CMD ["python", "-m", "server", "serve", "--host", "0.0.0.0"]
