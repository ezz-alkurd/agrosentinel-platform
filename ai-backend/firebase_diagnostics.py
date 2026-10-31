"""Read-only Firebase diagnostics and bounded, redacted operation errors."""
import re

REQUIRED_STORAGE_PERMISSIONS = ("storage.objects.create", "storage.objects.get", "storage.objects.update")


def describe_error(error):
    text = str(error)
    text = re.sub(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", "[redacted key]", text, flags=re.S)
    text = re.sub(r"https?://[^\s]+", "[endpoint]", text)
    text = re.sub(r"(?i)(bearer\s+|(?:access_token|token|key|signature)\s*[=:]\s*)[^\s,;]+", r"\1[redacted]", text)
    text = " ".join(text.split())[:650]
    lower = text.lower()
    if any(word in lower for word in ("billing", "blaze", "spark", "accountdisabled", "userprojectaccountproblem")):
        hint = "Check Firebase Storage billing: the project needs an active Blaze billing account."
    elif "forbidden" in type(error).__name__.lower() or any(word in lower for word in ("permission", "denied", "403")):
        hint = "Check this bucket's service-account IAM permissions and active Storage billing; do not open public rules."
    elif "notfound" in type(error).__name__.lower() or "404" in lower:
        hint = "Check the exact Storage bucket name and whether Storage is provisioned."
    elif any(word in type(error).__name__.lower() for word in ("transport", "connection", "timeout")):
        hint = "Check network access, proxy/firewall and Google API connectivity."
    else:
        hint = "Check the indicated operation and Firebase configuration."
    return f"{type(error).__name__}: {text} {hint}"


class FirebaseOperationError(RuntimeError):
    def __init__(self, operation, error):
        super().__init__(f"{operation}: {describe_error(error)}")


def check_storage_permissions(bucket):
    granted = set(bucket.test_iam_permissions(list(REQUIRED_STORAGE_PERMISSIONS), timeout=8, retry=None))
    missing = sorted(set(REQUIRED_STORAGE_PERMISSIONS) - granted)
    if missing:
        raise PermissionError("Storage IAM permissions missing: " + ", ".join(missing))


def check_firebase():
    from firebase_config import initialize_firebase
    from google.auth.transport.requests import Request
    import firebase_admin
    try:
        db, bucket = initialize_firebase()
    except Exception as error:
        print("FAIL [Firebase configuration]: " + describe_error(error), flush=True)
        return False
    print(f"Firebase project: {firebase_admin.get_app().project_id}; Storage bucket: {bucket.name}", flush=True)
    request = Request()
    def bounded_request(*args, **kwargs):
        kwargs["timeout"] = 8
        return request(*args, **kwargs)
    try:
        credential = firebase_admin.get_app().credential.get_credential()
        credential.refresh(bounded_request)
        print("PASS [Service-account authentication]", flush=True)
    except Exception as error:
        print("FAIL [Service-account authentication]: " + describe_error(error), flush=True)
        return False
    passed = True
    events = []
    try:
        events = list(db.collection("events").order_by("timestamp", direction="DESCENDING").limit(1).stream(timeout=8, retry=None))
        print(f"PASS [Firestore event read]; latest record present: {bool(events)}", flush=True)
    except Exception as error:
        print("FAIL [Firestore event read]: " + describe_error(error), flush=True)
        passed = False
    try:
        check_storage_permissions(bucket)
        print("PASS [Storage IAM]: create/read/update permissions granted. This is not an upload test.", flush=True)
        if events:
            path = events[0].to_dict().get("storage_path")
            if path and not bucket.blob(path).exists(timeout=8, retry=None):
                raise FileNotFoundError("Latest event's evidence object is missing from this bucket.")
    except Exception as error:
        print("FAIL [Storage bucket/permissions]: " + describe_error(error), flush=True)
        passed = False
    print("No cloud objects or events were created. Actual upload and phone receipt require a real detection.", flush=True)
    return passed
