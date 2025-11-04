# kissimmee.fyi - Project Context for AI Assistants

## Project Overview & Mission

This is a civic technology project aimed at making public information from the City of Kissimmee more accessible to its citizens. Government transparency is essential for civic engagement, but important public information is often scattered across multiple websites, buried in PDFs, or presented in formats that are difficult for ordinary citizens to understand and use.

**Primary Goals:**
- Make public notices, meeting agendas, and minutes easier to find and understand
- Provide contextual information (maps, zoning codes, property data) in one place
- Educate citizens on how to engage with local government processes
- Analyze and present civic data in ways that help residents make informed decisions

**Target Audience:** Residents of Kissimmee, Florida who want to stay informed about local government decisions, especially those affecting land use, zoning, and development.

## About Kissimmee

**Location:** Kissimmee is a city in Osceola County, located in Central Florida, just south of Orlando. It's a diverse, growing community with significant development activity.

**Government Structure:**
- **Planning Advisory Board (PAB):** Reviews and makes recommendations on land use, zoning changes, and development proposals
- **City Commission:** The main legislative body that makes final decisions on city matters
- **Various Departments:** Development Services, Building, Planning, etc.

**Why This Matters:** Land use decisions, zoning changes, and development proposals directly impact neighborhoods, property values, traffic patterns, and quality of life. Citizens have the right to participate in these decisions, but they need timely access to information to do so effectively.

## Current Features

### 1. PAB Public Notices System
The main working feature of the site. It automatically:
- Fetches public notices for Planning Advisory Board meetings from Florida Public Notices
- Parses structured information: addresses, zoning changes, parcel IDs, meeting dates
- Generates PDF thumbnails for visual reference
- Maintains a historical archive
- Provides RSS feed for updates
- Links to property appraiser records
- Adds helpful tooltips for zoning codes and acronyms

**Live Pages:**
- `/pab-notices/` - Current notices with thumbnails
- `/pab-notices/archive.html` - Historical archive
- `/pab-notices/rss.xml` - RSS feed

### 2. Meeting Transcripts Collection
The project maintains a collection of PAB meeting transcripts (`.srt` closed caption files) and markdown summaries dating back to June 2023. This data is stored in `data/pab_meetings/` but not yet displayed on the website.

### 3. Live Site
The site is deployed at **kissimmee.fyi** using GitHub Pages, with automatic updates every 6 hours.

## Planned Features (Roadmap)

From DEVLOG.md and project goals, these features are planned:

1. **Meeting Agendas & Minutes with Better Navigation**
   - Easier access to meeting materials
   - Search and filter by topic/date
   - RSS feeds for new agendas

2. **City Code Access**
   - Land Development Code (LDC) forwarding
   - Make it easy to look up specific ordinances
   - Link code sections directly from notices

3. **Florida Statutes Integration**
   - Quick access to relevant state laws
   - Contextualize how state law affects local decisions

4. **GIS Maps Integration**
   - Visual property/parcel lookup
   - Show zoning overlays
   - Display notices on a map

5. **Civic Education Blog**
   - Explain planning/zoning processes
   - Document how citizens can participate
   - Guide to reading legal notices
   - Analyze development trends

6. **Property Value Analysis**
   - Land tax analysis and trends
   - Compare property assessments
   - Understand development impacts on values

7. **Consolidated City Announcements**
   - Aggregate announcements from various city sources
   - Single place to see what's happening

## Architecture Overview

### Static Site Generation Approach
The site is **fully static HTML** with no server-side code or database. This makes it:
- **Cost-effective:** Free hosting on GitHub Pages
- **Reliable:** No server to crash or database to corrupt
- **Fast:** Just HTML/CSS/JS served by a CDN
- **Archival:** All historical data in git history

### Automation with GitHub Actions
A GitHub Actions workflow (`fetch-notices.yml`) runs every 6 hours to:
1. Fetch latest public notices from Florida Public Notices API
2. Parse and extract structured data
3. Generate PDF thumbnails
4. Update the archive (JSON)
5. Regenerate HTML pages
6. Auto-commit and push changes
7. GitHub Pages automatically deploys the updated site

### Technology Stack
- **Python 3.13:** Data fetching, parsing, HTML generation
- **pdf2image + Pillow:** PDF thumbnail generation
- **requests:** API calls
- **Jinja2-style templates:** HTML generation
- **uv:** Modern Python package manager
- **GitHub Pages:** Static hosting

## Data Sources

### Currently Integrated:
1. **Florida Public Notices API** (`floridapublicnotices.com`)
   - Public notices for Osceola County (code: 49)
   - Searches for "Planning Advisory Board"
   - JSON API with notice details and PDF links

2. **CivicClerk API** (`kissimmeefl.api.civicclerk.com/v1`)
   - Meeting events and schedules
   - Video recordings
   - Closed captions (`.srt` files)
   - Meeting metadata
   - Module implemented: `src/civicclerk.py`

### Planned Data Sources:
- **Municode** (library.municode.com): Land Development Code
- **EnerGov Portal**: Building permits, development applications
- **ArcGIS**: GIS Interactive Map data
- **Comprehensive Plan**: Policy documents (currently on Dropbox)
- **City Website**: News, announcements, calendar

## Project Structure

```
/home/alemi/projects/kissimmee.fyi/
├── src/                          # Python source code
│   ├── update_notices.py         # Main script: fetches & generates PAB notices
│   ├── civicclerk.py            # CivicClerk API client
│   ├── publicnotices.py         # Florida Public Notices API client
│   └── pab_meetings.py          # Meeting transcript collection script
├── docs/                         # Generated static site (served by GitHub Pages)
│   ├── index.html               # Landing page
│   ├── pab-notices/             # PAB notices pages
│   │   ├── index.html           # Current notices
│   │   ├── archive.html         # Historical archive
│   │   └── rss.xml              # RSS feed
│   └── thumbnails/              # PDF thumbnails (auto-cleaned)
├── data/                         # Archived data
│   ├── notices.json             # Historical notices with first_seen/last_seen
│   └── pab_meetings/            # Meeting transcripts and summaries
├── templates/                    # HTML templates
├── .github/workflows/           # GitHub Actions automation
│   └── fetch-notices.yml        # Cron job: runs every 6 hours
├── README.md                    # Basic project description
├── DEVLOG.md                    # Development log and future ideas
└── CLAUDE.md                    # This file - AI assistant context
```

### Key Files:

- **`src/update_notices.py`** (853 lines): The heart of the system. Fetches notices, parses structured data, generates thumbnails, merges with archive, and generates all HTML pages.
- **`data/notices.json`**: Historical archive with first_seen/last_seen timestamps for each notice.
- **`templates/`**: HTML templates used by update_notices.py to generate pages.
- **`florida_statutes.md`**: Guide for accessing Florida Statutes online.

## Development Workflow

### How Updates Happen
1. **Every 6 hours**, GitHub Actions triggers `fetch-notices.yml`
2. Workflow runs `python src/update_notices.py`
3. Script fetches latest notices, updates archive, regenerates HTML
4. If changes detected, auto-commit with message "Update public notices [skip ci]"
5. Push triggers GitHub Pages rebuild
6. Site updates at kissimmee.fyi

### Local Development
```bash
# Install dependencies
uv sync

# Run the main update script
uv run python src/update_notices.py

# Or use standard Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/update_notices.py
```

### Testing Changes
- Generated HTML is written to `docs/`
- Open `docs/index.html` or `docs/pab-notices/index.html` in a browser
- Check that parsing worked correctly, thumbnails generated, etc.

### Adding New Features
1. **New page/data source:**
   - Create a new Python script in `src/`
   - Add to GitHub Actions workflow if it needs automation
   - Generate HTML to `docs/your-feature/`

2. **Improve parsing:**
   - Edit `src/update_notices.py`
   - Focus on the parsing functions that extract structured data
   - Test with `data/notices.json` to ensure backward compatibility

3. **New template:**
   - Add HTML template to `templates/`
   - Update relevant Python script to use new template

## For AI Assistants: Common Tasks

### Understanding the Codebase
- **"Where is X parsed?"** → Look in `src/update_notices.py` around lines 200-600
- **"How are notices fetched?"** → `src/publicnotices.py` and `src/update_notices.py:main()`
- **"Where are pages generated?"** → `src/update_notices.py:generate_*_page()` functions
- **"How do thumbnails work?"** → `src/update_notices.py:generate_thumbnail()` uses pdf2image

### Coding Patterns in This Project
- **Regex parsing:** Extensive use of regex to extract structured data from legal notice text
- **Template strings:** HTML templates with `{{variable}}` placeholders, replaced with `.replace()`
- **JSON archive:** `notices.json` tracks all historical notices with metadata
- **Thumbnail cleanup:** Removes orphaned thumbnails when notices expire
- **Smart abbreviations:** Wraps known codes (zoning, land use) in `<abbr>` tags with tooltips

### Data Flow
```
API → Fetch → Parse → Merge with Archive → Generate HTML → Commit → Deploy
```

### Important Context for Development
- **Legal notices** use inconsistent formats, so parsing is brittle
- **Thumbnails** are only kept for current notices (not archive) to save space
- **Archive dates:** first_seen = when notice first appeared, last_seen = last time it was seen
- **Meeting dates** are parsed from text like "November 21, 2024 at 6:00 PM"
- **Zoning changes** follow pattern "FROM ... TO ..." in notice text
- **Parcel links** go to Osceola County Property Appraiser

### When Helping with This Project
- **Civic impact first:** Remember this helps real people engage with their government
- **Keep it simple:** Static HTML is a feature, not a limitation
- **Document changes:** Update this file or DEVLOG.md when adding features
- **Test with real data:** Use actual notices from `data/notices.json`
- **Preserve history:** Don't break backward compatibility with archive format

## Project Philosophy

This project embodies the belief that **democracy works better when citizens have easy access to information**. Local government decisions often have more direct impact on daily life than state or federal actions, yet local civic engagement is typically low—partly because information is hard to find and understand.

By making public information more accessible, we hope to:
- Increase civic awareness and engagement
- Give citizens tools to participate in decisions that affect them
- Promote government transparency and accountability
- Demonstrate that civic tech can be simple, effective, and sustainable

---

**Last Updated:** 2025-11-04
**Live Site:** https://kissimmee.fyi
**Repository:** (This file is in the root of the project)
