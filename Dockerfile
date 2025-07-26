FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV SOAP_WSDL_URL=""
ENV SOAP_USERNAME=""
ENV SOAP_PASSWORD=""
ENV SOAP_TIMEOUT_SECONDS="30"

CMD ["python", "src/soap_client.py"]
