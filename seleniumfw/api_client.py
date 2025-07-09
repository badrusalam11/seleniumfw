# File: seleniumfw/api_client.py
import threading
import os
from seleniumfw.thread_context import _thread_locals, _thread_data
import requests

# ensure we have a thread‑local container for API calls
if not hasattr(_thread_data, "api_calls"):
    _thread_data.api_calls = []

class ApiClient:
    def __init__(self, base_url: str, default_headers: dict = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

        # wrap the session.request method
        original_request = self.session.request

        def record_and_request(method, url, *args, **kwargs):
            full_url = url if url.startswith('http') else f"{self.base_url}/{url.lstrip('/')}"
            # record request info
            record = {
                "method": method,
                "url": full_url,
                "kwargs": kwargs.copy(),
            }

            try:
                response = original_request(method, full_url, *args, **kwargs)
                response.raise_for_status()
                record["status_code"] = response.status_code
                # you can record more: headers, body, etc.
                # but be cautious with very large bodies
                record["response_body"] = response.text
                return response
            finally:
                # store record in thread‑local
                if not hasattr(_thread_data, "api_calls"):
                    _thread_data.api_calls = []
                _thread_data.api_calls.append(record)

        # replace the session.request with our wrapper
        self.session.request = record_and_request

    def request(self, method: str, path: str, **kwargs):
        """
        Send an HTTP request using the session.

        :param method: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
        :param path: Path relative to the base_url
        :param kwargs: Passed to requests.Session.request (params, json, data, headers, etc.)
        :return: requests.Response object
        """
        return self.session.request(method, path, **kwargs)

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def head(self, path: str, **kwargs):
        return self.request("HEAD", path, **kwargs)

    def options(self, path: str, **kwargs):
        return self.request("OPTIONS", path, **kwargs)
