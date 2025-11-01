#!/usr/bin/env python3
"""
Fetch public notices from Florida Public Notices and generate static HTML and RSS feed.
"""
import json
import os
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import html

from publicnotices import get_kissimmee_planning_advisory_board_docs


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')


def generate_rss(notices, output_path):
    """Generate RSS 2.0 feed from notices data."""
    from datetime import timezone

    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    # Channel info
    title = SubElement(channel, 'title')
    title.text = 'Kissimmee Planning Advisory Board - Public Notices'

    link = SubElement(channel, 'link')
    link.text = 'https://kissimmee.fyi'

    description = SubElement(channel, 'description')
    description.text = 'Public notices for Kissimmee Planning Advisory Board meetings and proceedings'

    last_build = SubElement(channel, 'lastBuildDate')
    now_utc = datetime.now(timezone.utc)
    last_build.text = now_utc.strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Add items
    for notice in notices:
        item = SubElement(channel, 'item')

        item_title = SubElement(item, 'title')
        item_title.text = notice.get('title', 'Untitled Notice')

        item_link = SubElement(item, 'link')
        item_link.text = notice.get('pdf_url') or notice.get('link') or 'https://kissimmee.fyi'

        item_desc = SubElement(item, 'description')
        item_desc.text = notice.get('description', '')

        if notice.get('pub_date_rfc822'):
            pub_date = SubElement(item, 'pubDate')
            pub_date.text = notice['pub_date_rfc822']

        guid = SubElement(item, 'guid', isPermaLink='false')
        guid.text = f"kissimmee-notice-{notice.get('id', hash(notice.get('title', '')))}"

        # Add image as enclosure if available
        if notice.get('image_url'):
            enclosure = SubElement(item, 'enclosure',
                                  url=notice['image_url'],
                                  type='image/jpeg')

    # Write to file
    xml_string = prettify_xml(rss)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_string)


def parse_notice(notice_data):
    """Parse a single notice from the API response."""
    # Debug: Print the first notice structure
    if not hasattr(parse_notice, 'debug_printed'):
        print("Sample notice data structure:")
        print(json.dumps(notice_data, indent=2))
        parse_notice.debug_printed = True

    # Extract notice details based on actual API structure
    notice_id = notice_data.get('id')
    notice_text = notice_data.get('notice', '')
    subcategory = notice_data.get('subcategory', '')
    paper = notice_data.get('paper', '')
    city = notice_data.get('city', '')

    # Build a title from available fields
    title = f"{subcategory}" if subcategory else "Public Notice"
    if city:
        title = f"{title} - {city}"

    # Build description
    description_parts = []
    if paper:
        description_parts.append(f"Published in: {paper}")
    if notice_text:
        description_parts.append(notice_text)
    description = ' | '.join(description_parts)

    # Build link to notice detail page if available
    link = None
    if notice_data.get('_links', {}).get('self', {}).get('href'):
        href = notice_data['_links']['self']['href']
        link = f"https://floridapublicnotices.com{href}"

    parsed = {
        'id': notice_id,
        'title': title,
        'description': description,
        'notice_text': notice_text,
        'pub_date': notice_data.get('date'),
        'pdf_url': None,  # Not provided in this API response
        'link': link,
        'image_url': notice_data.get('image'),
        'newspaper': paper,
        'city': city,
        'subcategory': subcategory,
    }

    # Try to format the publication date as RFC 822 for RSS
    if parsed['pub_date']:
        try:
            # Parse the date (format: "2025-11-01")
            dt = datetime.fromisoformat(parsed['pub_date'])
            parsed['pub_date_rfc822'] = dt.strftime('%a, %d %b %Y 00:00:00 +0000')
            parsed['pub_date_formatted'] = dt.strftime('%B %d, %Y')
        except Exception as e:
            print(f"Error parsing date {parsed['pub_date']}: {e}")
            parsed['pub_date_rfc822'] = None
            parsed['pub_date_formatted'] = parsed['pub_date']
    else:
        parsed['pub_date_rfc822'] = None
        parsed['pub_date_formatted'] = None

    return parsed


def generate_notice_html(notice):
    """Generate HTML for a single notice."""
    html_parts = ['<div class="notice">']

    # Title
    html_parts.append('<div class="notice-title">')
    if notice.get('pdf_url'):
        html_parts.append(f'<a href="{html.escape(notice["pdf_url"])}" target="_blank">{html.escape(notice["title"])}</a>')
    else:
        html_parts.append(html.escape(notice["title"]))
    html_parts.append('</div>')

    # Date
    if notice.get('pub_date_formatted'):
        html_parts.append(f'<div class="notice-date">{html.escape(notice["pub_date_formatted"])}</div>')

    # Description
    if notice.get('description'):
        html_parts.append(f'<div class="notice-description">{html.escape(notice["description"])}</div>')

    # Image
    if notice.get('image_url'):
        html_parts.append(f'<img class="notice-image" src="{html.escape(notice["image_url"])}" alt="{html.escape(notice["title"])}" loading="lazy">')

    # Links
    links = []
    if notice.get('pdf_url'):
        links.append(f'<a href="{html.escape(notice["pdf_url"])}" target="_blank">View PDF</a>')
    if notice.get('link'):
        links.append(f'<a href="{html.escape(notice["link"])}" target="_blank">Details</a>')

    if links:
        html_parts.append('<div class="notice-links">')
        html_parts.append(' '.join(links))
        html_parts.append('</div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


def generate_static_html(notices, template_path, output_path, updated_time):
    """Generate static HTML from template."""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Generate HTML for all notices
    if notices:
        notices_html = '\n'.join(generate_notice_html(notice) for notice in notices)
    else:
        notices_html = '<p>No notices found.</p>'

    # Generate updated timestamp
    updated_html = f'Last updated: {updated_time.strftime("%B %d, %Y at %I:%M %p UTC")}'

    # Replace placeholders
    html_output = template.replace('<!-- NOTICES_PLACEHOLDER -->', notices_html)
    html_output = html_output.replace('<!-- UPDATED_PLACEHOLDER -->', updated_html)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)


def main():
    """Main function to fetch notices and generate output files."""
    print("Fetching public notices...")

    try:
        response = get_kissimmee_planning_advisory_board_docs(limit=50)
        response.raise_for_status()

        data = response.json()
        print(f"Received response: {response.status_code}")

        # Debug: Print response structure
        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Response is a list'}")

        # Parse notices from response
        # The actual structure may vary - adjust based on API response
        raw_notices = data.get('_embedded', {}).get('notices', [])
        if not raw_notices:
            raw_notices = data.get('results', [])
        if not raw_notices and isinstance(data, list):
            raw_notices = data

        notices = [parse_notice(n) for n in raw_notices]
        print(f"Parsed {len(notices)} notices")

        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(script_dir, '..', 'docs')

        # Ensure docs directory exists
        os.makedirs(docs_dir, exist_ok=True)

        updated_time = datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None)
        if updated_time.tzinfo is None:
            # Fallback for older Python versions
            from datetime import timezone
            updated_time = datetime.now(timezone.utc)

        # Generate static HTML
        template_path = os.path.join(docs_dir, 'template.html')
        html_path = os.path.join(docs_dir, 'index.html')
        generate_static_html(notices, template_path, html_path, updated_time)
        print(f"Generated {html_path}")

        # Generate RSS
        rss_path = os.path.join(docs_dir, 'rss.xml')
        generate_rss(notices, rss_path)
        print(f"Generated {rss_path}")

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
