# restpylot Module

[![Python package](https://github.com/ollie-galbraith/restpylot/actions/workflows/python-package.yml/badge.svg)](https://github.com/ollie-galbraith/restpylot/actions/workflows/python-package.yml)

A lightweight, flexible REST API client built on the `requests` library. The `RestClient` class simplifies HTTP interactions with persistent session management for connection pooling, support for multiple authentication strategies, file operations, and comprehensive error handling—all wrapped in an intuitive, easy-to-use interface.

## Features

- **HTTP Methods**: Supports GET, POST, PUT, DELETE, and PATCH requests.
- **Multiple Authentication Methods**: Bearer token authentication, API key headers, and custom authentication (including HTTP Basic Auth via requests.auth.AuthBase).
- **Dynamic Authentication Updates**: Set or update authentication credentials at runtime without reinitializing the client.
- **File Downloads**: Stream and save file responses directly to disk with configurable chunk sizes.
- **Response Cleanup**: Close each response after processing, including streamed downloads; use the client as a context manager to close its session automatically.
- **Session Management**: Leverages persistent HTTP sessions for connection pooling and performance optimization.
- **Custom Headers**: Set session-wide defaults or provide headers for an individual request without changing session defaults.
- **Configurable Timeout**: Set request timeouts to handle slow or unresponsive APIs.
- **Comprehensive Error Handling**: Graceful exception handling with detailed logging for HTTP errors, timeouts, and connection issues.
- **Debug Logging**: Optional detailed logging for troubleshooting API interactions and request/response inspection.

## Installation

To use the `restpylot` module:

```bash
pip install restpylot
```

## Usage

### Initialization

You can initialize the `restpylot` with a base URL, headers, authorization token, timeout, and debug mode.

```python
from restpylot import RestClient

client = RestClient(
    base_url='https://api.example.com',
    headers={'Custom-Header': 'value'},
    auth_token='your_auth_token',
    timeout=10,
    debug=True
)
```

### Making Requests

The `restpylot` provides methods for making various types of HTTP requests.

#### GET Request

```python
response = client.get('/endpoint', params={'key': 'value'})
print(response)
```

All request methods accept an optional `headers` argument. These headers apply only to that request, override matching session headers, and leave other session defaults in place.

```python
response = client.get('/endpoint', headers={'X-Request-ID': 'one-off'})
```

#### POST Request

```python
response = client.post('/endpoint', json={'key': 'value'})
print(response)
```

Use `data` instead of `json` to send form-encoded data. A request cannot specify both.

```python
response = client.post('/endpoint', data={'key': 'value'})
```

#### PUT Request

```python
response = client.put('/endpoint', json={'key': 'value'})
print(response)
```

#### DELETE Request

```python
response = client.delete('/endpoint')
print(response)
```

#### PATCH Request

```python
response = client.patch('/endpoint', json={'key': 'value'})
print(response)
```

### Setting Authorization Token

You can update the authorization token at any time.

```python
client.set_auth_token('new_auth_token')
```

### Setting API Key

You can set an API key with a custom header.

```python
client.set_apikey_header('your_api_key', api_key_type='X-Api-Key')
```

### Session Cleanup

Use the client as a context manager to close the session automatically when the block exits, including when an exception is raised.

```python
with RestClient(base_url='https://api.example.com') as client:
    response = client.get('/endpoint')
```

You can also close the session explicitly:

```python
client.close()
```

### Cookie Persistence

Cookies are not loaded automatically. Load them only for workflows that need them, then save them explicitly when you want to persist the session. Cookie files are stored in the platform's user cache directory. You can also add application-provided tokens to the jar with a TTL; the default cookie domain is the host in `base_url`, and requests sends domain cookies to its subdomains as well. Pass `domain` explicitly to control the cookie's domain scope.

```python
client.load_cookies()
client.set_cookie('access_token', 'token-value', ttl=3600)
response = client.get('/endpoint')
client.save_cookies()
```

`format_cookie()` creates a cookie object without adding it to the session; `set_cookie()` creates and adds it. Cookie names and values must follow cookie syntax. Closing the client does not save cookies automatically. Cookie load and save errors are raised to the caller.

## Logging

If debug mode is enabled, the `restpylot` will log detailed information about the requests and responses.

## License

This module is provided under the GPL-3.0 License.
