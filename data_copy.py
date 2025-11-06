import json
from tqdm import tqdm
import shutil
import os
with open("tables_english_data.json", "r") as f:
    data = json.load(f)

source_path = "/mnt/s3/vision/dtoibazar/arxiv_data_english"
html_path = "table_html"
image_path = "table_images"
tex_path = "table_tex"

for entry in tqdm(data[:500]):
    shutil.copy(f"{source_path}/{entry['html_path']}", os.path.join(html_path, os.path.basename(entry['html_path'])))
    shutil.copy(f"{source_path}/{entry['image_path']}", os.path.join(image_path, os.path.basename(entry['image_path'])))
    shutil.copy(f"{source_path}/{entry['tex_path']}", os.path.join(tex_path, os.path.basename(entry['tex_path'])))
