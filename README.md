# SDOH Place - Metadata Manager

This is the metadata manager for the SDOH & Place Project, a new map-based search platform for SDOH data discovery that will curate and integrate validated geospatial data relevant to public health at multiple scales.

## Preliminary Metadata Creation

### Schema

We are using the Aardvark schema from [OpenGeoMetadata (OGM) Aardvark Schema](https://opengeometadata.org/ogm-aardvark/), along with some extra fields specifically for our needs. These fields are:

Custom metadata schema for this project:
- Spatial Resolution (=tract, zip code, county)
- Spatial Resolution Note
- Data Variables
- Methods Variables

### Initial Discovery Datasets:

- County Health Rankings 
    - 2021 county (MK - Needs Review)
- City Health Dashboard
    - 2018 census tract (Augustyn will Review - Add Placenames to Spatial Coverage)
- Neighborhood Health Atlas (ADI)
    - 2015 block group (Sarthak - Needs Review)
    - 2020 block group (Sarthak - Needs Review)
- SDOH Indices
    - 2014 census tract
- Opportunity Index
    - most recent; census tract
    - most recent; county
- Social Vulnerability Index
    - 2016 county (Augustyn -  Review)
    - 2016 census tract (Augustyn -  Review)
    - 2020 county (Augustyn To Do)
    - 2020 census tract (Augustyn To Do)
    - 2018 county (Sarthak To Do)
    - 2018 census tract (Sarthak To Do)
    - Link to 2020 SVI GeoJSON files (county-level and tract-level): https://drive.google.com/drive/folders/1ke84gY2yCA90R2S0-YAZrZo9rJPl7I-R?usp=share_link

###  Contributors

- Marynia Kolak
- Sarthak Joshi
- Augustyn Crane
- Adam Cox
- Mandela Gadri

### Metadata Markdown Files

If you are looking for the Metadata or DataDictionary folders, these are now located in

```
MetadataManager/manager/metadata/
```

## MetadataManager Flask App

### Configure

```
cp ./flask/.env.example ./flask/.env
```

Required .env content:

`SOLR_HOST`: full url to Solr endpoint

### Install/Run locally

A dev deploy will serve the app on Flask's default port (5000).

Create Python virtual environment:

```
python3 -m venv env
source ./env/bin/activate
```

Clone and install package

```
git clone https://github.com/healthyregions/SDOHPlace-MetadataManager
cd SDOHPlace-MetadataManager
pip install -e .
```

Run in debug mode:

```
flask --app MetadataManager.manager.app run --debug
```

`--debug` will auto-reload the app whenever a file is changed (though it seems like changes to HTML or CSS files may require the app to be stopped and restarted...).

To run as a background process with gunicorn, first set scripts to be executable:

```
sudo chmod +x ./scripts/*.sh
```

Then use

```
./scripts/start.sh
./scripts/stop.sh
./scripts/restart.sh
```

to control the application. A log will be created in `./scripts/.log`.

### Install/Run with Docker

The Docker deploy will serve the app on port 8080 with nginx.

Start containers

```
docker-compose up -d --build
```

Stop containers

```
docker-compose down
```
