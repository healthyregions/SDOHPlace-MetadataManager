FROM --platform=linux/amd64 python:3.8-slim-buster

# Install curl for health checks
# Update sources to use archive.debian.org since Buster is EOL
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list && \
    sed -i '/stretch-updates/d' /etc/apt/sources.list && \
    apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Switch to new user "herop"
RUN useradd -m herop
USER herop
ENV PATH="/home/herop/.local/bin:$PATH"
WORKDIR /home/herop

# Install Python Dependencies
COPY --chown=herop:herop requirements.txt requirements.txt
RUN pip3 install -U -r requirements.txt --no-cache-dir

# Setup Python app
COPY --chown=herop:herop . .
RUN pip3 install . --no-cache-dir

# TODO: --disable-pip-version-check  ?

# Run application on port 8000
EXPOSE 8000
CMD ["flask", "run", "-h", "0.0.0.0", "-p", "8000"]
