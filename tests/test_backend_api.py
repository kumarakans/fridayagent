import unittest
from unittest.mock import patch

from services.backend_api import BackendAPI


class BackendAPITests(unittest.TestCase):
    @patch("services.backend_api.httpx.post")
    def test_login_uses_email_password_and_returns_access_token(self, post):
        post.return_value.json.return_value = {
            "access_token": "user-access-token",
            "token_type": "bearer",
        }
        api = BackendAPI("https://api.example.test")

        token = api.login("person@example.test", "password-value")

        self.assertEqual(token, "user-access-token")
        post.assert_called_once_with(
            "https://api.example.test/api/v1/auth/login",
            json={"email": "person@example.test", "password": "password-value"},
            headers={},
            timeout=30.0,
        )
        post.return_value.raise_for_status.assert_called_once_with()

    @patch("services.backend_api.httpx.post")
    def test_create_account_uses_registration_route(self, post):
        post.return_value.json.return_value = {"access_token": "new-user-token"}
        api = BackendAPI("https://api.example.test")

        self.assertEqual(api.create_account("new@example.test", "password"), "new-user-token")

        self.assertEqual(
            post.call_args.args[0],
            "https://api.example.test/api/v1/auth/register",
        )

    @patch("services.backend_api.httpx.post")
    def test_registers_device_with_user_token_and_persists_response(self, post):
        post.return_value.json.return_value = {
            "device_id": "device-01",
            "device_token": "device-secret",
        }
        api = BackendAPI("https://api.example.test")

        result = api.register_device(
            "user-access-token",
            "install-uuid",
            "test-pc",
            "0.1.0",
        )

        self.assertEqual(result, {"device_id": "device-01", "device_token": "device-secret"})
        post.assert_called_once_with(
            "https://api.example.test/api/v1/agent/devices/register",
            json={
                "installation_id": "install-uuid",
                "device_name": "test-pc",
                "agent_version": "0.1.0",
            },
            headers={"Authorization": "Bearer user-access-token"},
            timeout=30.0,
        )

    @patch("services.backend_api.httpx.post")
    def test_rejects_auth_response_without_access_token(self, post):
        post.return_value.json.return_value = {}
        api = BackendAPI("https://api.example.test")

        with self.assertRaisesRegex(ValueError, "no access_token"):
            api.login("person@example.test", "password")


if __name__ == "__main__":
    unittest.main()
