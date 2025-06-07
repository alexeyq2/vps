FROM certbot/certbot:latest
# envsubst для генерации cli.ini из шаблона
RUN apk add --no-cache envsubst

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/usr/local/bin/python", "main.py"]
