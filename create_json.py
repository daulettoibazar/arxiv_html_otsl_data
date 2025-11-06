import os
import json
from tqdm import tqdm

json_data = []

html_files = os.listdir("tables/html")

for html_file in tqdm(html_files):
    entry = { "tex_path": f"tables/tex_files/{html_file.replace('.html', '.tex')}",
        "html_path": f"tables/html/{html_file}",
        "image_path": f"tables/images/{html_file.replace('.html', '.jpeg')}"
    }

    json_data.append(entry)

with open("tables_english_data.json", "w") as json_file:
    json.dump(json_data, json_file, indent=4)
