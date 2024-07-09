from typing import Dict
import http.server
import socketserver


class Setup:
    default_url: str = None

    def start(self):
        pass

    def stop(self):
        pass

    @staticmethod
    def parse(args: Dict) -> "Setup":
        if "type" not in args:
            return Setup()

        if args["type"] == "static":
            return StaticServer(args.get("directory", "www", args.get("port", "8000")))


class StaticServer(Setup):
    default_url = "http://localhost:8000"

    def __init__(self, directory: str, port: str):
        self.directory = directory
        self.port = port

    def start(self):
        with socketserver.TCPServer(
            ("", self.port),
            lambda r, c: http.server.SimpleHTTPRequestHandler(
                r, c, directory=self.directory
            ),
        ) as httpd:
            httpd.serve_forever()
