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
- Yong Wook Kim
- Mandela Gadri
- Arli Coli
- Camrin Garrett

## `manager` Flask App

### Management Commands

Use `flask [command] [subcommand] --help` to see the specific arguments for each command. A general summary of usage for each command follows below.

#### Registry

`flask registry index [--env stage|prod]`

Index a specific record (provide the id), or all records, into Solr. Use `--clean` to remove all existing documents from the Solr core before indexing (for a full refresh).

- `--env stage`: Index to staging core
- `--env prod`: Index to production core
- If no `--env` specified, defaults to production

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

```
cp env.example .env
```

To get started, you won't need to edit any environment variables.

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

The Docker deploy uses Traefik as a reverse proxy. The main application is accessible on port 80. The Traefik dashboard is available at `https://traefik.${DOMAIN_NAME}` (protected with basic authentication).

It will also run Solr at http://localhost:8983 and will automatically create cores named `blacklight-core-stage` and `blacklight-core-prod`

**Data Persistence:** Solr core data is automatically persisted using Docker volumes, so your indexed data survives container restarts.

**Volume Mount Details:** The system uses a bind mount (`./solr-data:/var/solr/data`) to persist Solr core data on the host machine. This means:
- Solr index data is stored in the local `solr-data/` directory
- Data persists between container restarts and system reboots
- The `solr-data/` directory is automatically created with the correct core structure
- Core names are dynamically configured via environment variables (`SOLR_CORE_STAGE`, `SOLR_CORE_PROD`)

Start containers:

```bash
docker compose up -d --build
```

This will build a Docker image and run a container from that image.

#### Configuration

You can customize core names and other settings using environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `SOLR_CORE_STAGE` | Staging core name | `blacklight-core-stage` |
| `SOLR_CORE_PROD` | Production core name | `blacklight-core-prod` |
| `SOLR_HOST` | Solr server URL | `http://localhost:8983/solr` |
| `GBL_HOST` | GeoBlacklight URL | (optional) |
| `ADMIN_USERNAME` | Default admin username | `admin` |
| `ADMIN_EMAIL` | Default admin email (used for login) | `admin@example.com` |
| `ADMIN_PASSWORD` | Default admin password | `changeme` |

**Using .env file:**

Create your environment file from the example:

```bash
cp env.example .env
```

Edit `.env` and set your configuration. For Docker deployments, you must set `DOMAIN_NAME`:

```bash
# For local Docker development
DOMAIN_NAME=sdoh.metadata.local

# For production with HTTPS
DOMAIN_NAME=your-domain.com
LETSENCRYPT_EMAIL=your-email@example.com
```

**Important:** Change the default admin credentials before deploying to production:

```bash
ADMIN_USERNAME=admin
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password-here
```

You can also customize Solr core names if needed:

```bash
SOLR_CORE_STAGE=my-stage-core
SOLR_CORE_PROD=my-prod-core
```

**Using environment variables:**
```bash
export SOLR_CORE_STAGE=my-stage-core
export SOLR_CORE_PROD=my-prod-core
docker compose up
```

If you are also running the SDOHPlace Data Discovery application locally, you can point it to this solr instance by editing the `.env` for that project:

```env
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-stage'
```

Shutdown containers:
```bash
docker compose down
```

#### Traefik Reverse Proxy

The Docker setup uses **Traefik** as a reverse proxy and load balancer. Traefik automatically discovers services in Docker containers and routes traffic accordingly.

**Access Points:**
- **Main Application**: http://localhost (or http://your-server-ip) / `https://${DOMAIN_NAME}`
- **Solr Admin**: `https://solr.${DOMAIN_NAME}` (requires authentication)
- **Traefik Dashboard**: http://localhost:8080 (or http://your-server-ip:8080) / `https://traefik.${DOMAIN_NAME}` (requires authentication)

**Traefik Dashboard Authentication:**

The Traefik dashboard is protected with HTTP basic authentication. Default credentials are:
- **Username:** admin
- **Password:** changeme

To set custom credentials:
1. **Generate a password hash:**
   - Go to https://www.apivoid.com/tools/htpasswd-generator/
   - In the input field, enter your credentials in the format: `username:password`
     - Example: `admin:MySecurePassword123`
   - Click the **"Generate Htpasswd"** button
   - The tool will generate a hash like: `admin:$2a$10$xyz...hashedpassword`
   
2. **Escape dollar signs for docker-compose:**
   - Copy the generated hash
   - Replace every single `$` with `$$` (double dollar signs)
   - Example: `admin:$2a$10$xyz` becomes `admin:$$2a$$10$$xyz`

3. **Update your `.env` file:**
   ```bash
   TRAEFIK_AUTH=admin:$$2a$$10$$yourhashedpasswordhere
   ```

4. **Restart containers:**
   ```bash
   docker compose restart traefik
   ```

**Solr Admin Authentication:**

The Solr admin interface is also protected with HTTP basic authentication. Default credentials are:
- **Username:** admin
- **Password:** changeme

To set custom credentials:
1. **Generate a password hash:**
   - Go to https://www.apivoid.com/tools/htpasswd-generator/
   - In the input field, enter your credentials in the format: `username:password`
     - Example: `admin:MySecureSolrPassword123`
   - Click the **"Generate Htpasswd"** button
   - The tool will generate a hash like: `admin:$2a$10$xyz...hashedpassword`
   
2. **Escape dollar signs for docker-compose:**
   - Copy the generated hash
   - Replace every single `$` with `$$` (double dollar signs)
   - Example: `admin:$2a$10$xyz` becomes `admin:$$2a$$10$$xyz`

3. **Update your `.env` file:**
   ```bash
   SOLR_AUTH=admin:$$2a$$10$$yourhashedpasswordhere
   ```

4. **Restart containers:**
   ```bash
   docker compose restart solr traefik
   ```

**Features:**
- Automatic service discovery - No manual configuration needed
- Load balancing - Built-in load balancing
- Health checks - Automatic health monitoring
- Dashboard - Web UI to monitor services with authentication
- Auto-restart - Services restart automatically on VM reboot

**Common Commands:**

```bash
# View Traefik logs
docker compose logs traefik

# View all service logs
docker compose logs -f

# Restart specific service
docker compose restart manager
```

**Adding SSL/HTTPS:**

The setup supports automatic HTTPS with Let's Encrypt. To enable:

1. **Set environment variables** in `.env`:
   ```bash
   DOMAIN_NAME=your-domain.com
   LETSENCRYPT_EMAIL=your-email@example.com
   ```

2. **Start services**:
   ```bash
   docker compose up -d
   ```

3. **Access your site**:
   - **Main App**: https://your-domain.com (secure)
   - **Solr Admin**: https://solr.your-domain.com
   - **Traefik Dashboard**: https://traefik.your-domain.com (requires authentication)

**Features:**
- Automatic SSL certificate generation and renewal
- HTTP to HTTPS redirect
- Fallback to IP address if no domain set
- Modern TLS configuration

**Disable HTTPS:**
Leave the variables empty in `.env` to use HTTP only:
```bash
DOMAIN_NAME=
LETSENCRYPT_EMAIL=
```

### Getting Started with Docker

When you first start the application with `docker compose up -d --build`, the system will automatically:

1. Create a default admin user with credentials from your `.env` file (defaults: `admin@example.com` / `changeme`)
2. Index all metadata records into both the staging and production Solr cores

You can monitor the initialization progress by checking the logs:

```bash
docker compose logs -f manager
```

Once you see "Initialization complete!" in the logs, you can log in to the application using the credentials you set in your `.env` file:
- **Email:** Value from `ADMIN_EMAIL` (default: `admin@example.com`)
- **Password:** Value from `ADMIN_PASSWORD` (default: `changeme`)

**Security Note:** Make sure to change `ADMIN_PASSWORD` in your `.env` file before deploying to production!

**Note:** On every container restart, the system will re-index all records to ensure Solr cores are in sync with the JSON files. The admin user creation will be skipped if it already exists.

#### Manual Indexing

If you need to manually re-index records later (e.g., after adding new records), you can enter the container and run the indexing command:

```bash
docker exec -it sdoh-manager bash
flask registry index --env stage  # Index to staging core
flask registry index --env prod   # Index to production core
```

You may see a 503 error from Solr during indexing - this is expected and not a problem (it's a health status ping that is not enabled on the docker build of the core).

### Backup and Restore

The project includes automated backup scripts to preserve critical application data from both the Solr index and the Manager SQLite database.

#### Creating Backups

To create a manual backup:

```bash
# Make the script executable (first time only)
chmod +x scripts/backup.sh

# Run the backup
./scripts/backup.sh
```

The backup script will:
- Create timestamped backup archives in `./backups/`
- Back up Solr data directory (`./solr-data/`)
- Back up SQLite database (`./manager/data.db`)
- Compress backups as `.tar.gz` files
- Clean up old backups based on retention policy (default: 30 days)
- Log all operations to `./backups/backup.log`

**Environment Variables:**

You can customize the backup behavior using environment variables:

```bash
# Custom backup directory
BACKUP_DIR=/mnt/backups ./scripts/backup.sh

# Keep backups for 60 days instead of 30
RETENTION_DAYS=60 ./scripts/backup.sh

# Disable compression
COMPRESS=false ./scripts/backup.sh

# Custom log file
LOG_FILE=/var/log/sdoh-backup.log ./scripts/backup.sh
```

**Container Status:**

The backup script can run while containers are running or stopped. However, for best data consistency and safety, it's recommended to stop containers first:

```bash
# Recommended: Stop containers for consistent backups
docker compose down
./scripts/backup.sh
docker compose up -d
```

**Running backups while containers are active:**
- The script will warn you but will proceed with the backup
- This is acceptable for quick/test backups or automated scheduled backups
- Risk: May capture data files mid-write, potentially causing inconsistencies or corruption
- Use case: Convenient for frequent automated backups where brief inconsistencies are acceptable

#### Restoring Backups

To restore from a backup:

```bash
# Make the script executable (first time only)
chmod +x scripts/restore.sh

# List available backups
ls -lt ./backups/

# Stop containers first (required)
docker compose down

# Restore a specific backup
./scripts/restore.sh sdoh-backup-20241106_143022

# Start containers after restore
docker compose up -d
```

The restore script will:
- **Require containers to be stopped** (will exit if containers are running)
- Show backup metadata
- Ask for confirmation before proceeding
- Create a pre-restore backup of current data
- Restore Solr data and SQLite database
- Log all operations to `./backups/restore.log`

**Important:** Containers MUST be stopped before restore to prevent data corruption.

#### Automated Backups with Cron

To schedule automatic daily backups using cron:

1. Make the backup script executable:
   ```bash
   chmod +x scripts/backup.sh
   ```

2. Edit your crontab:
   ```bash
   crontab -e
   ```

3. Add a cron job (example runs daily at 2:00 AM):
   ```bash
   0 2 * * * cd /path/to/SDOHPlace-MetadataManager && ./scripts/backup.sh >> ./backups/cron.log 2>&1
   ```

See `scripts/backup-cron-example.sh` for more cron job examples.

#### Automated Backups with Systemd Timer

For systems using systemd, you can use a timer unit instead of cron:

1. Copy the service and timer files:
   ```bash
   sudo cp scripts/sdoh-backup.service /etc/systemd/system/
   sudo cp scripts/sdoh-backup.timer /etc/systemd/system/
   ```

2. Edit the service file to set the correct paths:
   ```bash
   sudo nano /etc/systemd/system/sdoh-backup.service
   ```

3. Enable and start the timer:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sdoh-backup.timer
   sudo systemctl start sdoh-backup.timer
   ```

4. Check timer status:
   ```bash
   sudo systemctl status sdoh-backup.timer
   sudo systemctl list-timers
   ```

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