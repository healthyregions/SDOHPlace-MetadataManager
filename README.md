# SDOH Place - Metadata Manager

This is the metadata manager for the SDOH & Place Project, a new map-based search platform for SDOH data discovery that will curate and integrate validated geospatial data relevant to public health at multiple scales.

## Metadata Creation

### Schema

We are using the Aardvark schema from [OpenGeoMetadata (OGM) Aardvark Schema](https://opengeometadata.org/ogm-aardvark/), along with some extra fields specifically for our needs. These fields are:

Custom metadata schema for this project:
- Spatial Resolution (=tract, zip code, county)
- Spatial Resolution Note
- Data Variables
- Methods Variables

###  Contributors

- Marynia Kolak
- Sarthak Joshi
- Augustyn Crane
- Adam Cox
- Mandela Gadri
- Arli Coli
- Camrin Garrett

## `manager` Flask App

### Management Commands

Use `flask [command] [subcommand] --help` to see the specific arguments for each command. A general summary of usage for each command follows below.

#### Registry

`flask registry index`

Index a specific record (provide the id), or all records, into Solr. Use `--clean` to remove all existing documents from the Solr core before indexing (for a full refresh).

**Stage/Prod Workflow:** Use `--env` to specify staging or production:

```bash
flask registry index --env stage    # Index to staging (preview)
flask registry index --env prod     # Index to production (admin only via web UI)
```

`flask registry resave-records`

Loads all records and then runs "save_data()" on each one, triggers whatever data cleaning is applied to each field.

`flask registry bulk-update`

Provides the capability of updating all instances of a specific value in a field with a new value (use with caution!).

#### Users

`flask user create [username] [email] [password]`

Create a new user with their username, email, and password. Note that only email and password are used to login, not the username.

`flask user reset-password`

Sets the specified user's password to a random 6 character string.

`flask user change-password`

Update a user's password to the provided string.

### Local Install

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

Copy the environment file:

```bash
cp .env.example .env
```

Edit `.env` and set a secure `SECRET_KEY`. For the stage/prod workflow, you can also configure:
- `SOLR_CORE_STAGE` (default: `blacklight-core-stage`)
- `SOLR_CORE_PROD` (default: `blacklight-core-prod`)

#### Run dev server

Run in debug mode:

```
flask run --debug
```

`--debug` will auto-reload the app whenever a file is changed (though it seems like changes to HTML or CSS files sometimes require the app to be stopped and restarted...).

You can now view the app at `http://localhost:5000`

#### Deploying with gunicorn

To run as a background process with gunicorn, first set the scripts to be executable:

```
sudo chmod +x ./scripts/*.sh
```

Then use the following commands to start/stop/restart the application. A log will be written to `./scripts/.log`.

```
./scripts/start_flask.sh
./scripts/stop_flask.sh
./scripts/restart_flask.sh
```

With gunicorn running, you can view the app at `http://localhost:8000`, or set a proxy through a production webserver like nginx.

You can change `PORT` in `.env` if you want gunicorn to listen on a different port than 8000.

### Install/Run with Docker

The Docker deploy will serve the app on port 8000 and Solr on port 8983.

#### Quick Start (Recommended)

Use the quickstart script to automatically set up everything:

**Linux/Mac:**
```bash
chmod +x docker-quickstart.sh
./docker-quickstart.sh
```

**Windows (PowerShell):**
```powershell
.\docker-quickstart.ps1
```

This will:
- Create `.env.docker` from the example
- Start Docker containers
- Create staging and production Solr cores
- Display next steps

#### Manual Setup

Start containers:

```bash
docker compose up -d --build
```

This will build a Docker image and run containers. By default, it creates a core named `blacklight-core-dev`.

**For Stage/Prod Workflow:** Create staging and production cores:

```bash
# Create staging core
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default"

# Create production core
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default"
```

Shutdown containers:
```bash
docker compose down
```

### Getting Started with Docker

Once the application is running, you'll need to create a user for login and then index records.

Enter the docker container:

```bash
docker exec -it sdoh-manager bash
```

Create an admin user:

```bash
flask user create admin admin@example.com password
```

**Important:** Login uses **email** and **password**, not the username!

Index records to staging (all users) or production (admin only):

```bash
# Index to staging
flask registry index --env stage

# Index to production (admin only)
flask registry index --env prod
```

**Note:** You may see a 503 error from Solr health checks - this is normal and can be ignored.

### Connecting to Data Discovery App

If you're running the SDOHPlace Data Discovery application locally, point it to the appropriate Solr core:

**For staging preview:**
```env
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-stage'
```

**For production:**
```env
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-prod'
```

### Docker Documentation

For detailed Docker setup and troubleshooting, see [DOCKER_SETUP.md](./DOCKER_SETUP.md)

## Running the coverage command as a standalone script

The coverage checking command can be run as a standalone script, outside of the Flask framework. This comes with many fewer python dependencies, and will not alter any data in the records, it just gives you an output text file of ids that can be pasted into the metadata manager "Highlight IDs" field.

### How to set it up

This process must be done in a terminal or command line interface.

In a new directory, create a new Python virtual environment. We recommend using the included `venv` package for this.

```
python3 -m venv env
```

This command will create a new "virtual environment" which is very important when dealing with Python. To activate this environment, run

```
source ./env/bin/activate
```

on a mac or linux operating system. On windows, use

```
.\env\Scripts\activate
```

You will see a `(env)` prefix in your command line prompt. Great! All this does is set some environment variables shortcuts. The environment is deactivated if you close your terminal, or run the `deactivate` command.

Now that the virtual environment is active, you can install Python packages directly into it, which allows you to keep your default Python installation on your system untouched (very important).

For this script, we just need the [geopandas]() package, which we can install using the `pip` command:

```
pip install geopandas
```

Great! Try running `python -c "import geopandas"` in your terminal. If you don't get an error, all is well.

Now, download the script from this repository and put it in your directory: https://github.com/healthyregions/SDOHPlace-MetadataManager/blob/main/manager/coverage/coverage.py. Again, no need to clone the whole repository to run this one script.

You should now be able to run this command, with your virtual environment activated, and you'll see the embedded help content for the script:

```
python coverage.py --help
```

If you get an `ImportError`, make sure you have installed `geopandas` as described above, and that you have your virtual environment activated.

## How to run it

The script must be given a couple of arguments to work, and there are some additional options you can add to the process.

1. Input file: Provide the local path to a CSV file that you want to analyze (for example, "SVI 2022.csv")
2. Geography: Indicate what geography level this file should be matched against, one of `state`, `county`, `tract`, `blockgroup`, or `zcta`.
3. Id field, `-i` (optional): The name of the field in your input CSV that holds a GEOID or FIPS-like identifier. This field will be converted to a HEROP_ID during the check, and compared against the source geography file. If not provided, the script will look for a field called FIPS.
4. Output, `-o` (optional): A text file to which the final highlight ids will be written. You can then open this file and copy its contents directly into the Metadata Manager web interface. If not provided, the script will perform the check and report the number of missing ids in our input file.

Putting these arguments together, let's assume we have a file called `SVI 2022.csv` that has a list of tracts in it, and the column in that file with FIPS codes is called `tractfips`. A run of the script that outputs the ids to a text file would look like this:

```
python coverage.py "SVI 2022.csv" tract -i tractfips -o svi-highlight-ids.txt
```

