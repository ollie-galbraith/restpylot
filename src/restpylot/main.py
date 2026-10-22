import logging
import os
import requests
import tempfile
import time

from typing import overload, Optional
from http.cookiejar import MozillaCookieJar
from platformdirs import user_cache_dir
from pathlib import Path
from urllib.parse import urlsplit


class RestClient():
    @overload
    def __init__(auth_token: str, api_key: None = None, auth: None = None) -> None:
        ...

    @overload
    def __init__(api_key: str, auth_token: None = None, auth: None = None) -> None:
        ...

    @overload
    def __init__(auth: dict, auth_token: None = None, api_key: None = None) -> None:
        ...

    def __init__(
        self, base_url: str, headers: dict = None,
        auth_token: str = None, auth_token_type: str = 'Bearer',
        api_key: str = None, api_key_type: str = 'APIKey',
        auth=None, app_name: str = 'rest_client',
        validate_certs: bool = True, timeout: int = 10, debug: bool = False
    ) -> None:
        """
        Initialize the RestClient for REST API requests.

        :param base_url: Base URL for the API (e.g., "https://api.example.com")
        :param headers: Default headers (optional)
        :param auth_token: Authentication token (optional, for Bearer auth)
        :param auth_token_type: Type of the authentication token
        :param api_key: API key value (optional)
        :param api_key_type: Header name for the API key
        :param auth: Authentication credentials (optional, can be a requests.auth.AuthBase instance or a tuple for basic auth)
        :param validate_certs: Validate SSL certificates or not
        :param timeout: Request timeout (default: 10s)
        :param debug: Enable debug logging (default: False)
        """

        self.base_url = base_url.rstrip('/') if base_url else None

        self.logger = logging.getLogger(__name__)
        self.log_level = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(level=self.log_level, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger.debug(f"Initialized RestClient with base URL: {self.base_url}")

        self.session = requests.Session()

        if validate_certs is False:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.session.verify = validate_certs

        self.session.headers.update(headers or {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain'
        })

        # Initialise cookie storage
        self.cookie_dir = Path(user_cache_dir(app_name))
        self.cookie_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == 'posix':
            self.cookie_dir.chmod(0o700)
        self.cookie_file = self.cookie_dir / "cookies.txt"

        # Attach cookie jar
        self.session.cookies = MozillaCookieJar(str(self.cookie_file))

        if auth_token:
            self.session.headers.update({'Authorization': f'{auth_token_type} {auth_token}'})

        if api_key:
            self.session.headers.update({api_key_type: api_key})

        if auth:
            if not isinstance(auth, (requests.auth.AuthBase, tuple)):
                raise TypeError(f"auth must be an instance of requests.auth.AuthBase or a tuple, got {type(auth).__name__}")
            self.session.auth = auth

        self.timeout = timeout

    @property
    def get_headers(self, header: Optional[str] = None):
        if header is not None:
            return self.session.headers.get(header)
        return self.session.headers

    def _request(self, method: str, endpoint: str, download_path: str = None, chunk_size: int = 1024, **kwargs) -> Optional[object]:
        """
        Internal method to make a REST API request.

        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        :param endpoint: API endpoint (e.g., "/users/1")
        :param download_path: If provided, saves response content to this file path
        :param chunk_size: Size of chunks to use when downloading files (default: 102
        :param kwargs: Additional request parameters (params, json, etc.)
        :return: Parsed JSON response or error message
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self.logger.debug(f"Making {method} request to: {url} with kwargs: {kwargs}")

        try:
            with self.session.request(method, url, timeout=self.timeout, stream=True, **kwargs) as response:
                try:
                    response.raise_for_status()  # Raises HTTPError for 4xx, 5xx responses
                except requests.exceptions.HTTPError as exc:
                    error_response = exc.response
                    if error_response is not None:
                        try:
                            error_details = error_response.json()
                        except ValueError:
                            error_details = error_response.text

                        self.logger.error(
                            f"HTTPError {error_response.status_code} for {method} {url}: {error_details}"
                        )
                    else:
                        self.logger.error(f"HTTPError for {method} {url}: {exc}")
                    raise

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

        except requests.exceptions.HTTPError:
            raise

        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out: {method} {url}")
            raise requests.exceptions.Timeout(f'Request to {url} timed out')

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {method} {url} - {e}")
            raise requests.exceptions.ConnectionError(str(e))

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Unexpected error: {method} {url} - {e}")
            raise requests.exceptions.RequestException(str(e))

    def get(self, endpoint: str, params: dict = None, download_path: str = None,
            headers: dict = None) -> Optional[object]:
        """
        Perform a GET request (used for retrieving data).

        :param endpoint: API endpoint (e.g., "/users/1")
        :param params: Query parameters (optional)
        :param download_path: If provided, saves response content to this file path (for file downloads)
        :param headers: If provided, sets the headers for this specific request, instead of session headers
        :return: Parsed JSON response or path to downloaded file
        """
        kwargs = {}
        if headers is not None:
            kwargs['headers'] = headers

        return self._request("GET", endpoint, params=params, download_path=download_path, **kwargs)

    def post(self, endpoint: str, json: dict = None, data: dict = None,
             headers: dict = None) -> Optional[object]:
        """
        Perform a POST request (used for creating resources).

        :param endpoint: API endpoint (e.g., "/users")
        :param json: JSON data for the request body
        :param data: x-www-form-urlencoded data for the request body
        :param headers: If provided, sets the headers for this specific request, instead of session headers
        :return: Parsed JSON response
        """

        if json is not None and data is not None:
            raise Exception("Unable to define both 'json' and 'data' blocks for a single request")

        kwargs = {}
        if json is not None:
            kwargs['json'] = json
        if data is not None:
            kwargs['data'] = data
        if headers is not None:
            kwargs['headers'] = headers

        return self._request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, json: dict = None, data: dict = None,
            headers: dict = None) -> Optional[object]:
        """
        Perform a PUT request (used for updating resources).

        :param endpoint: API endpoint (e.g., "/users/1")
        :param json: JSON data for the request body
        :param data: x-www-form-urlencoded data for the request body
        :param headers: If provided, sets the headers for this specific request, instead of session headers
        :return: Parsed JSON response
        """

        if json is not None and data is not None:
            raise Exception("Unable to define both 'json' and 'data' blocks for a single request")

        kwargs = {}
        if json is not None:
            kwargs['json'] = json
        if data is not None:
            kwargs['data'] = data
        if headers is not None:
            kwargs['headers'] = headers

        return self._request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, json: dict = None, data: dict = None,
              headers: dict = None) -> Optional[object]:
        """
        Perform a PATCH request (used for partial updates).

        :param endpoint: API endpoint (e.g., "/users/1")
        :param json: JSON data for the request body
        :param data: x-www-form-urlencoded data for the request body
        :param headers: If provided, sets the headers for this specific request, instead of session headers
        :return: Parsed JSON response
        """

        if json is not None and data is not None:
            raise Exception("Unable to define both 'json' and 'data' blocks for a single request")

        kwargs = {}
        if json is not None:
            kwargs['json'] = json
        if data is not None:
            kwargs['data'] = data
        if headers is not None:
            kwargs['headers'] = headers

        return self._request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, headers: dict = None) -> Optional[object]:
        """
        Perform a DELETE request (used for deleting resources).

        :param endpoint: API endpoint (e.g., "/users/1")
        :param headers: If provided, sets the headers for this specific request, instead of session headers
        :return: Parsed JSON response
        """
        if headers is not None:
            return self._request("DELETE", endpoint, headers=headers)
        return self._request("DELETE", endpoint)

    def save_cookies(self) -> None:
        """Save current session cookies to disk."""
        fd, temp_name = tempfile.mkstemp(
            prefix=".cookies-", suffix=".tmp", dir=self.cookie_dir
        )
        temp_path = Path(temp_name)
        try:
            os.close(fd)
            temp_jar = MozillaCookieJar(str(temp_path))
            for cookie in self.session.cookies:
                temp_jar.set_cookie(cookie)
            temp_jar.save(ignore_discard=True, ignore_expires=False)
            if os.name == 'posix':
                temp_path.chmod(0o600)
            os.replace(temp_path, self.cookie_file)
            self.logger.debug(f"Cookies saved to {self.cookie_file}")
        except Exception:
            self.logger.exception("Failed to save cookies")
            raise
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    def load_cookies(self) -> None:
        """Load cookies from disk into the session."""
        if self.cookie_file.exists():
            try:
                self.session.cookies.load(ignore_discard=True, ignore_expires=False)
                self.logger.debug(f"Cookies loaded from {self.cookie_file}")
            except Exception:
                self.logger.exception("Failed to load cookies")
                raise
        else:
            self.logger.debug(f"No cookie file found at {self.cookie_file}")

    def format_cookie(
        self, name: str, value: str, ttl: Optional[int] = None,
        domain: str = None, path: str = '/', secure: Optional[bool] = None
    ):
        """Create a cookie object suitable for the session cookie jar.

        :param name: Cookie name
        :param value: Cookie value
        :param ttl: Cookie lifetime in seconds; None creates a session cookie
        :param domain: Cookie domain; defaults to the base URL's host only
        :param path: Request path the cookie applies to
        :param secure: Restrict transmission to HTTPS; defaults from the base URL
        """
        name_chars = "!#$%&'*+-.^_`|~"
        if not isinstance(name, str) or not name or any(
            not (char.isascii() and (char.isalnum() or char in name_chars))
            for char in name
        ):
            raise ValueError("Cookie name contains invalid characters")
        if not isinstance(value, str) or any(
            not value_char.isascii()
            or not (
                ord(value_char) == 0x21
                or 0x23 <= ord(value_char) <= 0x2B
                or 0x2D <= ord(value_char) <= 0x3A
                or 0x3C <= ord(value_char) <= 0x5B
                or 0x5D <= ord(value_char) <= 0x7E
            )
            for value_char in value
        ):
            raise ValueError("Cookie value contains characters not permitted by the cookie format")
        if ttl is not None:
            if not isinstance(ttl, int) or isinstance(ttl, bool):
                raise TypeError("ttl must be an integer number of seconds or None")
            if ttl <= 0:
                raise ValueError("ttl must be greater than zero")

        base_url = urlsplit(self.base_url or '')
        cookie_domain = domain or base_url.hostname
        if not cookie_domain:
            raise ValueError("A cookie domain is required when base_url has no hostname")
        if not isinstance(cookie_domain, str) or any(
            not char.isascii() or ord(char) < 0x21 or ord(char) == 0x7f
            for char in cookie_domain
        ):
            raise ValueError("Cookie domain contains invalid characters")
        if not isinstance(path, str) or not path.startswith('/') or any(
            not char.isascii() or ord(char) < 0x20 or ord(char) == 0x7f
            for char in path
        ):
            raise ValueError("Cookie path must be an absolute path without control characters")
        if secure is not None and not isinstance(secure, bool):
            raise TypeError("secure must be a bool or None")
        if secure is None:
            secure = base_url.scheme.lower() == 'https'

        cookie = requests.cookies.create_cookie(
            name=name,
            value=value,
            domain=cookie_domain,
            path=path,
            secure=secure,
            expires=int(time.time()) + ttl if ttl is not None else None,
        )
        return cookie

    def set_cookie(
        self, name: str, value: str, ttl: Optional[int] = None,
        domain: str = None, path: str = '/', secure: Optional[bool] = None
    ) -> None:
        """Add a cookie to the session, optionally with a TTL."""
        self.session.cookies.set_cookie(
            self.format_cookie(name, value, ttl, domain, path, secure)
        )

    def has_valid_cookies(self, domain: str = None) -> bool:
        now = time.time()
        requested_domain = domain.lstrip('.').rstrip('.').lower() if domain else None
        for cookie in self.session.cookies:
            cookie_domain = cookie.domain.lstrip('.').rstrip('.').lower()
            if requested_domain and not (
                cookie_domain == requested_domain
                or cookie_domain.endswith(f".{requested_domain}")
            ):
                continue
            if cookie.expires is None or cookie.expires > now:
                return True
        return False

    def set_apikey_header(self, api_key: str, api_key_type: str = 'APIKey') -> None:
        """
        Update APIKey header

        :param api_key: API key value
        :param api_key_type: Header name for the API key (default: 'APIKey')
        """
        self.update_headers({api_key_type: api_key})
        self.logger.debug("API Key set successfully")

    def set_auth_token(self, auth_token: str, auth_token_type: str = 'Bearer') -> None:
        """
        Update authentication token.

        :param auth_token: Authentication token value
        :param auth_token_type: Type of the authentication token (default: 'Bearer')
        """
        self.logger.debug(f"Auth Token '{auth_token_type}' added to session")
        self.update_headers({"Authorization": f"{auth_token_type} {auth_token}"})

    def set_auth(self, auth: dict) -> None:
        """
        Update authentication method

        :param auth: Authentication credentials
        """
        if not isinstance(auth, (requests.auth.AuthBase, tuple)):
            raise TypeError(f"auth must be an instance of requests.auth.AuthBase or a tuple, got {type(auth).__name__}")
        self.logger.debug("Authentication added to session")
        self.session.auth = auth

    def clear_headers(self) -> None:
        """
        Remove all headers from current session
        """
        self.session.headers.clear()

    def set_headers(self, headers: dict) -> None:
        """
        Replaces all current headers in the session with defined headers

        :param headers: Headers to set
        """
        self.clear_headers()
        self.session.headers.update(headers)

    def remove_headers(self, headers: dict) -> None:
        """
        Removes headers from current session matching keys supplied in `headers` parameter

        :param headers: Headers to remove
        """
        for header in headers:
            self.session.headers.pop(header, None)

    def update_headers(self, headers: dict) -> None:
        """
        Update current sessions headers

        :param headers: Headers to update
        """
        self.session.headers.update(headers)

    def close(self) -> None:
        """Close the session."""
        self.session.close()
        self.logger.debug("Closing session")

    def __enter__(self) -> "RestClient":
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()
