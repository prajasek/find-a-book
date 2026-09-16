FROM python:3.12-bookworm

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN patchright install --with-deps chromium

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends xvfb xauth which\
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN chmod +x /app/run.sh

EXPOSE 8080


CMD ["/app/run.sh"]