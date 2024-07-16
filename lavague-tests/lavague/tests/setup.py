from typing import Dict
import http.server
import socketserver
import threading
import os


class Setup:
    default_url: str = None

    def start(self):
        pass

    def stop(self):
        pass

    @staticmethod
    def parse(directory: str, args: Dict) -> "Setup":
        if args.get("type", "web") == "web":
            return Setup()

        if args["type"] == "static":
            directory = os.path.join(directory, args.get("directory", "www"))
            return StaticServer(directory, args.get("port", "8000"))


class StaticServer(Setup):
    default_url = "http://localhost:8000"
    httpd: socketserver.TCPServer = None

    def __init__(self, directory: str, port: int):
        self.directory = directory
        self.port = port

    def start(self):
        def handler(*args, **kwargs):
            http.server.SimpleHTTPRequestHandler(
                *args, directory=self.directory, **kwargs
            )

        self.httpd = socketserver.TCPServer(("", self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.thread.join()
