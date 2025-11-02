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


# Zoning code mapping (from https://www.kissimmee.gov/Business-Development/Development/Planning-Zoning/Find-Your-Propertys-Zoning-Category/Zoning-Classifications)
ZONING_CODES = {
    'AC': 'Agriculture and Conservation',
    'RE': 'Residential Estate',
    'RA-1': 'Single Family Residential (12,000 sq. ft.)',
    'RA-2': 'Single Family Residential (9,000 sq. ft.)',
    'RA-3': 'Single Family Residential (7,000 sq. ft.)',
    'RA-4': 'Single Family Residential (6,000 sq. ft.)',
    'RB-1': 'Medium Density Residential',
    'RB-2': 'Medium Density Residential/Office',
    'RC-1': 'Multiple Family Medium Density Residential',
    'RC-2': 'Multiple Family High Density Residential',
    'MH': 'Mobile Home',
    'MHP': 'Mobile Home Park',
    'RPB': 'Residential Professional Business',
    'B-2': 'Neighborhood Commercial',
    'B-3': 'General Commercial',
    'HC': 'Highway Commercial',
    'B-5': 'Office Commercial',
    'BP': 'Business Park',
    'IB': 'Industrial Business',
    'AO': 'Airport Operations',
    'AI': 'Airport Industrial',
    'CF': 'Community Facilities',
    'HF': 'Hospital Facilities',
    'UT': 'Utilities',
    'OS': 'Open Space',
    'T1': 'Natural',
    'T3': 'Edge',
    'T4-R': 'Neighborhood Restricted',
    'TD': 'Neighborhood Open',
    'T5-U': 'Mixed-Use Urban Core',
    'T5-M': 'Mixed-Use Center',
    'T6': 'Waterfront',
    'SD': 'Special District',
    'PUD': 'Planned Unit Development',
    'REC': 'Recreation',
}

# Future Land Use code mapping
LAND_USE_CODES = {
    'SF-LDR': 'Single Family Low Density Residential',
    'SF-MDR': 'Single Family Medium Density Residential',
    'MF-MDR': 'Multiple Family Medium Density Residential',
    'MH-MDR': 'Mobile Home Medium Density Residential',
    'MU': 'Mixed Use',
    'MU-D': 'Mixed-Use Downtown',
    'MU-V': 'Mixed-Use Vine',
    'MU-T': 'Mixed-Use Tapestry',
    'MU-FR': 'Mixed-Use Flora Ridge',
    'CG': 'Commercial General',
    'OR': 'Office-Residential',
    'IN': 'Industrial Business',
    'REC': 'Recreation',
    'CONS': 'Conservation',
    'INST': 'Institutional',
    'UT': 'Utilities',
    'AE': 'Airport Expansion',
    'MMTD': 'Multimodal Transportation District',
}

# Common acronyms
ACRONYMS = {
    'PAB': 'Planning Advisory Board',
    'MUPUD': 'Mixed Use Planned Urban Development',
}


def wrap_codes_with_abbr(text):
    """Wrap zoning codes, land use codes, and acronyms with HTML abbr tags."""
    import re

    if not text:
        return text

    # Combine all code mappings
    all_codes = {**ZONING_CODES, **LAND_USE_CODES, **ACRONYMS}

    # Sort by length (descending) to match longer codes first (e.g., "MU-FR" before "MU")
    sorted_codes = sorted(all_codes.keys(), key=len, reverse=True)

    # Create pattern that matches codes as whole words or with specific boundaries
    # Match codes that are surrounded by word boundaries, parentheses, or dashes
    for code in sorted_codes:
        # Escape special regex characters in the code
        escaped_code = re.escape(code)
        # Pattern: code must be at word boundary or followed by space/paren/dash/end
        pattern = r'\b(' + escaped_code + r')(?=\s|\(|\)|,|$|-(?!\w))'
        replacement = f'<abbr title="{html.escape(all_codes[code])}">{code}</abbr>'
        text = re.sub(pattern, replacement, text)

    return text


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')


def load_archive(archive_path):
    """Load the historical notices archive from JSON file."""
    if not os.path.exists(archive_path):
        return {"last_updated": None, "notices": {}}

    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load archive from {archive_path}: {e}")
        return {"last_updated": None, "notices": {}}


def merge_notices(archive, new_notices):
    """Merge new notices into archive, preserving all historical data."""
    archive_notices = archive.get("notices", {})
    # Use timezone-aware datetime
    current_date = datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None)
    if current_date.tzinfo is None:
        from datetime import timezone
        current_date = datetime.now(timezone.utc)
    current_date = current_date.isoformat()

    for notice in new_notices:
        notice_id = str(notice['id'])

        if notice_id in archive_notices:
            # Update existing notice
            archive_notices[notice_id].update(notice)
            archive_notices[notice_id]['last_seen'] = current_date
        else:
            # Add new notice
            notice['first_seen'] = current_date
            notice['last_seen'] = current_date
            archive_notices[notice_id] = notice

    archive['notices'] = archive_notices
    archive['last_updated'] = current_date

    return archive


def save_archive(archive, archive_path):
    """Save the notices archive to JSON file."""
    try:
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(archive, f, indent=2, ensure_ascii=False)
        print(f"Saved archive with {len(archive['notices'])} total notices")
    except IOError as e:
        print(f"Error: Could not save archive to {archive_path}: {e}")


def get_orphaned_thumbnails(thumbnails_dir, current_notices):
    """Find thumbnail files that are not referenced in current notices."""
    if not os.path.exists(thumbnails_dir):
        return []

    # Get all notice IDs that should have thumbnails (only current notices)
    valid_ids = set()
    for notice in current_notices:
        valid_ids.add(str(notice['id']))

    # Find thumbnails that don't match any valid ID
    orphaned = []
    for filename in os.listdir(thumbnails_dir):
        if filename.endswith('.jpg'):
            notice_id = filename[:-4]  # Remove .jpg extension
            if notice_id not in valid_ids:
                orphaned.append(os.path.join(thumbnails_dir, filename))

    return orphaned


def cleanup_thumbnails(thumbnails_dir, current_notices):
    """Delete thumbnail files that are not referenced in current notices."""
    orphaned = get_orphaned_thumbnails(thumbnails_dir, current_notices)

    if orphaned:
        print(f"Cleaning up {len(orphaned)} orphaned thumbnails...")
        for filepath in orphaned:
            try:
                os.remove(filepath)
                print(f"  Deleted {os.path.basename(filepath)}")
            except OSError as e:
                print(f"  Warning: Could not delete {filepath}: {e}")
    else:
        print("No orphaned thumbnails to clean up")


def extract_meeting_date(text):
    """Extract the meeting date and time from notice text."""
    import re
    # Pattern: "on Wednesday, November 19, 2025 at 6:00 p.m."
    pattern = r'on\s+(\w+),\s+(\w+)\s+(\d{1,2}),\s+(\d{4})\s+at\s+([\d:]+\s*[ap]\.?m\.?)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        day, month, date, year, time = match.groups()
        return f"{day}, {month} {date}, {year} at {time}"
    return None


def extract_property_address(text):
    """Extract property address from notice text."""
    import re
    # Pattern: "located at approximately 2220 Fortune Road" or "located at 2220 Fortune Road"
    pattern = r'located at(?:\s+approximately)?\s+([^,\n\.]+?)(?:,|\s+Parcel|\.|\s+Legal)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_zoning_change(text):
    """Extract zoning change (FROM/TO) from notice text."""
    import re
    # Pattern: "FROM: RC-1 (description) TO: RC-2 (description)"
    from_pattern = r'FROM:\s*([^\n]+?)\s+(?:City|TO:)'
    to_pattern = r'TO:\s*([^\n]+?)\s+(?:City|The)'

    from_match = re.search(from_pattern, text, re.IGNORECASE)
    to_match = re.search(to_pattern, text, re.IGNORECASE)

    if from_match and to_match:
        from_zone = from_match.group(1).strip()
        to_zone = to_match.group(1).strip()
        return f"{from_zone} → {to_zone}"
    return None


def extract_reference_number(text):
    """Extract reference number from notice text."""
    import re
    # Pattern: "Reference # ZMA-25-0009"
    pattern = r'Reference\s*#\s*([^\s\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_amendment_type(ref_num):
    """Extract and categorize amendment type from reference number."""
    if not ref_num:
        return None

    ref_upper = ref_num.upper()

    # Map amendment codes to full names
    amendment_types = {
        'LUPA': 'Future Land Use Amendment',
        'ZMA': 'Zoning Map Amendment',
        'PUD': 'Planned Unit Development',
        'VAR': 'Variance',
        'CUP': 'Conditional Use Permit',
        'SPR': 'Site Plan Review'
    }

    for code, full_name in amendment_types.items():
        if code in ref_upper:
            return {'code': code, 'name': full_name}

    return None


def extract_parcel_id(text):
    """Extract parcel ID from notice text."""
    import re
    # Pattern: "Parcel ID: 19-25-30-00U0-0050-0000" or "Parcel IDs: ..." or "Parcel 1: ... Parcel 2: ..."
    # First try standard format
    pattern = r'Parcel IDs?:\s*([^\n]+?)(?:\s+Legal|$)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try alternative format: "Parcel 1: ... Together with Parcel 2: ..."
    alt_pattern = r'Parcel\s+\d+:\s*([0-9\-]+)(?:.*?Parcel\s+\d+:\s*([0-9\-]+))?'
    alt_matches = re.findall(alt_pattern, text, re.IGNORECASE)
    if alt_matches:
        parcels = []
        for match_tuple in alt_matches:
            for parcel in match_tuple:
                if parcel:
                    parcels.append(parcel)
        if parcels:
            return ' and '.join(parcels)

    return None


def format_parcel_id_for_url(parcel_id):
    """Convert parcel ID to URL format for property appraiser search."""
    if not parcel_id:
        return None
    # Remove spaces and dashes
    formatted = parcel_id.replace(' ', '').replace('-', '')
    return formatted


def split_parcel_ids(parcel_id_string):
    """Split a string containing multiple parcel IDs into individual IDs."""
    if not parcel_id_string:
        return []

    # Split by " and " or comma
    import re
    parcels = re.split(r'\s+and\s+|,\s*', parcel_id_string)
    return [p.strip() for p in parcels if p.strip()]


def generate_parcel_links(parcel_id_string):
    """Generate HTML links for one or more parcel IDs."""
    parcels = split_parcel_ids(parcel_id_string)

    if not parcels:
        return html.escape(parcel_id_string) if parcel_id_string else ''

    links = []
    for parcel in parcels:
        parcel_url_format = format_parcel_id_for_url(parcel)
        if parcel_url_format:
            parcel_url = f'https://search.property-appraiser.org/Search/MainSearch?pin={parcel_url_format}'
            links.append(f'<a href="{parcel_url}" target="_blank">{html.escape(parcel)}</a>')
        else:
            links.append(html.escape(parcel))

    return ', '.join(links)


def generate_short_description(notice_text, address, zoning, ref_num):
    """Generate a concise description from extracted fields."""
    parts = []

    # Determine action type from reference number
    action = "Notice"
    if ref_num:
        if 'ZMA' in ref_num:
            action = "Rezoning"
        elif 'PUD' in ref_num:
            action = "Planned Unit Development"
        elif 'VAR' in ref_num:
            action = "Variance"

    # Build description
    if address and zoning:
        parts.append(f"{action} at {address}: {zoning}")
    elif address:
        parts.append(f"{action} at {address}")
    elif zoning:
        parts.append(f"{action}: {zoning}")
    else:
        # Fallback: extract first sentence or first 150 chars
        if notice_text:
            first_sentence = notice_text.split('.')[0]
            if len(first_sentence) > 150:
                parts.append(first_sentence[:147] + "...")
            else:
                parts.append(first_sentence)

    return parts[0] if parts else ""


def generate_pdf_thumbnail(pdf_url, notice_id, thumbnails_dir):
    """Download PDF and generate thumbnail from first page."""
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image
        import requests

        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()

        # Convert first page to image
        images = convert_from_bytes(response.content, first_page=1, last_page=1, dpi=150)

        if images:
            # Resize to thumbnail (max width 400px, maintain aspect ratio)
            img = images[0]
            max_width = 400
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Ensure thumbnails directory exists
            os.makedirs(thumbnails_dir, exist_ok=True)

            # Save as JPEG
            thumbnail_path = os.path.join(thumbnails_dir, f"{notice_id}.jpg")
            img.save(thumbnail_path, "JPEG", quality=85, optimize=True)

            # Return relative path for HTML
            return f"thumbnails/{notice_id}.jpg"

    except Exception as e:
        print(f"Warning: Failed to generate thumbnail for notice {notice_id}: {e}")
        return None


def generate_rss_description(notice):
    """Generate a rich RSS description with structured fields and full text."""
    parts = []

    # Add short description
    if notice.get('description'):
        parts.append(notice['description'])
        parts.append('')  # Blank line

    # Add structured details
    if notice.get('amendment_type'):
        parts.append(f"Type: {notice['amendment_type']['name']} ({notice['amendment_type']['code']})")

    if notice.get('meeting_date'):
        parts.append(f"Meeting: {notice['meeting_date']}")

    if notice.get('property_address'):
        parts.append(f"Location: {notice['property_address']}")

    if notice.get('zoning_change'):
        parts.append(f"Zoning: {notice['zoning_change']}")

    if notice.get('parcel_id'):
        parts.append(f"Parcel ID: {notice['parcel_id']}")

    if notice.get('reference_num'):
        parts.append(f"Reference: {notice['reference_num']}")

    # Add full notice text
    if notice.get('notice_text'):
        parts.append('')  # Blank line
        parts.append('--- Full Notice Text ---')
        parts.append(notice['notice_text'])

    return '\n'.join(parts)


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
        item_desc.text = generate_rss_description(notice)

        if notice.get('pub_date_rfc822'):
            pub_date = SubElement(item, 'pubDate')
            pub_date.text = notice['pub_date_rfc822']

        guid = SubElement(item, 'guid', isPermaLink='false')
        guid.text = f"kissimmee-notice-{notice.get('id', hash(notice.get('title', '')))}"

        # Add thumbnail as enclosure if available
        if notice.get('thumbnail_url'):
            # Use full URL for RSS
            thumbnail_full_url = f"https://kissimmee.fyi/{notice['thumbnail_url']}"
            enclosure = SubElement(item, 'enclosure',
                                  url=thumbnail_full_url,
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

    # Normalize notice text by unescaping HTML entities
    normalized_text = notice_text
    if notice_text:
        prev_text = None
        while prev_text != normalized_text:
            prev_text = normalized_text
            normalized_text = html.unescape(normalized_text)

    # Extract structured fields from notice text
    meeting_date = extract_meeting_date(normalized_text) if normalized_text else None
    property_address = extract_property_address(normalized_text) if normalized_text else None
    zoning_change = extract_zoning_change(normalized_text) if normalized_text else None
    reference_num = extract_reference_number(normalized_text) if normalized_text else None
    parcel_id = extract_parcel_id(normalized_text) if normalized_text else None
    amendment_type = extract_amendment_type(reference_num) if reference_num else None

    # Generate concise description
    short_desc = generate_short_description(normalized_text, property_address, zoning_change, reference_num)

    # Build title from reference number or use default
    if reference_num:
        title = f"{reference_num}"
        if property_address:
            title += f" - {property_address}"
    else:
        title = f"{subcategory}" if subcategory else "Public Notice"
        if city:
            title += f" - {city}"

    # Full description for RSS/details
    description = short_desc

    # Build link to notice detail page if available
    link = None
    if notice_data.get('_links', {}).get('self', {}).get('href'):
        href = notice_data['_links']['self']['href']
        link = f"https://floridapublicnotices.com{href}"

    # Extract PDF URL from _links.media.href
    pdf_url = None
    if notice_data.get('_links', {}).get('media', {}).get('href'):
        pdf_url = notice_data['_links']['media']['href']

    # Extract image URL (if it's an actual URL, not just "pdf")
    image_url = None
    image_field = notice_data.get('image')
    if image_field and image_field != 'pdf' and (image_field.startswith('http://') or image_field.startswith('https://')):
        image_url = image_field

    parsed = {
        'id': notice_id,
        'title': title,
        'description': description,
        'notice_text': normalized_text,
        'pub_date': notice_data.get('date'),
        'pdf_url': pdf_url,
        'link': link,
        'image_url': image_url,
        'thumbnail_url': None,  # Will be set later if thumbnail generation succeeds
        'newspaper': paper,
        'city': city,
        'subcategory': subcategory,
        'meeting_date': meeting_date,
        'property_address': property_address,
        'zoning_change': zoning_change,
        'reference_num': reference_num,
        'parcel_id': parcel_id,
        'amendment_type': amendment_type,
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

    # Thumbnail (if available)
    if notice.get('thumbnail_url'):
        html_parts.append('<div class="notice-thumbnail">')
        if notice.get('pdf_url'):
            html_parts.append(f'<a href="{html.escape(notice["pdf_url"])}" target="_blank">')
            html_parts.append(f'<img src="{html.escape(notice["thumbnail_url"])}" alt="PDF Preview" loading="lazy">')
            html_parts.append('</a>')
        else:
            html_parts.append(f'<img src="{html.escape(notice["thumbnail_url"])}" alt="PDF Preview" loading="lazy">')
        html_parts.append('</div>')

    html_parts.append('<div class="notice-content">')

    # Title with amendment type badge
    html_parts.append('<div class="notice-title">')
    escaped_title = html.escape(notice["title"])
    title_with_abbr = wrap_codes_with_abbr(escaped_title)
    if notice.get('pdf_url'):
        html_parts.append(f'<a href="{html.escape(notice["pdf_url"])}" target="_blank">{title_with_abbr}</a>')
    else:
        html_parts.append(title_with_abbr)

    # Add amendment type badge if available
    if notice.get('amendment_type'):
        amt = notice['amendment_type']
        code_lower = amt['code'].lower()
        html_parts.append(f'<span class="notice-amendment-type {code_lower}" title="{html.escape(amt["name"])}">{html.escape(amt["code"])}</span>')

    html_parts.append('</div>')

    # Meeting date (if extracted)
    if notice.get('meeting_date'):
        html_parts.append(f'<div class="notice-meeting-date">📅 Meeting: {html.escape(notice["meeting_date"])}</div>')

    # Description (normalized by unescaping in parse_notice, re-escape for HTML)
    if notice.get('description'):
        escaped_desc = html.escape(notice["description"])
        desc_with_abbr = wrap_codes_with_abbr(escaped_desc)
        html_parts.append(f'<div class="notice-description">{desc_with_abbr}</div>')

    # Details list for extracted fields
    details = []
    if notice.get('property_address'):
        details.append(f'📍 {html.escape(notice["property_address"])}')
    if notice.get('zoning_change'):
        escaped_zoning = html.escape(notice["zoning_change"])
        zoning_with_abbr = wrap_codes_with_abbr(escaped_zoning)
        details.append(f'🏗️ {zoning_with_abbr}')
    if notice.get('parcel_id'):
        parcel_links = generate_parcel_links(notice['parcel_id'])
        details.append(f'🗂️ Parcel: {parcel_links}')

    if details:
        html_parts.append('<div class="notice-details">')
        html_parts.append('<br>'.join(details))
        html_parts.append('</div>')

    # Publication date
    if notice.get('pub_date_formatted'):
        html_parts.append(f'<div class="notice-pub-date">Published: {html.escape(notice["pub_date_formatted"])}</div>')

    # Links and expand button
    links = []
    if notice.get('pdf_url'):
        links.append(f'<a href="{html.escape(notice["pdf_url"])}" target="_blank">View PDF</a>')
    if notice.get('link'):
        links.append(f'<a href="{html.escape(notice["link"])}" target="_blank">Details</a>')
    if notice.get('notice_text'):
        links.append(f'<a href="#" class="expand-link" onclick="toggleFullText(event, {notice["id"]}); return false;">Show full text</a>')

    if links:
        html_parts.append('<div class="notice-links">')
        html_parts.append(' | '.join(links))
        html_parts.append('</div>')

    # Full text section (hidden by default)
    if notice.get('notice_text'):
        html_parts.append(f'<div id="full-text-{notice["id"]}" class="notice-full-text" style="display: none;">')
        html_parts.append(f'<div class="full-text-content">{html.escape(notice["notice_text"])}</div>')
        html_parts.append('</div>')

    html_parts.append('</div>')  # Close notice-content
    html_parts.append('</div>')  # Close notice

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
        thumbnails_dir = os.path.join(docs_dir, 'thumbnails')
        archive_path = os.path.join(script_dir, 'notices_archive.json')

        # Ensure docs directory exists
        os.makedirs(docs_dir, exist_ok=True)

        # Generate thumbnails for CURRENT notices first (before merging into archive)
        print("Generating PDF thumbnails...")
        for notice in notices:
            if notice.get('pdf_url'):
                thumbnail_url = generate_pdf_thumbnail(
                    notice['pdf_url'],
                    notice['id'],
                    thumbnails_dir
                )
                if thumbnail_url:
                    notice['thumbnail_url'] = thumbnail_url
                    print(f"  Generated thumbnail for notice {notice['id']}")
        print(f"Thumbnail generation complete")

        # Load and merge with archive (thumbnails will be included in merge)
        print("Loading archive...")
        archive = load_archive(archive_path)
        print(f"Archive contains {len(archive.get('notices', {}))} notices before merge")

        archive = merge_notices(archive, notices)
        save_archive(archive, archive_path)

        # Get all archived notices as a list (sorted by date, newest first)
        all_notices = list(archive['notices'].values())
        all_notices.sort(key=lambda n: n.get('pub_date', ''), reverse=True)

        updated_time = datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None)
        if updated_time.tzinfo is None:
            # Fallback for older Python versions
            from datetime import timezone
            updated_time = datetime.now(timezone.utc)

        # Generate main page from current API results only
        template_path = os.path.join(docs_dir, 'template.html')
        html_path = os.path.join(docs_dir, 'index.html')
        generate_static_html(notices, template_path, html_path, updated_time)
        print(f"Generated {html_path}")

        # Generate archive page from all historical notices (without thumbnails)
        # Create copies of notices without thumbnail_url to avoid rendering thumbnails on archive
        archive_notices_no_thumbs = []
        for notice in all_notices:
            notice_copy = notice.copy()
            notice_copy['thumbnail_url'] = None
            archive_notices_no_thumbs.append(notice_copy)

        archive_template_path = os.path.join(docs_dir, 'archive_template.html')
        archive_html_path = os.path.join(docs_dir, 'archive.html')
        generate_static_html(archive_notices_no_thumbs, archive_template_path, archive_html_path, updated_time)
        print(f"Generated {archive_html_path} with {len(all_notices)} total notices")

        # Generate RSS from current API results only
        rss_path = os.path.join(docs_dir, 'rss.xml')
        generate_rss(notices, rss_path)
        print(f"Generated {rss_path}")

        # Clean up orphaned thumbnails (only keep thumbnails for current notices)
        cleanup_thumbnails(thumbnails_dir, notices)

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
