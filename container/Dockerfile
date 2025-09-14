FROM ubuntu:20.04

LABEL maintainer="Nader Karimi Bavandpour <nader.karimi.bavandpour@anu.edu.au>" \
      authors="Nader Karimi Bavandpour, Pascal Lauer, Songtuan Lin, Pascal Bercher" \
      publication_title="Supplementary Material, Code, and Experimental Results for the ECAI 2025 Paper: 'Repairing Planning Domains Based on Lifted Test Plans'" \
      description="Docker image containing code and experimental results for the ECAI 2025 paper." \
      url="https://github.com/nader93k/lifted-domain-repair"


ENV DEBIAN_FRONTEND=noninteractive \
    LD_LIBRARY_PATH="/lib:/usr/lib:/usr/local/lib" \
    DYLD_LIBRARY_PATH="/lib:/usr/lib:/usr/local/lib" \
    PATH="/usr/local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        wget p7zip-full cmake g++ make build-essential autotools-dev \
        libboost-all-dev libboost-program-options-dev zlib1g-dev \
        libssl-dev libffi-dev libsqlite3-dev libbz2-dev liblzma-dev \
        tk-dev software-properties-common gpg-agent curl \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y python3.8 python3.8-dev python3.8-distutils python3.8-venv \
    && curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | python3.8 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 \
    && python3 --version && pip3 --version \
    && apt-get clean && rm -rf /var/lib/apt/lists/*



## Changes may happen after this line 

# Set working directory inside container
WORKDIR /app

COPY requirements.txt .

# Install dependencies (if you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .