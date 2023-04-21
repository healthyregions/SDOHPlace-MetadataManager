# PlaceProject

## Configure

```
cp ./ingest/.env.example ./ingest/.env
```

Update `SOLR_HOST` appropriately in `./ingest/.env`.

## Run

Start containers

```
docker-compose up -d --build
```

Stop containers

```
docker-compose down
```
