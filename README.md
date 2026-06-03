# restpylot Module

[![Python package](https://github.com/ollie-galbraith/restpylot/actions/workflows/python-package.yml/badge.svg)](https://github.com/ollie-galbraith/restpylot/actions/workflows/python-package.yml)

A lightweight, flexible REST API client built on the `requests` library. The `RestClient` class simplifies HTTP interactions with persistent session management for connection pooling, support for multiple authentication strategies, file operations, and comprehensive error handling—all wrapped in an intuitive, easy-to-use interface.

## Features

- **HTTP Methods**: Supports GET, POST, PUT, DELETE, and PATCH requests.
- **Multiple Authentication Methods**: Bearer token authentication, API key headers, and custom authentication (including HTTP Basic Auth via requests.auth.AuthBase).
- **Dynamic Authentication Updates**: Set or update authentication credentials at runtime without reinitializing the client.
- **File Downloads**: Stream and save file responses directly to disk with configurable chunk sizes.
- **Session Management**: Leverages persistent HTTP sessions for connection pooling and performance optimization.
- **Custom Headers**: Easily set default headers and customize them per request.
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

#### POST Request

```python
response = client.post('/endpoint', json={'key': 'value'})
print(response)
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
client.set_api_key('your_api_key', header='X-Api-Key')
```

### Closing the Session

It is a good practice to close the session when you are done with the client.

```python
client.close()
```

## Logging

If debug mode is enabled, the `restpylot` will log detailed information about the requests and responses.

## License

This module is provided under the GPL-3.0 License.
