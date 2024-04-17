import re
from typing import List

def clean_html(html_to_clean: str, tags_to_remove: List[str] = ['style', 'svg', 'script'], attributes_to_keep: List[str] = ['id', 'href']) -> str:
    """
    Clean HTML content by removing specified tags and attributes while keeping specified attributes.

    Args:
        html_to_clean (str): The HTML content to clean.
        tags_to_remove (List[str]): List of tags to remove from the HTML content. Default is ['style', 'svg', 'script'].
        attributes_to_keep (List[str]): List of attributes to keep in the HTML tags. Default is ['id', 'href'].

    Returns:
        str: The cleaned HTML content.

    Example:
    >>> from clean_html_for_llm import clean_html
    >>> cleaned_html = clean_html('<div id="main" style="color:red">Hello <script>alert("World")</script></div>', tags_to_remove=['script'], attributes_to_keep=['id'])
    """
    for tag in tags_to_remove:
        html_to_clean = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html_to_clean, flags=re.DOTALL)

    attributes_to_keep = '|'.join(attributes_to_keep)
    pattern = rf'\b(?!({attributes_to_keep})\b)\w+(?:-\w+)?\s*=\s*["\'][^"\']*["\']'
    cleaned_html = re.sub(pattern, '', html_to_clean)
    return cleaned_html