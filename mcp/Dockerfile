FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
WORKDIR /app
COPY server.py .
ENV PORT=3000
EXPOSE 3000
HEALTHCHECK --interval=30s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:3000/health',timeout=3)"
ENTRYPOINT ["python", "server.py"]
