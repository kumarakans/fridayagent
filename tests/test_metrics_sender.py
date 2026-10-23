import unittest
from unittest.mock import patch

import httpx

from services.metrics_sender import MetricsSender


class MetricsSenderTests(unittest.TestCase):
    def test_requires_endpoint_and_device_token(self):
        with self.assertRaises(ValueError):
            MetricsSender("", "token")
        with self.assertRaises(ValueError):
            MetricsSender("https://example.test/metrics", "")

    @patch("services.metrics_sender.httpx.post")
    def test_posts_metrics_with_device_bearer_token_and_timeout(self, post):
        sender = MetricsSender("https://example.test/metrics", "device-secret")
        metrics = {"cpu_percent": 12.5}
        response = post.return_value
        response.status_code = 202

        sender.send(metrics)

        post.assert_called_once_with(
            "https://example.test/metrics",
            json=metrics,
            headers={"Authorization": "Bearer device-secret"},
            timeout=20.0,
        )
        response.raise_for_status.assert_called_once_with()

    @patch("services.metrics_sender.httpx.post")
    def test_rejects_unsuccessful_response(self, post):
        sender = MetricsSender("https://example.test/metrics", "device-secret")
        post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "failed",
            request=httpx.Request("POST", "https://example.test/metrics"),
            response=httpx.Response(503),
        )

        with self.assertRaises(httpx.HTTPStatusError):
            sender.send({"cpu_percent": 12.5})

    @patch("services.metrics_sender.httpx.post")
    def test_requires_accepted_response_status(self, post):
        sender = MetricsSender("https://example.test/metrics", "device-secret")
        response = post.return_value
        response.status_code = 200
        response.request = httpx.Request("POST", "https://example.test/metrics")

        with self.assertRaises(httpx.HTTPStatusError):
            sender.send({"cpu_percent": 12.5})


if __name__ == "__main__":
    unittest.main()
