import json
import requests
import calendar
from datetime import date
import tqdm


def get_events_for_month(year: int = 2025, month: int = 1):
    start_date = f"{year}-{month:02d}-01"

    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    response = requests.get(
        f"https://kissimmeefl.api.civicclerk.com/v1/Events?$filter=startDateTime+ge+{start_date}+and+startDateTime+lt+{end_date}&$orderby=startDateTime+asc,+eventName+asc"
    )
    return response.json()["value"]


all_events = {}

# For every month from June 2023 to now.
startDate = "2023-06-01"
endDate = date.today().strftime("%Y-%m-%d")
for year in tqdm.trange(2023, 2025):
    for month in tqdm.trange(1, 13):
        current_date = f"{year}-{month:02d}-01"
        if current_date < startDate or current_date > endDate:
            continue
        events = get_events_for_month(year, month)
        all_events |= {event["id"]: event for event in events}

print(f"Found {len(all_events)} events")


with open("data/events.json", "w") as f:
    json.dump(all_events, f, indent=2)

pab_meetings = {
    id: event
    for id, event in all_events.items()
    if event["eventName"].startswith("Planning")
}

with open("data/pab_meetings.json", "w") as f:
    json.dump(pab_meetings, f, indent=2)

print(f"Number of PAB meetings: {len(pab_meetings)}")


def get_event_media(event_id: str) -> dict:
    response = requests.get(
        f"https://kissimmeefl.api.civicclerk.com/v1/EventsMedia/{event_id}"
    )
    return response.json()


medias = {}

for id in pab_meetings:
    print(f"Processing PAB meeting {id}")
    media = get_event_media(id)
    medias[id] = media

with open("data/pab_meetings_media.json", "w") as f:
    json.dump(medias, f, indent=2)


for id, item in medias.items():
    if url := item.get("closedCaptionUrl"):
        response = requests.get(url)
        filename = f"data/pab_meetings/{pab_meetings[id]['eventDate'][:10]}.srt"
        print(f"Downloading transcript for {filename}")
        with open(filename, "wb") as f:
            f.write(response.content)
