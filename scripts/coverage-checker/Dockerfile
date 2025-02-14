# Start with Python 3 in the /usr/app folder
FROM python:3-slim
WORKDIR /usr/app/

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir --user
COPY . .

# Run coverage script
CMD [ "/bin/bash", "-c", "python -u ./coverage.py" ]
