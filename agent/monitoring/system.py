import time
from datetime import datetime, timezone

import psutil

def get_system_status():
    """Collect a small, timestamped snapshot suitable for the metrics API."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
    }