from typing import Iterable, Callable, TypeVar, Optional

T = TypeVar("T")


def nested_get(d: dict, keys: list):
    """Get a value from a nested dictionary using a list of keys.

    Args:
        d (dict): The dictionary to get the value from.
        keys (list): A list of keys to navigate through the dictionary.

    Returns:
        The value from the nested dictionary.

    Raises:
        KeyError: If any key in keys does not exist in the dictionary.
    """
    for key in keys:
        d = d[key]
    return d


def nested_set(d: dict, keys: list, value):
    """Set a value in a nested dictionary using a list of keys. If a key
    does not exist, it will be created.

    Args:
        d (dict): The dictionary to set the value in.
        keys (list): A list of keys to navigate through the dictionary.
        value: The value to set in the dictionary.
    """
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def find(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Optional[T]:
    """Find the first item in an iterable that matches a predicate.

    Args:
        iterable (Iterable): The iterable to search.
        predicate (Callable): A function that takes an item and returns True if it matches.

    Returns:
        The first item that matches the predicate, or None if no match is found.
    """
    return next((item for item in iterable if predicate(item)), None)
