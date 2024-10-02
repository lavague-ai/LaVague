from typing import Optional


class NavigationException(Exception):
    pass


class ExtractorException(Exception):
    pass


class CannotBackException(NavigationException):
    def __init__(self, message="History root reached, cannot go back"):
        super().__init__(message)


class NoPageException(NavigationException):
    def __init__(self, message="No page loaded"):
        super().__init__(message)


class RetrievalException(NavigationException):
    pass


class NoElementException(RetrievalException):
    def __init__(self, message="No element found"):
        super().__init__(message)


class AmbiguousException(RetrievalException):
    def __init__(self, message="Multiple elements could match"):
        super().__init__(message)


class HallucinatedException(RetrievalException):
    def __init__(self, xpath: str, message: Optional[str] = None):
        super().__init__(message or f"Element was hallucinated: {xpath}")


class ElementOutOfContextException(RetrievalException):
    def __init__(self, xpath: str, message: Optional[str] = None):
        super().__init__(message or f"Element exists but was not in context: {xpath}")
