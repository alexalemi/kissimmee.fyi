"""The city uses a civicclerk portal for hosting the meeting agenda."""

import json
import requests
from datetime import datetime
from typing import Literal
from urllib.parse import urljoin

BASE_URL = "https://kissimmeefl.api.civicclerk.com/v1"


def get_civic_clerk_events(
    filter_date: str | None = None,
    filter_operator: Literal["lt", "gt"] = "lt",
    order_by: str = "startDateTime desc, eventName desc",
    path: str = "Events",
) -> requests.Response:
    """
    Make an API call to the CivicClerk portal to retrieve events.

    Args:
        base_url: The base URL for the CivicClerk API endpoint
        filter_date: Filter events with startDateTime less than or greater than this date (format: YYYY-MM-DD)
        filter_operator: Comparison operator for date filtering ('lt' for less than, 'gt' for greater than)
        order_by: Order by clause for sorting results

    Returns:
        Response object from the API call
    """
    params = {}
    if filter_date is None:
        filter_date = datetime.now().strftime("%Y-%m-%d")

    if filter_date:
        params["$filter"] = f"startDateTime {filter_operator} {filter_date}"

    if order_by:
        params["$orderby"] = order_by

    url = urljoin(BASE_URL, path)
    print(f"{url=}")
    response = requests.get(url, params=params)
    return response


def get_civic_clerk_event(
    event_id: int,
    path: str = "Events",
) -> requests.Response:
    """
    Make an API call to the CivicClerk portal to retrieve a specific event.

    Args:
        event_id: The ID of the event to retrieve
        base_url: The base URL for the CivicClerk Events API endpoint

    Returns:
        Response object from the API call
    """
    url = urljoin(BASE_URL, f"{path}/{event_id}")
    response = requests.get(url)
    return response


def get_civic_clerk_event_media(
    event_id: int,
    path: str = "EventsMedia",
) -> requests.Response:
    """
    Make an API call to the CivicClerk portal to retrieve event media.

    Args:
        event_id: The ID of the event to retrieve media for
        base_url: The base URL for the CivicClerk EventsMedia API endpoint

    Returns:
        Response object from the API call
    """
    url = urljoin(BASE_URL, f"{path}/{event_id}")
    response = requests.get(url)
    return response


# stream/KISSIMMEEFL/4ee3390e-3566-4e08-97ce-e752cfb95a3d.pdf

if __name__ == "__main__":
    response = get_civic_clerk_events()
    print(response)
    # with open("data/events.json", "w") as f:
    #     json.dump(response.json(), f)
