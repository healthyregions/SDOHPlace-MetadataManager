# PlaceProject

## Configure

```
cp ./flask/.env.example ./flask/.env
```

Required .env content:

`SOLR_HOST`: full url to Solr endpoint
`MODE`: use `"dev"` to run locally, use `"prod"` to run with Docker

## Install/Run locally

A dev deploy will serve the app on Flask's default port (5000).

Set `MODE="dev"`.

```
python3 -m venv env
source ./env/bin/activate
pip install -r flask/requirements.txt
pip install -e flask
```

Then

`python flask/server.py -u`

## Install/Run with Docker

The Docker deploy will serve the app on port 8080 with nginx.

Set `MODE="prod"`.

Start containers

```
docker-compose up -d --build
```

Stop containers

```
docker-compose down
```
