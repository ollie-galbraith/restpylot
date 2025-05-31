# restpylot Module

This module provides a `RestClient` class for making HTTP requests with ease. It is built on top of the `requests` library and provides methods for common HTTP operations such as GET, POST, PUT, DELETE, and PATCH.

## Features

- Supports GET, POST, PUT, DELETE, and PATCH requests.
- Allows setting custom headers, including Authorization tokens and API keys.
- Configurable timeout for requests.
- Debug logging for request and response details.
- Handles common HTTP errors and exceptions.

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
