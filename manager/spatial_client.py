import json
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import BotoCoreError, ClientError

class SpatialPipelineError(Exception):
    pass

SPATIAL_LEVEL_MAP = {
    "State": "state",
    "County": "county",
    "Census Tract": "tract",
    "Census Block Group": "bg",
    "Zip Code Tabulation Area (ZCTA)": "zcta",
}

UPLOAD_KINDS = {
    "csv": (".csv",),
    "geo": (".zip", ".geojson", ".json"),
}

BOUNDARY_YEARS = ("2018", "2010")

class SpatialClient:
    def __init__(self):
        self.bucket = os.getenv("SPATIAL_UPLOAD_BUCKET", "herop-sdohplace-upload")
        self.lambda_name = os.getenv("SPATIAL_LAMBDA_NAME", "herop-sdohplace-spatial")
        self.region = os.getenv("AWS_REGION", "us-east-2")
        self._s3 = None
        self._lambda = None
        
    def _s3_client(self):
        if self._s3 is None:
            self._s3 = boto3.client("s3", region_name=self.region)
        return self._s3

    def _lambda_client(self):
        if self._lambda is None:
            self._lambda = boto3.client("lambda", region_name=self.region)
        return self._lambda

    @staticmethod
    def new_job_key(record_id, filename):
        # format: uploads/{record_id}/{timestamp}/{filename}
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"uploads/{record_id}/{timestamp}/{filename}"

    @staticmethod
    def result_key(s3_key):
        folder, _, _filename = s3_key.rpartition("/")
        return f"{folder}/result.json" if folder else "result.json"

    @staticmethod
    def build_payload(
        record_id,
        s3_key,
        upload_kind,
        boundary_year=None,
        spatial_level=None,
        geo_id_column=None,
    ):
        payload = {
            "record_id": record_id,
            "s3_key": s3_key,
            "upload_kind": upload_kind,
        }
        if upload_kind == "csv":
            payload["boundary_year"] = int(boundary_year)
            payload["spatial_level"] = spatial_level
            if geo_id_column:
                payload["geo_id_column"] = geo_id_column
        return payload

    def upload_fileobj(self, fileobj, s3_key):
        try:
            self._s3_client().upload_fileobj(fileobj, self.bucket, s3_key)
        except (BotoCoreError, ClientError) as exc:
            raise SpatialPipelineError(f"S3 upload failed: {exc}") from exc

    def invoke(self, payload):
        try:
            response = self._lambda_client().invoke(
                FunctionName=self.lambda_name,
                InvocationType="Event",
                Payload=json.dumps(payload).encode("utf-8"),
            )
        except (BotoCoreError, ClientError) as exc:
            raise SpatialPipelineError(f"Lambda invoke failed: {exc}") from exc
        status = response.get("StatusCode")
        if status != 202:
            raise SpatialPipelineError(f"Lambda invoke returned status {status}")

    def fetch_result(self, result_key):
        """Return the parsed result.json, or None while the pipeline is still running."""
        try:
            response = self._s3_client().get_object(Bucket=self.bucket, Key=result_key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                return None
            raise SpatialPipelineError(f"Could not read result.json: {exc}") from exc
        except BotoCoreError as exc:
            raise SpatialPipelineError(f"Could not read result.json: {exc}") from exc
        try:
            return json.loads(response["Body"].read())
        except ValueError as exc:
            raise SpatialPipelineError(f"result.json is not valid JSON: {exc}") from exc
