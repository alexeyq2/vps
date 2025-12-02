FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY geo_update.py ./

ENTRYPOINT ["/usr/local/bin/python", "geo_update.py", "--delay"]

