import httpx

from agent.config import API_BASE_URL


class ServerConnection:
    def __init__(self, server_url=API_BASE_URL):
        self.server_url = server_url.rstrip("/")
        self.connected = False

    def check_connection(self):
        """
        Check whether the FRIDAY server is reachable.
        """

        try:
            response = httpx.get(
                f"{self.server_url}/",
                timeout=5.0
            )

            if response.status_code < 500:
                self.connected = True
                return True

            self.connected = False
            return False

        except httpx.RequestError:
            self.connected = False
            return False

    def get_status(self):
        """
        Return the current connection status.
        """

        return {
            "server_url": self.server_url,
            "connected": self.connected,
        }