FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV BROKER_ADDRESS=${BROKER_ADDRESS}
ENV SWITCH_NAME=${SWITCH_NAME}

CMD ["python", "main.py", "${BROKER_ADDRESS}", "${SWITCH_NAME}"]
