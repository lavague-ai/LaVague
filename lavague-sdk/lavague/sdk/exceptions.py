class DriverException(Exception):
    pass


class CannotBackException(DriverException):
    def __init__(self, message="History root reached, cannot go back"):
        super().__init__(message)


class NoPageException(DriverException):
    def __init__(self, message="No page loaded"):
        super().__init__(message)


class ElementNotFoundException(DriverException):
    def __init__(self, xpath: str):
        super().__init__(f"Element not found: {xpath}")