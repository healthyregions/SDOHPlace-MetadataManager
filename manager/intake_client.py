import os
import requests

SPATIAL_LEVEL_MAP = {
    "State": "state",
    "County": "county",
    "Census Tract": "tract",
    "Census Block Group": "bg",
    "Zip Code Tabulation Area (ZCTA)": "zcta",
}

BOUNDARY_YEARS = ("2018", "2010")

UPLOAD_KINDS = {
    "csv": (".csv",),
    "geo": (".zip", ".geojson", ".gpkg"),
}

MAX_UPLOAD_BYTES = 500 * 1024 * 1024

def format_bytes(num_bytes):
    value = int(num_bytes or 0)
    if value >= 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024 * 1024):.1f} GB"
    if value >= 1024 * 1024:
        return f"{round(value / (1024 * 1024))} MB"
    return f"{max(1, round(value / 1024))} KB"

def upload_kind_for_filename(filename):
    """Return the pipeline upload kind for a filename, or None if unsupported."""
    lowered = str(filename or "").lower()
    for kind, extensions in UPLOAD_KINDS.items():
        if lowered.endswith(extensions):
            return kind
    return None

class IntakeApiError(Exception):
    pass

class SpatialPipelineError(IntakeApiError):
    pass

class IntakeClient:
    def __init__(self):
        self.base_url = os.getenv("INTAKE_API_BASE_URL", "").rstrip("/")
        self.token = os.getenv("INTAKE_API_TOKEN", "")
        self.timeout = int(os.getenv("INTAKE_API_TIMEOUT", "10"))
        self.upload_timeout = int(os.getenv("INTAKE_UPLOAD_TIMEOUT", "900"))

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method, path, json_payload=None, params=None):
        if not self.base_url:
            raise IntakeApiError("INTAKE_API_BASE_URL is not set")
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_payload,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise IntakeApiError(str(exc)) from exc

        if not response.ok:
            details = response.text
            raise IntakeApiError(f"{response.status_code} {response.reason}: {details}")

        if not response.text:
            return {}

        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    def list_submissions(self, status=None):
        params = {}
        if status:
            params["status"] = status
        return self._request("GET", "/submissions", params=params)

    def get_submission(self, submission_id):
        return self._request("GET", f"/submissions/{submission_id}")

    def update_submission(
        self,
        submission_id,
        payload_json=None,
        status=None,
        submitter_email=None,
        submitter_name=None,
        record_id=None,
    ):
        body = {}
        if payload_json is not None:
            body["payload_json"] = payload_json
        if status:
            body["status"] = status
        if record_id:
            body["record_id"] = record_id
        if submitter_email is not None:
            body["submitter_email"] = submitter_email
        if submitter_name is not None:
            body["submitter_name"] = submitter_name
        return self._request("PATCH", f"/submissions/{submission_id}", json_payload=body)

    def delete_submission(self, submission_id, actor="admin", reviewer=None):
        params = {"actor": actor}
        if reviewer:
            params["reviewer"] = reviewer
        try:
            self._request("DELETE", f"/submissions/{submission_id}", params=params)
            return {"deleted": True, "soft_deleted": False}
        except IntakeApiError as exc:
            if "405" not in str(exc):
                raise
            self.update_submission(submission_id, status="deleted")
            return {"deleted": True, "soft_deleted": True}

    def decide_submission(
        self,
        submission_id,
        decision,
        notes=None,
        record_id=None,
        reviewed_by=None,
        reviewed_payload=None,
    ):
        body = {
            "decision": decision,
            "notes": notes,
            "record_id": record_id,
            "reviewed_by": reviewed_by,
            "reviewed_payload": reviewed_payload,
        }
        return self._request(
            "POST",
            f"/submissions/{submission_id}/decision",
            json_payload=body,
        )

    def mark_published(self, submission_id, record_id=None, index_env="prod", notify=True):
        body = {"index_env": index_env, "notify": notify}
        if record_id:
            body["record_id"] = record_id
        return self._request(
            "POST",
            f"/submissions/{submission_id}/published",
            json_payload=body,
        )

    def mark_record_deleted(self, submission_id, index_env=None):
        body = {}
        if index_env:
            body["index_env"] = index_env
        return self._request(
            "POST",
            f"/submissions/{submission_id}/record-deleted",
            json_payload=body,
        )

    def spatial_upload_url(self, record_id, filename, file_size=None):
        body = {"record_id": record_id, "filename": filename}
        if file_size is not None:
            body["file_size"] = file_size
        return self._request("POST", "/spatial/upload-url", json_payload=body)

    def spatial_upload_file(self, upload_url, fileobj, content_type="text/csv"):
        try:
            response = requests.put(
                upload_url,
                data=fileobj,
                headers={"Content-Type": content_type},
                timeout=self.upload_timeout,
            )
        except requests.Timeout as exc:
            raise SpatialPipelineError(
                "The upload ran out of time before it finished. This usually means the file is "
                "large or the connection is slow. Try again, or raise INTAKE_UPLOAD_TIMEOUT."
            ) from exc
        except requests.RequestException as exc:
            raise SpatialPipelineError(
                f"The file could not be uploaded. Check the connection and try again. ({exc})"
            ) from exc
        if response.status_code == 403:
            raise SpatialPipelineError(
                "The upload window ran out before the file finished transferring. "
                "Click Generate again to start a fresh upload."
            )
        if not response.ok:
            raise SpatialPipelineError(
                f"The file could not be uploaded (error {response.status_code} "
                f"{response.reason}). Try again, or contact the team if it keeps failing."
            )

    def spatial_start(
        self,
        record_id,
        s3_key,
        boundary_year=None,
        spatial_level=None,
        geo_id_column=None,
        upload_kind="csv",
    ):
        body = {
            "record_id": record_id,
            "s3_key": s3_key,
            "upload_kind": upload_kind,
        }
        if upload_kind == "csv":
            body["boundary_year"] = boundary_year
            body["spatial_level"] = spatial_level
            if geo_id_column:
                body["geo_id_column"] = geo_id_column
        return self._request("POST", "/spatial/start", json_payload=body)

    def spatial_status(self, record_id, s3_key):
        return self._request(
            "GET",
            "/spatial/status",
            params={"record_id": record_id, "key": s3_key},
        )

    def find_submission_by_record_id(self, record_id):
        if not record_id:
            return None
        payload = self.list_submissions()
        items = payload if isinstance(payload, list) else []
        if isinstance(payload, dict):
            for key in ["items", "results", "submissions", "data"]:
                value = payload.get(key)
                if isinstance(value, list):
                    items = value
                    break
        for item in items:
            if not isinstance(item, dict):
                continue
            candidate = item.get("record_id") or (item.get("payload_json") or {}).get("id")
            if candidate and str(candidate) == str(record_id):
                return item
        return None
