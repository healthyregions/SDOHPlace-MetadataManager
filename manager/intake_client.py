import os
import requests

class IntakeApiError(Exception):
    pass

class IntakeClient:
    def __init__(self):
        self.base_url = os.getenv("INTAKE_API_BASE_URL", "").rstrip("/")
        self.token = os.getenv("INTAKE_API_TOKEN", "")
        self.timeout = int(os.getenv("INTAKE_API_TIMEOUT", "10"))

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
    ):
        body = {}
        if payload_json is not None:
            body["payload_json"] = payload_json
        if status:
            body["status"] = status
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

    def mark_published(self, submission_id, record_id=None):
        body = {}
        if record_id:
            body["record_id"] = record_id
        return self._request(
            "POST",
            f"/submissions/{submission_id}/published",
            json_payload=body,
        )

    def mark_record_deleted(self, submission_id):
        return self._request(
            "POST",
            f"/submissions/{submission_id}/record-deleted",
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
