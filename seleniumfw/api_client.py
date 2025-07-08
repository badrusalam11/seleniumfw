# File: seleniumfw/api_client.py
import requests

class ApiClient:
    def __init__(self, base_url: str, default_headers: dict = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

    def request(self, method: str, path: str, **kwargs):
        """
        Send an HTTP request using the session.

        :param method: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
        :param path: Path relative to the base_url
        :param kwargs: Passed to requests.Session.request (params, json, data, headers, etc.)
        :return: requests.Response object
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

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
