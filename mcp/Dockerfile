FROM python:3.12-slim
WORKDIR /app
COPY server.py .
ENV PORT=3000
EXPOSE 3000
HEALTHCHECK --interval=30s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:3000/health',timeout=3)"
ENTRYPOINT ["python", "server.py"]
