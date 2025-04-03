FROM python:3.8-slim-buster

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
CMD ["flask", "--app", "manager.app", "run", "-h", "0.0.0.0", "-p", "8000"]
