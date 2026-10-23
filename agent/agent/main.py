import getpass
import logging
import platform
import re
import time

import httpx

from agent.config import (
    create_directories,
    get_config,
    get_installation_id,
    load_device_credentials,
    save_device_credentials,
)
from services.backend_api import BackendAPI
from monitoring.system import get_system_status
from services.metrics_sender import MetricsSender


logger = logging.getLogger("friday-agent")


def enroll_device(config):
    api = BackendAPI(config["api_base_url"])
    print("\nThis computer is not registered with FRIDAY.")
    print("1. Create a new website account")
    print("2. Sign in with an existing website account")
    choice = input("Choose 1 or 2: ").strip()
    if choice not in {"1", "2"}:
        raise ValueError("Invalid choice. Enter 1 to create an account or 2 to sign in.")

    if choice == "1":
        print("\nCreate your FRIDAY website account")
        print("  - Enter a valid email address, for example name@example.com.")
        print("  - Password must be 12 to 256 characters long.")
        print("  - Password input is hidden and will not be saved by the agent.")
        print("  - If you already have an account, go back and choose 2 to sign in.")
    else:
        print("\nSign in with your existing FRIDAY website account.")

    email = input("Email address: ").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Enter a valid email address, such as name@example.com.")
    password = getpass.getpass("Password (input is hidden): ")
    if not password:
        raise ValueError("Password cannot be empty.")
    if choice == "1" and not 12 <= len(password) <= 256:
        raise ValueError(
            "Account password must be between 12 and 256 characters. "
            "No request was sent; run the agent again and try again."
        )

    if choice == "1":
        try:
            access_token = api.create_account(email, password)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 422:
                print(
                    "\nThe API rejected the signup details. Check that the email "
                    "is valid and the password is 12 to 256 characters, then try "
                    "again. If this email already has an account, choose sign in."
                )
            raise
    else:
        access_token = api.login(email, password)

    installation_id = get_installation_id()
    device = api.register_device(
        access_token=access_token,
        installation_id=installation_id,
        device_name=platform.node() or "FRIDAY device",
        agent_version=config["agent_version"],
    )
    save_device_credentials(device["device_id"], device["device_token"])
    logger.info(
        "Computer registered as device %s; device credential saved securely",
        device["device_id"],
    )
    return device


def main():
    create_directories()
    config = get_config()

    try:
        credentials = load_device_credentials()
        if credentials is None:
            credentials = enroll_device(config)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Account or device registration failed (HTTP %s). "
            "See the guidance above and try again.",
            exc.response.status_code,
        )
        raise SystemExit(1) from exc
    except (EOFError, httpx.RequestError, OSError, RuntimeError, ValueError) as exc:
        logger.error("Account or device registration failed: %s", exc)
        raise SystemExit(1) from exc

    sender = MetricsSender(config["metrics_url"], credentials["device_token"])
    logger.info("Device token configured; sending metrics to %s", config["api_base_url"])

    logger.info("%s v%s started", config["app_name"], config["agent_version"])
    while True:
        metrics = get_system_status()
        try:
            sender.send(metrics)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logger.error(
                    "Metrics API rejected this device token (401). Re-register or "
                    "request a replacement token, then remove the saved credentials."
                )
                raise SystemExit(1) from exc
            else:
                logger.warning(
                    "Metrics upload rejected (HTTP %s)", exc.response.status_code
                )
        except httpx.RequestError as exc:
            logger.warning("Metrics upload failed (%s)", type(exc).__name__)
        else:
            logger.info(
                "System metrics accepted: CPU %.1f%%, memory %.1f%%, disk %.1f%%",
                metrics["cpu_percent"], metrics["memory_percent"], metrics["disk_percent"]
            )

        time.sleep(config["heartbeat_interval"])


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        main()
    except KeyboardInterrupt:
        logger.info("FRIDAY Agent stopped")