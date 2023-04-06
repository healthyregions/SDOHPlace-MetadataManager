FROM python:3.8-slim-buster

WORKDIR /docker-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

EXPOSE 80
CMD ["python3", "-u", "server.py"]