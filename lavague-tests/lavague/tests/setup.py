from typing import Dict, Optional, Any
import http.server
import socketserver
import threading
import os


class Setup:
    default_url: Optional[str] = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def start(self):
        pass

    def stop(self):
        pass

    @staticmethod
    def parse(directory: str, args: Dict) -> "Setup":
        if args["type"] == "static":
            directory = os.path.join(directory, args.get("directory", "www"))
            return StaticServer(directory, args.get("port", "8000"))

        return Setup()


class StaticServer(Setup):
    default_url = "http://localhost:8000"
    httpd: Optional[socketserver.TCPServer] = None

    def __init__(self, directory: str, port: int):
        self.directory = directory
        self.port = port

    def start(self):
        def handler(*args, **kwargs) -> Any:
            try:
                return http.server.SimpleHTTPRequestHandler(
                    *args, directory=self.directory, **kwargs
                )
            except ConnectionResetError:
                pass

        self.httpd = socketserver.TCPServer(("", self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.thread.join()
