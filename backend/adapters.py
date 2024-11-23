# Description: This file contains the adapter functions that are used to convert data from one format to another.

from urllib.parse import unquote


def url_decode(text: str) -> str:
    """
    Decodes a URL-encoded string.

    Args:
        text (str): A URL-encoded string.

    Returns:
        str: A decoded string.
    """
    return unquote(text)


ADAPTERS_MAP: dict[str, callable] = {
    "Ai4Chat": url_decode,
}


def adapt_response(model_name: str, text: str) -> str:
    """
    Adapts the given text based on the model.

    Args:
        model_name (str): The name of the model.
        text (str): The text to adapt.

    Returns:
        str: The adapted text.
    """
    adapter = ADAPTERS_MAP.get(model_name)
    if adapter is None:
        return text
    return adapter(text)
