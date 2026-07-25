import unittest
import sys
import os
from unittest.mock import Mock
import requests

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.restpylot.main import RestClient

class TestRestClient(unittest.TestCase):
    def setUp(self):
        self.client = RestClient(base_url="https://jsonplaceholder.typicode.com")

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

            def raise_for_status(self):
                raise requests.exceptions.HTTPError(
                    "boom",
                    response=self,
                    request=requests.Request("GET", "https://example.test/bad").prepare(),
                )

            def json(self):
                return self._json

            @property
            def text(self):
                return self._text

        response = DummyResponse()
        self.client.session.request = Mock(return_value=response)

        with self.assertRaises(requests.exceptions.HTTPError) as ctx:
            self.client.get("bad")

        self.assertEqual(ctx.exception.response.status_code, 500)
        self.assertEqual(ctx.exception.response.text, '{"error": "bad request"}')
        self.assertEqual(ctx.exception.request.method, "GET")

if __name__ == '__main__':
    unittest.main()