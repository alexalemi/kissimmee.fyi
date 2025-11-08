#!/usr/bin/env python3
"""
Generate static blog pages from markdown files.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import html

try:
    import markdown
except ImportError:
    print("Error: markdown library not installed. Run: uv sync")
    exit(1)


POSTS_DIR = Path("posts")
OUTPUT_DIR = Path("docs/blog")
TEMPLATES_DIR = Path("templates")


def parse_frontmatter(content):
    """
    Parse YAML-like frontmatter from markdown content.

    Expected format:
    ---
    title: Post Title
    date: 2025-11-08
    author: Author Name (optional)
    description: Brief description
    slug: custom-url-slug (optional, defaults to filename)
    ---

    Actual markdown content...
    """
    frontmatter = {}

    # Check if content starts with ---
    if not content.startswith('---\n'):
        return frontmatter, content

    # Find the end of frontmatter
    try:
        end_index = content.index('\n---\n', 4)
    except ValueError:
        # No closing ---, treat as no frontmatter
        return frontmatter, content

    # Extract frontmatter section
    fm_section = content[4:end_index]
    remaining_content = content[end_index + 5:].strip()

    # Parse frontmatter lines
    for line in fm_section.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, remaining_content


def markdown_to_html(md_content):
    """Convert markdown to HTML with extensions."""
    md = markdown.Markdown(extensions=[
        'extra',      # Tables, fenced code blocks, etc.
        'nl2br',      # Newlines to <br>
        'sane_lists', # Better list handling
    ])
    return md.convert(md_content)


def generate_slug(filename):
    """Generate URL slug from filename."""
    # Remove .md extension
    slug = filename.replace('.md', '')
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-zA-Z0-9-]', '', slug)
    # Convert to lowercase
    slug = slug.lower()
    return slug


def format_date(date_str):
    """Format date string for display."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date.strftime('%B %d, %Y')
    except ValueError:
        return date_str


def parse_date(date_str):
    """Parse date string to datetime object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return datetime.now()


def extract_excerpt(html_content, max_length=200):
    """Extract plain text excerpt from HTML content."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    return text


def load_template(template_name):
    """Load HTML template."""
    template_path = TEMPLATES_DIR / template_name
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_post_page(post_data):
    """Generate individual blog post HTML page."""
    template = load_template('blog_post.html')

    # Author line (optional)
    author_line = f" | {post_data['author']}" if post_data.get('author') else ""

    # Replace placeholders
    html_content = template.replace('{{TITLE}}', html.escape(post_data['title']))
    html_content = html_content.replace('{{DESCRIPTION}}', html.escape(post_data.get('description', '')))
    html_content = html_content.replace('{{DATE}}', post_data['formatted_date'])
    html_content = html_content.replace('{{AUTHOR}}', author_line)
    html_content = html_content.replace('{{CONTENT}}', post_data['html_content'])

    # Write to file
    output_file = OUTPUT_DIR / f"{post_data['slug']}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated: {output_file}")


def generate_index_page(posts):
    """Generate blog index page with list of posts."""
    template = load_template('blog_index.html')

    # Generate post list HTML
    post_items = []
    for post in posts:
        author_line = f" | {post['author']}" if post.get('author') else ""

        post_html = f"""
			<li>
				<div class="post-title">
					<a href="/blog/{post['slug']}.html">{html.escape(post['title'])}</a>
				</div>
				<div class="post-meta">{post['formatted_date']}{author_line}</div>
				<div class="post-excerpt">{html.escape(post['excerpt'])}</div>
			</li>"""
        post_items.append(post_html)

    posts_html = '\n'.join(post_items)

    # Replace placeholder
    html_content = template.replace('{{POSTS}}', posts_html)

    # Write to file
    output_file = OUTPUT_DIR / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated: {output_file}")


def generate_rss_feed(posts):
    """Generate RSS feed for blog posts."""
    # Create RSS feed
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    # Channel info
    SubElement(channel, 'title').text = 'kissimmee.fyi Blog'
    SubElement(channel, 'link').text = 'https://kissimmee.fyi/blog/'
    SubElement(channel, 'description').text = 'Civic education and insights about Kissimmee, Florida'
    SubElement(channel, 'language').text = 'en-us'

    # Add posts
    for post in posts[:10]:  # Include last 10 posts in RSS
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = post['title']
        SubElement(item, 'link').text = f"https://kissimmee.fyi/blog/{post['slug']}.html"
        SubElement(item, 'description').text = post.get('description', post['excerpt'])
        SubElement(item, 'pubDate').text = post['date_obj'].strftime('%a, %d %b %Y 00:00:00 GMT')
        SubElement(item, 'guid').text = f"https://kissimmee.fyi/blog/{post['slug']}.html"

    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss, encoding='unicode')).toprettyxml(indent='  ')

    # Write to file
    output_file = OUTPUT_DIR / 'rss.xml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)

    print(f"Generated: {output_file}")


def main():
    """Main function to generate blog."""
    print("Generating blog from markdown files...")

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Find all markdown files in posts directory
    if not POSTS_DIR.exists():
        print(f"Error: Posts directory '{POSTS_DIR}' does not exist.")
        return

    md_files = list(POSTS_DIR.glob('*.md'))

    if not md_files:
        print(f"No markdown files found in '{POSTS_DIR}'.")
        print("Create markdown files with frontmatter like:")
        print("""
---
title: My First Post
date: 2025-11-08
author: Your Name
description: A brief description of the post
---

Your markdown content here...
""")
        return

    print(f"Found {len(md_files)} post(s)")

    # Parse all posts
    posts = []
    for md_file in md_files:
        print(f"Processing: {md_file.name}")

        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter, md_content = parse_frontmatter(content)

        # Require title and date
        if 'title' not in frontmatter:
            print(f"  Warning: No title in frontmatter, skipping {md_file.name}")
            continue
        if 'date' not in frontmatter:
            print(f"  Warning: No date in frontmatter, skipping {md_file.name}")
            continue

        # Convert markdown to HTML
        html_content = markdown_to_html(md_content)

        # Generate slug
        slug = frontmatter.get('slug', generate_slug(md_file.stem))

        # Parse and format date
        date_obj = parse_date(frontmatter['date'])
        formatted_date = format_date(frontmatter['date'])

        # Extract excerpt
        excerpt = frontmatter.get('description', extract_excerpt(html_content))

        # Create post data
        post_data = {
            'title': frontmatter['title'],
            'date': frontmatter['date'],
            'date_obj': date_obj,
            'formatted_date': formatted_date,
            'author': frontmatter.get('author'),
            'description': frontmatter.get('description', ''),
            'slug': slug,
            'html_content': html_content,
            'excerpt': excerpt,
            'filename': md_file.name,
        }

        posts.append(post_data)

        # Generate individual post page
        generate_post_page(post_data)

    if not posts:
        print("No valid posts to generate.")
        return

    # Sort posts by date (newest first)
    posts.sort(key=lambda p: p['date_obj'], reverse=True)

    # Generate index page
    generate_index_page(posts)

    # Generate RSS feed
    generate_rss_feed(posts)

    print(f"\nBlog generation complete! Generated {len(posts)} post(s).")
    print(f"View at: docs/blog/index.html")


if __name__ == '__main__':
    main()
