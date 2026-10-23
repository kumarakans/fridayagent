import unittest
from unittest.mock import patch

from agent.main import enroll_device


class EnrollmentFlowTests(unittest.TestCase):
    @patch("agent.main.save_device_credentials")
    @patch("agent.main.platform.node", return_value="test-pc")
    @patch("agent.main.get_installation_id", return_value="stable-install-id")
    @patch("agent.main.BackendAPI")
    @patch("agent.main.getpass.getpass", return_value="website-password")
    @patch("builtins.input", side_effect=["1", "new@example.test"])
    def test_signup_then_registers_and_saves_device(
        self, _input, _password, backend_api, _installation_id, _node, save_credentials
    ):
        api = backend_api.return_value
        api.create_account.return_value = "temporary-user-access-token"
        api.register_device.return_value = {
            "device_id": "device-01",
            "device_token": "device-secret",
        }
        config = {
            "api_base_url": "https://api.example.test",
            "agent_version": "0.1.0",
        }

        device = enroll_device(config)

        api.create_account.assert_called_once_with("new@example.test", "website-password")
        api.register_device.assert_called_once_with(
            access_token="temporary-user-access-token",
            installation_id="stable-install-id",
            device_name="test-pc",
            agent_version="0.1.0",
        )
        save_credentials.assert_called_once_with("device-01", "device-secret")
        self.assertEqual(device["device_id"], "device-01")

    @patch("builtins.print")
    @patch("agent.main.BackendAPI")
    @patch("agent.main.getpass.getpass", return_value="too-short")
    @patch("builtins.input", side_effect=["1", "new@example.test"])
    def test_signup_explains_password_rule_and_rejects_short_password(
        self, _input, _password, backend_api, print_message
    ):
        with self.assertRaisesRegex(ValueError, "between 12 and 256 characters"):
            enroll_device({"api_base_url": "https://api.example.test"})

        backend_api.return_value.create_account.assert_not_called()
        printed = " ".join(call.args[0] for call in print_message.call_args_list)
        self.assertIn("12 to 256 characters", printed)
        self.assertIn("input is hidden", printed)

    @patch("builtins.print")
    @patch("agent.main.BackendAPI")
    @patch("agent.main.getpass.getpass", return_value="long-enough-password")
    @patch("builtins.input", side_effect=["1", "new@example.test"])
    def test_signup_422_shows_actionable_guidance_without_echoing_input(
        self, _input, _password, backend_api, print_message
    ):
        import httpx

        response = httpx.Response(
            422,
            request=httpx.Request("POST", "https://api.example.test/api/v1/auth/register"),
        )
        backend_api.return_value.create_account.side_effect = httpx.HTTPStatusError(
            "unprocessable entity",
            request=response.request,
            response=response,
        )

        with self.assertRaises(httpx.HTTPStatusError):
            enroll_device({"api_base_url": "https://api.example.test"})

        printed = " ".join(call.args[0] for call in print_message.call_args_list)
        self.assertIn("API rejected the signup details", printed)
        self.assertIn("choose sign in", printed)

    @patch("agent.main.BackendAPI")
    @patch("builtins.input", side_effect=["1", "invalid-email"])
    def test_signup_rejects_invalid_email_before_password_prompt(
        self, _input, backend_api
    ):
        with self.assertRaisesRegex(ValueError, "valid email address"):
            enroll_device({"api_base_url": "https://api.example.test"})

        backend_api.return_value.create_account.assert_not_called()

    @patch("agent.main.save_device_credentials")
    @patch("agent.main.platform.node", return_value="existing-pc")
    @patch("agent.main.get_installation_id", return_value="stable-install-id")
    @patch("agent.main.BackendAPI")
    @patch("agent.main.getpass.getpass", return_value="existing-password")
    @patch("builtins.input", side_effect=["2", "person@example.test"])
    def test_login_then_registers_existing_computer(
        self, _input, _password, backend_api, _installation_id, _node, _save_credentials
    ):
        api = backend_api.return_value
        api.login.return_value = "temporary-user-access-token"
        api.register_device.return_value = {
            "device_id": "device-02",
            "device_token": "device-secret",
        }

        enroll_device(
            {"api_base_url": "https://api.example.test", "agent_version": "0.1.0"}
        )

        api.login.assert_called_once_with("person@example.test", "existing-password")
        api.create_account.assert_not_called()


if __name__ == "__main__":
    unittest.main()
