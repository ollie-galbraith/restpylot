import os
import logging
import requests
from typing import overload, Optional, Union
from requests.auth import AuthBase

class RestClient():

    @overload
    def __init__(self, base_url: Optional[str] = None, headers: Optional[dict] = None,
                 auth_token: str = ..., auth_token_type: str = 'Bearer',
                 api_key: None = None, api_key_type: str = 'APIKey',
                 auth: None = None,
                 timeout: int = 10, debug: bool = False): ...

    @overload
    def __init__(self, base_url: Optional[str] = None, headers: Optional[dict] = None,
                 auth_token: None = None, auth_token_type: str = 'Bearer',
                 api_key: str = ..., api_key_type: str = 'APIKey',
                 auth: None = None,
                 timeout: int = 10, debug: bool = False): ...

    @overload
    def __init__(self, base_url: Optional[str] = None, headers: Optional[dict] = None,
                 auth_token: None = None, auth_token_type: str = 'Bearer',
                 api_key: None = None, api_key_type: str = 'APIKey',
                 auth: dict = ...,
                 timeout: int = 10, debug: bool = False): ...

    def __init__(self, base_url: Optional[str] = None, headers: Optional[dict] = None,
                 auth_token: Optional[str] = None, auth_token_type: str = 'Bearer',
                 api_key: Optional[str] = None, api_key_type: str = 'APIKey',
                 auth: Optional[dict] = None,
                 timeout: int = 10, debug: bool = False):
        """
        Initialize the RestClient for REST API requests.

        :param base_url: Base URL for the API (e.g., "https://api.example.com")
        :param headers: Default headers (optional)
        :param auth_token: Authentication token (optional, for Bearer auth)
        :param timeout: Request timeout (default: 10s)
        """

        self.base_url = base_url.rstrip('/') if base_url else None
        self.session = requests.Session()
        self.session.headers.update(headers or {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        if auth_token:
            self.session.headers.update({'Authorization': f'{auth_token_type} {auth_token}'})

        if api_key:
            self.session.headers.update({api_key_type: api_key})

        if auth:
            if not isinstance(auth, (AuthBase, tuple)):
                raise TypeError(f"auth must be an instance of requests.auth.AuthBase or a tuple, got {type(auth).__name__}")
            self.session.auth = auth

        self.timeout = timeout

        self.logger = logging.getLogger(__name__)
        log_level = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger.debug(f"Initialized RestClient with base URL: {self.base_url}")

    def _request(self, method, endpoint, download_path=None, chunk_size=1024, **kwargs):
        """
        Internal method to make a REST API request.

        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        :param endpoint: API endpoint (e.g., "/users/1")
        :param kwargs: Additional request parameters (params, json, etc.)
        :return: Parsed JSON response or error message
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self.logger.debug(f"Making {method} request to: {url} with kwargs: {kwargs}")

        try:
            response = self.session.request(method, url, timeout=self.timeout, stream=True, **kwargs)
            response.raise_for_status()  # Raises HTTPError for 4xx, 5xx responses

            if download_path is not None:
                output_dir = os.path.dirname(download_path)
                os.makedirs(output_dir, exist_ok=True)

                with open(download_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # Filter out keep-alive new chunks
                            file.write(chunk)
                logging.debug(f"Downloaded file to {download_path}")
                return download_path

            # Try to parse JSON response
            logging.debug(f"Response Status: {response.status_code}")
            if response.content:
                return response.json()

        except requests.exceptions.HTTPError as e:
            # Extract detailed error message from response if available
            error_details = None
            try:
                error_details = response.json()  # Attempt to parse JSON error message
            except ValueError:
                error_details = response.text  # If not JSON, return raw text

            self.logger.error(f"HTTPError {response.status_code} for {method} {url}: {error_details}")
            raise requests.exceptions.HTTPError({
                "status_code": response.status_code,
                "message": error_details,
                "url": url
            })

        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out: {method} {url}")
            raise requests.exceptions.Timeout(f'Request to {url} timed out')
            #return {"error": "Timeout", "message": f"Request to {url} timed out."}

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {method} {url} - {e}")
            raise requests.exceptions.ConnectionError(str(e))
            #return {"error": "Connection Error", "message": str(e)}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Unexpected error: {method} {url} - {e}")
            raise requests.exceptions.RequestException(str(e))
            #return {"error": "Request Exception", "message": str(e)}

    def get(self, endpoint, params=None, download_path=None):
        """Perform a GET request (used for retrieving data)."""
        return self._request("GET", endpoint, params=params, download_path=download_path)

    def post(self, endpoint, json=None):
        """Perform a POST request (used for creating resources)."""
        return self._request("POST", endpoint, json=json)

    def put(self, endpoint, json=None):
        """Perform a PUT request (used for updating resources)."""
        return self._request("PUT", endpoint, json=json)

    def patch(self, endpoint, json=None):
        """Perform a PATCH request (used for partial updates)."""
        return self._request("PATCH", endpoint, json=json)

    def delete(self, endpoint):
        """Perform a DELETE request (used for deleting resources)."""
        return self._request("DELETE", endpoint)

    def set_apikey_header(self, api_key, api_key_type='APIKey'):
        """Update APIKey header"""
        self.session.headers.update({api_key_type: api_key})
        self.logger.debug("API Key set successfully")

    def set_auth_token(self, auth_token, auth_token_type='Bearer'):
        """Update authentication token."""
        self.logger.debug(f"Auth Token '{auth_token_type}' added to session")
        self.session.headers.update({"Authorization": f"{auth_token_type} {auth_token}"})

    def set_auth(self, auth):
        """Update authentication method"""
        if not isinstance(auth, (AuthBase, tuple)):
            raise TypeError(f"auth must be an instance of requests.auth.AuthBase or a tuple, got {type(auth).__name__}")
        self.logger.debug(f"Authentication added to session")
        self.session.auth = auth

    def close(self):
        """Close the session."""
        self.session.close()
        self.logger.debug("Closing session")