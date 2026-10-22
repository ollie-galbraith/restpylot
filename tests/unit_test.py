import unittest
import sys
import os
import tempfile
import time
from unittest.mock import Mock
from unittest.mock import patch
import requests

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.restpylot.main import RestClient


class TestRestClient(unittest.TestCase):
    def setUp(self):
        self.client = RestClient(base_url="https://jsonplaceholder.typicode.com")

    def test_context_manager_closes_session(self):
        self.client.session.close = Mock()

        with self.client as client:
            self.assertIs(client, self.client)

        self.client.session.close.assert_called_once_with()

    def test_context_manager_closes_session_when_exception_is_raised(self):
        self.client.session.close = Mock()

        with self.assertRaisesRegex(RuntimeError, "request failed"):
            with self.client:
                raise RuntimeError("request failed")

        self.client.session.close.assert_called_once_with()

    def test_update_headers_preserves_other_headers(self):
        self.client.update_headers({"X-Custom": "value"})

        self.assertEqual(self.client.session.headers["X-Custom"], "value")
        self.assertEqual(self.client.session.headers["Accept"], "application/json")

    def test_set_headers_replaces_existing_headers(self):
        self.client.set_headers({"X-Custom": "value"})

        self.assertEqual(dict(self.client.session.headers), {"X-Custom": "value"})

    def test_remove_headers_removes_only_matching_headers(self):
        self.client.update_headers({"X-Remove": "remove", "X-Keep": "keep"})

        self.client.remove_headers({"x-remove": None})

        self.assertNotIn("X-Remove", self.client.session.headers)
        self.assertEqual(self.client.session.headers["X-Keep"], "keep")

    def test_clear_headers_removes_all_headers(self):
        self.client.clear_headers()

        self.assertEqual(len(self.client.session.headers), 0)

    def test_set_apikey_header(self):
        self.client.set_apikey_header("secret", "X-API-Key")

        self.assertEqual(self.client.session.headers["X-API-Key"], "secret")

    def test_set_auth_token(self):
        self.client.set_auth_token("secret", "Token")

        self.assertEqual(self.client.session.headers["Authorization"], "Token secret")

    def test_cookie_save_and_load_uses_private_file(self):
        with tempfile.TemporaryDirectory() as cookie_directory:
            with patch("src.restpylot.main.user_cache_dir", return_value=cookie_directory):
                client = RestClient(base_url="https://example.com")
                client.set_cookie("access_token", "secret-token", ttl=3600)
                cookie = next(iter(client.session.cookies))
                self.assertEqual(cookie.name, "access_token")
                self.assertGreater(cookie.expires, int(time.time()))
                self.assertTrue(cookie.secure)
                client.save_cookies()

                self.assertTrue(client.cookie_file.exists())
                if os.name == "posix":
                    self.assertEqual(client.cookie_file.stat().st_mode & 0o777, 0o600)
                    self.assertEqual(client.cookie_dir.stat().st_mode & 0o777, 0o700)

                restored_client = RestClient(base_url="https://example.com")
                restored_client.load_cookies()
                restored_cookie = next(
                    cookie for cookie in restored_client.session.cookies
                    if cookie.name == "access_token"
                )
                self.assertEqual(restored_cookie.value, "secret-token")

                matching_request = restored_client.session.prepare_request(
                    requests.Request("GET", "https://example.com/resource")
                )
                subdomain_request = restored_client.session.prepare_request(
                    requests.Request("GET", "https://sub.example.com/resource")
                )
                unrelated_request = restored_client.session.prepare_request(
                    requests.Request("GET", "https://other.test/resource")
                )
                self.assertEqual(matching_request.headers["Cookie"], "access_token=secret-token")
                self.assertEqual(subdomain_request.headers["Cookie"], "access_token=secret-token")
                self.assertNotIn("Cookie", unrelated_request.headers)

    def test_format_cookie_rejects_invalid_values_and_ttls(self):
        with self.assertRaises(ValueError):
            self.client.format_cookie("token", "contains spaces")

        with self.assertRaises(ValueError):
            self.client.format_cookie("token", "value", ttl=0)

        with self.assertRaises(TypeError):
            self.client.format_cookie("token", "value", ttl=1.5)

    def test_has_valid_cookies_ignores_expired_cookies_if_valid_ones_exist(self):
        self.client.session.cookies.set_cookie(
            requests.cookies.create_cookie(
                "expired", "old", domain="example.com", expires=int(time.time()) - 10
            )
        )
        self.client.session.cookies.set_cookie(
            requests.cookies.create_cookie(
                "valid", "current", domain="example.com", expires=int(time.time()) + 3600
            )
        )

        self.assertTrue(self.client.has_valid_cookies("example.com"))

    def test_has_valid_cookies_requires_domain_boundary(self):
        self.client.session.cookies.set_cookie(
            requests.cookies.create_cookie("session", "secret", domain="notexample.com")
        )

        self.assertFalse(self.client.has_valid_cookies("example.com"))

    def test_http_methods_accept_per_request_headers(self):
        headers = {"X-Request-ID": "one-off"}
        cases = [
            ("get", "GET", "posts", {"params": None, "download_path": None}),
            ("post", "POST", "posts", {}),
            ("put", "PUT", "posts/1", {}),
            ("patch", "PATCH", "posts/1", {}),
            ("delete", "DELETE", "posts/1", {}),
        ]

        for method_name, http_method, endpoint, kwargs in cases:
            with self.subTest(method=method_name):
                self.client._request = Mock()

                getattr(self.client, method_name)(endpoint, headers=headers)

                self.client._request.assert_called_once_with(
                    http_method, endpoint, headers=headers, **kwargs
                )

    def test_per_request_headers_do_not_mutate_session_headers(self):
        headers = {"X-Request-ID": "one-off"}
        response = requests.Response()
        response.status_code = 200
        response._content = b""
        self.client.session.request = Mock(return_value=response)

        self.client.get("posts", headers=headers)

        self.client.session.request.assert_called_once_with(
            "GET",
            "https://jsonplaceholder.typicode.com/posts",
            timeout=10,
            stream=True,
            params=None,
            headers=headers,
        )
        self.assertNotIn("X-Request-ID", self.client.session.headers)

    def test_post_with_data(self):
        data = {"title": "foo"}
        self.client._request = Mock(return_value={})

        self.client.post("posts", data=data)

        self.client._request.assert_called_once_with("POST", "posts", data=data)

    def test_put_with_data(self):
        data = {"title": "foo"}
        self.client._request = Mock(return_value={})

        self.client.put("posts/1", data=data)

        self.client._request.assert_called_once_with("PUT", "posts/1", data=data)

    def test_patch_with_data(self):
        data = {"title": "foo"}
        self.client._request = Mock(return_value={})

        self.client.patch("posts/1", data=data)

        self.client._request.assert_called_once_with("PATCH", "posts/1", data=data)

    def test_get_posts(self):
        response = self.client.get("posts")
        self.assertIsInstance(response, list)
        self.assertGreater(len(response), 0)
        self.assertIn("userId", response[0])
        self.assertIn("id", response[0])
        self.assertIn("title", response[0])
        self.assertIn("body", response[0])

    def test_get_post(self):
        response = self.client.get("posts/1")
        self.assertIsInstance(response, dict)
        self.assertEqual(response["id"], 1)
        self.assertIn("userId", response)
        self.assertIn("title", response)
        self.assertIn("body", response)

    def test_post_post(self):
        response = self.client.post("posts", json={"title": "foo", "body": "bar", "userId": 1})
        self.assertIsInstance(response, dict)
        self.assertIn("id", response)
        self.assertEqual(response["title"], "foo")
        self.assertEqual(response["body"], "bar")
        self.assertEqual(response["userId"], 1)

    def test_post_post_with_files(self):
        response = self.client.post("posts", json={"title": "foo", "body": "bar", "userId": 1})
        self.assertIsInstance(response, dict)
        self.assertIn("id", response)
        self.assertEqual(response["title"], "foo")
        self.assertEqual(response["body"], "bar")
        self.assertEqual(response["userId"], 1)

    def test_put_post(self):
        response = self.client.put("posts/1", json={"title": "foo", "body": "bar", "userId": 1})
        self.assertIsInstance(response, dict)
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["title"], "foo")
        self.assertEqual(response["body"], "bar")
        self.assertEqual(response["userId"], 1)

    def test_delete_post(self):
        response = self.client.delete("posts/1")
        self.assertEqual(response, {})  # Empty dict returned on successful delete

    def test_patch_post(self):
        response = self.client.patch("posts/1", json={"title": "foo"})
        self.assertIsInstance(response, dict)
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["title"], "foo")
        self.assertIn("userId", response)
        self.assertIn("body", response)

    def test_http_error_preserves_response(self):
        class DummyResponse(object):
            def __init__(self):
                self.status_code = 500
                self._text = '{"error": "bad request"}'
                self._json = {"error": "bad request"}
                self.closed = False
                self.body_read_before_close = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                self.closed = True

            def raise_for_status(self):
                raise requests.exceptions.HTTPError(
                    "boom",
                    response=self,
                    request=requests.Request("GET", "https://example.test/bad").prepare(),
                )

            def json(self):
                if self.closed:
                    raise RuntimeError("response body read after close")
                self.body_read_before_close = True
                return self._json

            @property
            def text(self):
                if self.closed and not self.body_read_before_close:
                    raise RuntimeError("response body read after close")
                return self._text

        response = DummyResponse()
        self.client.session.request = Mock(return_value=response)

        with self.assertRaises(requests.exceptions.HTTPError) as ctx:
            self.client.get("bad")

        self.assertEqual(ctx.exception.response.status_code, 500)
        self.assertEqual(ctx.exception.response.text, '{"error": "bad request"}')
        self.assertEqual(ctx.exception.request.method, "GET")
        self.assertTrue(response.closed)
        self.assertTrue(response.body_read_before_close)


if __name__ == '__main__':
    unittest.main()
