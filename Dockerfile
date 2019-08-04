FROM python:3.7
WORKDIR app
ENV NATS_URL="nats://nats:4222"
ENV NATS_QUEUE="myqueue"
ENV PORT="7298"
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt && \
    apt update && \
    apt install -y telnet
COPY main.py /app/main.py
CMD ["python", "-u", "/app/main.py"]