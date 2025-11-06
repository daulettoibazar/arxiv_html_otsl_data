from bs4 import BeautifulSoup
import os
import re


html_folder = "table_html"

# Tags to exclude from extraction
excluded_tags = {'table', 'caption', 'tr', 'td', 'thead', 'tbody'}

# Set to store all unique tags found
all_tags = set()

html_files = os.listdir(html_folder)
for html_file in html_files:
    print(f"\nProcessing file: {html_file}")
    with open(os.path.join(html_folder, html_file), "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        
        # Find all tags in the file
        all_elements = soup.find_all()
        
        # Extract unique tag names for this file
        file_tags = set()
        for element in all_elements:
            tag_name = element.name
            if tag_name and tag_name not in excluded_tags:
                file_tags.add(tag_name)
                all_tags.add(tag_name)
        
        # Print tags found in this file
        if file_tags:
            print(f"  Tags found: {sorted(file_tags)}")
        else:
            print("  No non-table tags found")

# Print summary of all unique tags found across all files
print(f"\n{'='*50}")
print("SUMMARY: All unique tags found across all files:")
print(f"{'='*50}")
if all_tags:
    for tag in sorted(all_tags):
        print(f"  <{tag}>")
else:
    print("No non-table tags found in any files")
    

