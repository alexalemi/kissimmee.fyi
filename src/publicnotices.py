import requests
import logging


def get_kissimmee_planning_advisory_board_docs(
    offset=None, limit=12, keywords=f'"Planning Advisory Board"'
):
    """
    Fetch documents from Florida Public Notices for Kissimmee Planning Advisory Board.

    Args:
        offset: Pagination offset (default: None)
        limit: Number of results to return (default: 12)
        keywords: Search keywords (default: "Kissimmee Planning Advisory Board")

    Returns:
        Response object from the API request
    """
    url = "https://floridapublicnotices.com/"
    headers = {"content-type": "application/json; charset=utf-8"}
    data = {
        "counties": ["49"],  # Osceola County
        "keywords": keywords,
        "offset": offset,
        "paper": "-1",
        "sort-by": None,
        "limit": limit,
    }

    logging.debug(
        f"Requesting documents from Florida Public Notices at {url=}, {headers=}, {data=}"
    )
    response = requests.post(url, headers=headers, json=data)
    import json

    logging.debug("Got response:", json.dumps(response.json(), indent=2))
    return response
