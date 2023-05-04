# PlaceProject

## Configure

```
cp ./flask/.env.example ./flask/.env
```

Required .env content:

`SOLR_HOST`: full url to Solr endpoint

## Install/Run locally

A dev deploy will serve the app on Flask's default port (5000).

```
python3 -m venv env
source ./env/bin/activate
pip install -e ./MetadataManager
```

Then

```
flask --app MetadataManager.manager.app run --debug
```

`--debug` will auto-reload the app whenever a file is changed (though it seems like changes to HTML files requires the app to be stopped and restarted...).

## Install/Run with Docker

The Docker deploy will serve the app on port 8080 with nginx.

Start containers

```
docker-compose up -d --build
```

Stop containers

```
docker-compose down
```
