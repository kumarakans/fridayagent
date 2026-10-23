import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

from agent import config


class DeviceCredentialTests(unittest.TestCase):
    def test_uses_handoff_api_endpoint_by_default(self):
        self.assertEqual(
            config.METRICS_URL,
            "https://monitoring-metrics-api.onrender.com/api/v1/agent/metrics",
        )

    def test_returns_none_when_device_is_not_registered(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("agent.config.DEVICE_TOKEN", ""),
            patch(
                "agent.config.DEVICE_CREDENTIALS_PATH",
                os.path.join(directory, "credentials.json"),
            ),
            patch(
                "agent.config.LEGACY_DEVICE_TOKEN_PATH",
                os.path.join(directory, "legacy-token"),
            ),
        ):
            self.assertIsNone(config.load_device_credentials())

    def test_saves_and_loads_private_device_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            credentials_path = os.path.join(directory, "credentials.json")
            with (
                patch("agent.config.FRIDAY_HOME", directory),
                patch("agent.config.DEVICE_CREDENTIALS_PATH", credentials_path),
            ):
                config.save_device_credentials("device-01", "device-secret")
                self.assertEqual(
                    config.load_device_credentials(),
                    {"device_id": "device-01", "device_token": "device-secret"},
                )

            self.assertEqual(stat.S_IMODE(os.stat(credentials_path).st_mode), 0o600)
            with open(credentials_path, encoding="utf-8") as credentials_file:
                self.assertEqual(
                    json.load(credentials_file),
                    {"device_id": "device-01", "device_token": "device-secret"},
                )

    def test_reads_legacy_device_token(self):
        with tempfile.TemporaryDirectory() as directory:
            token_path = os.path.join(directory, "device_token")
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write("legacy-secret\n")

            with (
                patch("agent.config.DEVICE_TOKEN", ""),
                patch(
                    "agent.config.DEVICE_CREDENTIALS_PATH",
                    os.path.join(directory, "credentials.json"),
                ),
                patch("agent.config.LEGACY_DEVICE_TOKEN_PATH", token_path),
            ):
                self.assertEqual(
                    config.load_device_credentials(),
                    {"device_id": None, "device_token": "legacy-secret"},
                )
            self.assertEqual(stat.S_IMODE(os.stat(token_path).st_mode), 0o600)

    def test_persists_stable_installation_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "installation_id")
            with (
                patch("agent.config.FRIDAY_HOME", directory),
                patch("agent.config.INSTALLATION_ID_PATH", path),
            ):
                first_id = config.get_installation_id()
                second_id = config.get_installation_id()
            self.assertEqual(first_id, second_id)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_rejects_invalid_saved_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            credentials_path = os.path.join(directory, "credentials.json")
            with open(credentials_path, "w", encoding="utf-8") as credentials_file:
                json.dump({"device_token": ""}, credentials_file)

            with (
                patch("agent.config.DEVICE_TOKEN", ""),
                patch("agent.config.DEVICE_CREDENTIALS_PATH", credentials_path),
            ):
                with self.assertRaisesRegex(ValueError, "no device token"):
                    config.load_device_credentials()


if __name__ == "__main__":
    unittest.main()
