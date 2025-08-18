FROM python:3.12-bullseye

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    libxrender1 \
    poppler-utils \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libasound2 \
    libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .

# Install selectolax first with specific options
RUN pip install --no-cache-dir selectolax==0.3.16

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install 'torch<2.6' torchvision

RUN python -m playwright install
# RUN python -m playwright install-deps

# Docker is available from host via volume mount, no need to install in container

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]