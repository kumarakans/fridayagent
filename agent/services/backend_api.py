import httpx


class BackendAPI:
    def __init__(self, api_base_url, timeout=30.0):
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path, payload, access_token=None):
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        response = httpx.post(
            f"{self.api_base_url}{path}",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError(f"The API returned an invalid response for {path}")
        return result

    def create_account(self, email, password):
        result = self._post(
            "/api/v1/auth/register",
            {"email": email, "password": password},
        )
        return self._access_token(result)

    def login(self, email, password):
        result = self._post(
            "/api/v1/auth/login",
            {"email": email, "password": password},
        )
        return self._access_token(result)

    @staticmethod
    def _access_token(result):
        access_token = result.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("The authentication API response has no access_token")
        return access_token.strip()

    def register_device(self, access_token, installation_id, device_name, agent_version):
        result = self._post(
            "/api/v1/agent/devices/register",
            {
                "installation_id": installation_id,
                "device_name": device_name,
                "agent_version": agent_version,
            },
            access_token=access_token,
        )
        device_id = result.get("device_id")
        device_token = result.get("device_token")
        if not isinstance(device_id, str) or not device_id.strip():
            raise ValueError("The device-registration API response has no device_id")
        if not isinstance(device_token, str) or not device_token.strip():
            raise ValueError("The device-registration API response has no device_token")
        return {"device_id": device_id.strip(), "device_token": device_token.strip()}
