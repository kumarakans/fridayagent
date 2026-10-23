import httpx


class MetricsSender:
    def __init__(self, metrics_url, device_token, timeout=20.0):
        if not metrics_url:
            raise ValueError("A metrics URL is required to enable metrics upload")
        if not device_token:
            raise ValueError("A device token is required to enable metrics upload")

        self.metrics_url = metrics_url
        self.device_token = device_token
        self.timeout = timeout

    def send(self, metrics):
        response = httpx.post(
            self.metrics_url,
            json=metrics,
            headers={"Authorization": f"Bearer {self.device_token}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        if response.status_code != 202:
            raise httpx.HTTPStatusError(
                "Metrics API did not return HTTP 202 Accepted",
                request=response.request,
                response=response,
            )
