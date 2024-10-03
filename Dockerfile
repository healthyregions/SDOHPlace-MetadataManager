FROM python:3.8-slim-buster

RUN useradd -m herop
USER herop

ENV PATH="/home/herop/.local/bin:$PATH"

WORKDIR /home/herop

COPY --chown=herop:herop requirements.txt requirements.txt
RUN pip3 --disable-pip-version-check install -U -r requirements.txt
COPY --chown=herop:herop . .
RUN pip3 install . --disable-pip-version-check

EXPOSE 8000
CMD ["flask", "--app", "manager.app", "run", "-h", "0.0.0.0", "-p", "8000"]
