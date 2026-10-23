import unittest
from datetime import datetime
from unittest.mock import patch

from monitoring.system import get_system_status


class SystemMetricsTests(unittest.TestCase):
    @patch("monitoring.system.psutil.boot_time", return_value=1000)
    @patch("monitoring.system.psutil.cpu_count", return_value=4)
    @patch("monitoring.system.psutil.disk_usage")
    @patch("monitoring.system.psutil.virtual_memory")
    @patch("monitoring.system.psutil.cpu_percent", return_value=27.5)
    @patch("monitoring.system.time.time", return_value=1600)
    def test_returns_timestamped_metrics(
        self, _time, _cpu_percent, virtual_memory, disk_usage, _cpu_count, _boot_time
    ):
        virtual_memory.return_value = type(
            "Memory", (), {"total": 1000, "used": 400, "percent": 40.0}
        )()
        disk_usage.return_value = type(
            "Disk", (), {"total": 2000, "used": 500, "percent": 25.0}
        )()

        metrics = get_system_status()

        self.assertEqual(
            set(metrics),
            {
                "timestamp",
                "cpu_percent",
                "memory_percent",
                "disk_percent",
                "uptime_seconds",
            },
        )
        self.assertEqual(metrics["cpu_percent"], 27.5)
        self.assertEqual(metrics["memory_percent"], 40.0)
        self.assertEqual(metrics["disk_percent"], 25.0)
        self.assertEqual(metrics["uptime_seconds"], 600)
        self.assertIsInstance(datetime.fromisoformat(metrics["timestamp"]), datetime)


if __name__ == "__main__":
    unittest.main()