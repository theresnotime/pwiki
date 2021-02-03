"""Collection of methods shared by query classes"""
from __future__ import annotations

import logging

from typing import Any, TYPE_CHECKING, Union

from .utils import has_error, make_params, mine_for, read_error

if TYPE_CHECKING:
    from .wiki import Wiki

log = logging.getLogger(__name__)


def basic_query(wiki: Wiki, pl: dict, big_query: bool = False) -> dict:
    """Performs a query action and returns the response from the server as json.

    Args:
        wiki (Wiki): The Wiki object to use
        pl (dict): The parameter list to send.  Do not include `{"action": "query"}`, this pair will be automatically included.
        big_query (bool, optional): Indicates if the query could be large, in which case a `POST` will be performed instead.  Defaults to False.

    Returns:
         dict: The response from the server.  Empty dict if something went wrong
    """
    p = make_params("query", pl)
    try:
        return (wiki.client.post(wiki.endpoint, data=p) if big_query else wiki.client.get(wiki.endpoint, params=p)).json()
    except Exception:
        log.error("%s: Could not reach server or read response while performing query with params: %s", wiki, p, exc_info=True)

    return {}


def chunker(l: list, size: int) -> tuple:
    """Divides the input list, `l`, into equal sub-lists of size, `size`.  Any remainder will be in the last element.

    Args:
        l (list): The input list
        size (int): The maximum size of the sub-lists

    Returns:
        tuple: The output tuple containing all the sub-lists derived from `l`.
    """
    return (l[pos:pos + size] for pos in range(0, len(l), size))


def denormalize_result(d: dict, normalized: list, target_class: type[Any]):
    """Reads the normalized json array returned by queries and denormalizes, merges, and updates `d` accordingly.

    Args:
        d (dict): The results dict which will eventually be returned to the caller
        normalized (list): The normalized array returned by a query.  If `None`, then this method does nothing.
        target_class (type[Any]): The type of the values in `d`.  This indicates the merge stratedgy to be used.
    """
    if normalized:
        for e in normalized:
            new = d.pop(e["to"])
            existing = d[e["from"]] if e["from"] in d else target_class()

            if target_class == list:
                existing += new
            elif target_class == dict:
                existing |= new
            else:
                existing = new

            d[e["from"]] = existing


def extract_body(id: str, response: dict) -> Union[dict, list]:
    """Gets the value from a json object 2 levels down, following the path `"query"` -> `id`.  Useful for extracting the results of a query.

    Args:
        id (str): The key under `"query"` in `response` to fetch.
        response (dict): The response from the server.

    Returns:
        Union[dict, list]: the contents under `"query"` -> `id`.
    """
    return mine_for(response, "query", id)


def get_continue_params(response: dict) -> dict:
    """Gets the query continuation parameters from the response

    Args:
        response (dict): The response from the server

    Returns:
        dict: The continuation paramters to be applied to the next query
    """
    return response.get("continue", {})


def query_and_validate(wiki: Wiki, pl: dict, big_query: bool = False, desc: str = "perform query") -> dict:
    """Performs a `basic_query()` and checks the results for errors.  If there is an error, it will be logged accordingly.

    Args:
        wiki (Wiki): The Wiki object to use
        pl (dict): The parameter list to send.  Do not include `{"action": "query"}`, this pair will be automatically included.
        big_query (bool, optional): Indicates if the query could be large, in which case a `POST` will be performed instead.  Defaults to False.
        desc (str, optional): A few words describing what this query was trying to accomplish.  This will be displayed in the logs if there was an error. Defaults to "perform query".

    Returns:
        dict: The response from the server.  `None` if something went wrong.
    """
    if not (response := basic_query(wiki, pl, big_query)):
        log.error("%s: No response from server while trying to %s", wiki, desc)
        log.debug("Sent parameters: %s", pl)
        return

    if not has_error(response):
        return response

    log.error("%s: encountered error while trying to %s, server said: %s", wiki, desc, read_error("query", response))
    log.debug(response)
