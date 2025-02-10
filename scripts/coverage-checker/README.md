# SDOH&Place Coverage Checker
Simple data pipeline to report on coverage for SDOH datasets

## Setup
Clone this repository:
```bash
git clone TBD
cd TBD
```

Prepare file mapping:
```python
file_map = {
   'study/dataset/file/path': 'master/geography/file/path',
   ...
}
```

Adjust `.env` if needed:
```bash
vi .env
```

## Running in Python
Install dependencies:
```bash
pip install -r requirements.txt --user
```

Run coverage script:
```bash
./coverage.py
```

## Running in Docker
Build and run the image:
```bash
docker compose up --build
```

