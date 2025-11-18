# Blog Posts

This directory contains blog posts written in Markdown format. The `generate_blog.py` script converts these files into static HTML pages.

## Creating a New Post

1. Create a new `.md` file in this directory with a descriptive filename (e.g., `understanding-zoning-codes.md`)

2. Add frontmatter at the top of the file with metadata:

```markdown
---
title: Your Post Title
date: 2025-11-08
author: Your Name (optional)
description: A brief description for SEO and RSS feed
slug: custom-url-slug (optional, defaults to filename)
---

Your markdown content here...
```

3. Write your content using standard Markdown syntax:
   - Use `#` for headings (the title from frontmatter becomes the h1)
   - Use `##` for sections, `###` for subsections
   - Regular Markdown for links, lists, bold, italic, etc.
   - Code blocks with triple backticks
   - Tables, blockquotes, etc.

4. Run the blog generator:

```bash
uv run python src/generate_blog.py
```

5. The script will generate:
   - Individual post page: `docs/blog/your-slug.html`
   - Updated blog index: `docs/blog/index.html`
   - Updated RSS feed: `docs/blog/rss.xml`

## Frontmatter Fields

### Required Fields

- **title**: The post title (displayed as h1 on the page)
- **date**: Publication date in `YYYY-MM-DD` format (used for sorting)

### Optional Fields

- **author**: Author name (displayed in post metadata)
- **description**: Brief description (used for meta tags and RSS feed, defaults to auto-generated excerpt)
- **slug**: Custom URL slug (defaults to filename converted to lowercase with hyphens)

## Example Post

```markdown
---
title: How to Read Planning Advisory Board Agendas
date: 2025-11-08
author: kissimmee.fyi
description: A practical guide to understanding PAB meeting agendas and participating effectively.
---

Planning Advisory Board meetings can seem complex, but understanding the agenda is key to effective participation...

## What's on a PAB Agenda?

Each PAB meeting agenda typically includes:

- **Call to order** and roll call
- **Public comment** period
- **Old business** from previous meetings
- **New business** including applications for review

...
```

## Supported Markdown Features

The blog system uses Python-Markdown with these extensions:

- **extra**: Tables, fenced code blocks, footnotes, attribute lists
- **nl2br**: Converts newlines to `<br>` tags
- **sane_lists**: Better list handling

### Common Markdown Syntax

```markdown
# Heading 1
## Heading 2
### Heading 3

**bold text**
*italic text*
[link text](https://example.com)

- Unordered list item
- Another item

1. Ordered list item
2. Another item

> Blockquote

`inline code`

\```
code block
\```

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |
```

## Best Practices

1. **Use descriptive filenames**: They become URLs (e.g., `understanding-zoning.md` → `/blog/understanding-zoning.html`)
2. **Write clear titles**: They appear in search results and RSS feeds
3. **Add good descriptions**: Helps with SEO and gives readers context
4. **Date posts accurately**: Posts are sorted by date on the blog index
5. **Link to relevant resources**: Include links to city websites, laws, and other references
6. **Keep it accessible**: Write for a general audience, explain technical terms

## Automating Blog Generation

To automatically regenerate the blog when posts change, you can add it to the GitHub Actions workflow:

```yaml
# In .github/workflows/fetch-notices.yml
- name: Generate blog
  run: uv run python src/generate_blog.py
```

This will regenerate the blog pages whenever the workflow runs.

## Viewing Locally

After generating the blog:

1. Open `docs/blog/index.html` in a web browser to see the blog index
2. Click on a post title to view the individual post page
3. The RSS feed is at `docs/blog/rss.xml`

## Content Ideas

The blog is for civic education. Good topics include:

- Explaining zoning codes and land use terminology
- How to participate in public hearings
- Understanding the planning process
- Analyzing development trends
- Guides to city services and resources
- Explaining Florida Statutes relevant to local government
- Case studies of recent development decisions

## Questions?

For questions about the blog system, see `src/generate_blog.py` or contact info@kissimmee.fyi.
