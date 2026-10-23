import getpass
import json
import os
import stat
import tempfile
import uuid
from urllib.parse import urlsplit


APP_NAME = "FRIDAY Cloud Agent"
AGENT_VERSION = "0.1.0"

API_BASE_URL = os.getenv(
    "FRIDAY_API_BASE_URL",
    "https://monitoring-metrics-api.onrender.com",
).strip().rstrip("/")
METRICS_URL = f"{API_BASE_URL}/api/v1/agent/metrics"
DEVICE_TOKEN = os.getenv("FRIDAY_DEVICE_TOKEN", "").strip()
if not DEVICE_TOKEN:
    DEVICE_TOKEN = os.getenv("FRIDAY_AGENT_TOKEN", "").strip()

CLOUD_ID = os.getenv(
    "FRIDAY_CLOUD_ID",
    ""
)


def _heartbeat_interval():
    value = os.getenv("FRIDAY_HEARTBEAT_INTERVAL", "30")
    try:
        interval = int(value)
    except ValueError as exc:
        raise ValueError("FRIDAY_HEARTBEAT_INTERVAL must be an integer") from exc

    if not 5 <= interval <= 3600:
        raise ValueError(
            "FRIDAY_HEARTBEAT_INTERVAL must be between 5 and 3600 seconds"
        )

    return interval


def _validate_api_base_url(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("FRIDAY_API_BASE_URL must be a valid HTTPS base URL")


HEARTBEAT_INTERVAL = _heartbeat_interval()
_validate_api_base_url(API_BASE_URL)

FRIDAY_HOME = os.path.expanduser("~/FRIDAY")
DEVICE_CREDENTIALS_PATH = os.path.join(FRIDAY_HOME, "device_credentials.json")
INSTALLATION_ID_PATH = os.path.join(FRIDAY_HOME, "installation_id")
LEGACY_DEVICE_TOKEN_PATH = os.path.join(FRIDAY_HOME, "device_token")

FRIDAY_STORAGE = os.path.join(
    FRIDAY_HOME,
    "storage"
)

FRIDAY_BACKUP = os.path.join(
    FRIDAY_HOME,
    "backups"
)

FRIDAY_LOGS = os.path.join(
    FRIDAY_HOME,
    "logs"
)


def create_directories():
    os.makedirs(FRIDAY_HOME, mode=0o700, exist_ok=True)
    os.chmod(FRIDAY_HOME, 0o700)

    directories = [
        FRIDAY_STORAGE,
        FRIDAY_BACKUP,
        FRIDAY_LOGS,
    ]

    for directory in directories:
        os.makedirs(directory, mode=0o700, exist_ok=True)
        os.chmod(directory, 0o700)


def _write_private_file(path, content):
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=".friday-",
        dir=FRIDAY_HOME,
    )
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as state_file:
            state_file.write(content)
            state_file.flush()
            os.fsync(state_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def get_installation_id():
    try:
        path_stat = os.lstat(INSTALLATION_ID_PATH)
    except FileNotFoundError:
        path_stat = None

    if path_stat is not None:
        if not stat.S_ISREG(path_stat.st_mode):
            raise ValueError("The installation ID path must be a regular file")
        os.chmod(INSTALLATION_ID_PATH, 0o600)
        with open(INSTALLATION_ID_PATH, encoding="utf-8") as state_file:
            installation_id = state_file.read().strip()
        try:
            return str(uuid.UUID(installation_id))
        except ValueError as exc:
            raise ValueError("The saved installation ID is invalid") from exc

    installation_id = str(uuid.uuid4())
    _write_private_file(INSTALLATION_ID_PATH, f"{installation_id}\n")
    return installation_id


def load_device_credentials():
    if DEVICE_TOKEN:
        return {"device_token": DEVICE_TOKEN, "device_id": None}

    try:
        credentials_stat = os.lstat(DEVICE_CREDENTIALS_PATH)
    except FileNotFoundError:
        credentials_stat = None

    if credentials_stat is not None:
        if not stat.S_ISREG(credentials_stat.st_mode):
            raise ValueError("The saved device credentials must be a regular file")
        os.chmod(DEVICE_CREDENTIALS_PATH, 0o600)
        with open(DEVICE_CREDENTIALS_PATH, encoding="utf-8") as state_file:
            credentials = json.load(state_file)
        if not isinstance(credentials, dict):
            raise ValueError("The saved device credentials are invalid")
        token = credentials.get("device_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("The saved device credentials contain no device token")
        device_id = credentials.get("device_id")
        if device_id is not None and not isinstance(device_id, str):
            raise ValueError("The saved device ID is invalid")
        return {"device_token": token.strip(), "device_id": device_id}

    try:
        legacy_stat = os.lstat(LEGACY_DEVICE_TOKEN_PATH)
    except FileNotFoundError:
        legacy_stat = None

    if legacy_stat is not None:
        if not stat.S_ISREG(legacy_stat.st_mode):
            raise ValueError("The legacy device token must be a regular file")
        os.chmod(LEGACY_DEVICE_TOKEN_PATH, 0o600)
        with open(LEGACY_DEVICE_TOKEN_PATH, encoding="utf-8") as token_file:
            token = token_file.read().strip()
        if not token:
            raise ValueError("The legacy device token is empty")
        return {"device_token": token, "device_id": None}

    return None


def save_device_credentials(device_id, device_token):
    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("The API returned an invalid device ID")
    if not isinstance(device_token, str) or not device_token.strip():
        raise ValueError("The API returned an invalid device token")

    credentials = {
        "device_id": device_id.strip(),
        "device_token": device_token.strip(),
    }
    _write_private_file(
        DEVICE_CREDENTIALS_PATH,
        json.dumps(credentials, separators=(",", ":")) + "\n",
    )


def get_config():
    return {
        "app_name": APP_NAME,
        "agent_version": AGENT_VERSION,
        "api_base_url": API_BASE_URL,
        "metrics_url": METRICS_URL,
        "cloud_id": CLOUD_ID,
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "friday_home": FRIDAY_HOME,
        "storage": FRIDAY_STORAGE,
        "backup": FRIDAY_BACKUP,
        "logs": FRIDAY_LOGS,
    }