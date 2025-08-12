FROM python:3.12

RUN apt-get update && apt-get install -y \
    libxrender1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install 'torch<2.6' torchvision

RUN python -m playwright install
RUN python -m playwright install-deps

RUN apt-get install -y docker.io

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]