# Florida Statutes Access Guide

## Overview
This guide provides instructions for accessing specific sections of the Florida Statutes using available tools.

## Primary Method: Florida Senate Website

### URL Pattern
The most reliable method for accessing Florida Statutes is through the Florida Senate website using the following URL pattern:

```
https://www.flsenate.gov/Laws/Statutes/[YEAR]/[STATUTE_NUMBER]
```

### Parameters
- **YEAR**: The year of the statutes (e.g., 2025, 2024)
- **STATUTE_NUMBER**: The statute section number in the format `XXXX.XX` (e.g., 0270.10, 163.3161)

### Examples
- Florida Statute Â§270.10 (2025): `https://www.flsenate.gov/Laws/Statutes/2025/0270.10`
- Florida Statute Â§163.3161 (2025): `https://www.flsenate.gov/Laws/Statutes/2025/163.3161`
- Florida Statute Â§112.501 (2025): `https://www.flsenate.gov/Laws/Statutes/2025/112.501`

## Usage Instructions

### When to Use
Use the `web_fetch` tool to access Florida Statutes when:
- You need the current text of a specific statute
- The user references a Florida Statute by number
- You need to verify statute language or details
- The statute is not already available in project files

### How to Use
1. Identify the statute number from the user's query
2. Construct the URL using the pattern above
3. Use the `web_fetch` tool with the constructed URL
4. Extract and present the relevant statute text

### Example Implementation
```
User asks: "What does Florida Statute 270.10 say?"

Step 1: Identify statute number: 270.10
Step 2: Construct URL: https://www.flsenate.gov/Laws/Statutes/2025/0270.10
Step 3: Call web_fetch with the URL
Step 4: Extract and summarize the statute content
```

## Alternative Sources

### Florida Legislature Website
The official legislature website (`www.leg.state.fl.us`) is less reliable for programmatic access due to JavaScript rendering limitations. Use the Florida Senate website instead.

### Project Knowledge
Before fetching statutes from the web, check if relevant statutes are already available in the project files. Several Florida Statutes are already included in this project's knowledge base.

## Best Practices

1. **Check Project Files First**: Always search project knowledge before fetching from the web
2. **Use Current Year**: Default to the most recent year (2025) unless the user specifies otherwise
3. **Format Statute Numbers Correctly**: Ensure leading zeros are included (e.g., 0270.10, not 270.10)
4. **Cite Sources**: When presenting statute text, always include the statute number and year
5. **Handle Errors Gracefully**: If a fetch fails, try alternative sources or inform the user

## Common Florida Statutes in Project Context

The following statutes are already available in project files:
- Florida Statute 112.501 - Municipal board members; suspension; removal
- Florida Statute 163.3161 - Community Planning Act
- Florida Statute 163.3174 - Local Planning Agency

## Troubleshooting

### Issue: URL Returns No Content
- Verify the statute number format (include leading zeros)
- Check that the statute exists for the specified year
- Try an alternative year if the current year returns no results

### Issue: Statute Not Found
- Verify the statute number is correct
- Check if the statute has been repealed or renumbered
- Search project knowledge for related statutes

## Notes
- The Florida Senate website provides clean, accessible text without requiring JavaScript
- Statute content includes the full text, related links, and bill citations
- Always verify you're accessing the correct year's version of the statute
