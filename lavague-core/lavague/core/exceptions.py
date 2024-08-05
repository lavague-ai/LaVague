class NavigationException(Exception):
    pass


class CannotBackException(NavigationException):
    def __init__(self, message="History root reached, cannot go back"):
        super().__init__(message)
