import requests


def get_kissimmee_planning_advisory_board_docs(
    offset=None, limit=12, keywords='"Kissimmee Planning Advisory Board"'
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
    headers = {"content-type": "application/hal+json"}
    data = {
        "counties": [],
        "keywords": keywords,
        "offset": offset,
        "paper": "-1",
        "sort-by": None,
        "limit": limit,
    }

    response = requests.post(url, headers=headers, json=data)
    return response
