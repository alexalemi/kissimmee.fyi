#!/usr/bin/env python3
"""
One-time migration script to split the existing single notices archive
into category-specific archives based on meeting body classification.
"""
import json
import os
from update_notices import classify_meeting_body


def main():
    """Migrate existing archive to category-specific archives."""
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    old_archive_path = os.path.join(script_dir, 'notices_archive.json')
    data_dir = os.path.join(project_root, 'data')

    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Check if old archive exists
    if not os.path.exists(old_archive_path):
        print(f"No archive found at {old_archive_path}")
        print("Nothing to migrate.")
        return

    # Load old archive
    print(f"Loading archive from {old_archive_path}...")
    with open(old_archive_path, 'r', encoding='utf-8') as f:
        old_archive = json.load(f)

    old_notices = old_archive.get('notices', {})
    print(f"Found {len(old_notices)} notices in archive")

    # Group notices by category
    categories = {}
    for notice_id, notice in old_notices.items():
        notice_text = notice.get('notice_text', '')

        # Classify the notice
        category_key, category_name = classify_meeting_body(notice_text)

        # Add category fields to notice if not present
        if 'meeting_body_key' not in notice:
            notice['meeting_body_key'] = category_key
        if 'meeting_body_name' not in notice:
            notice['meeting_body_name'] = category_name

        # Group by category
        if category_key not in categories:
            categories[category_key] = {
                'name': category_name,
                'notices': {}
            }

        categories[category_key]['notices'][notice_id] = notice

    print(f"\nFound {len(categories)} categories:")
    for cat_key, cat_data in categories.items():
        print(f"  {cat_data['name']} ({cat_key}): {len(cat_data['notices'])} notices")

    # Save each category to its own archive
    for category_key, category_data in categories.items():
        new_archive_path = os.path.join(data_dir, f'notices_{category_key}.json')

        # Create new archive structure
        new_archive = {
            'last_updated': old_archive.get('last_updated'),
            'notices': category_data['notices']
        }

        # Save
        with open(new_archive_path, 'w', encoding='utf-8') as f:
            json.dump(new_archive, f, indent=2, ensure_ascii=False)

        print(f"\nCreated {new_archive_path}")
        print(f"  Contains {len(category_data['notices'])} notices")

    # Create backup of old archive
    backup_path = old_archive_path + '.backup'
    print(f"\nCreating backup of old archive at {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(old_archive, f, indent=2, ensure_ascii=False)

    print("\nMigration complete!")
    print("Old archive backed up to:", backup_path)
    print("New category-specific archives created in:", data_dir)


if __name__ == '__main__':
    main()
