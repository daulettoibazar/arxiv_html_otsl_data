from utils import html_to_otsl_enhanced_latex
import os
import re
from tqdm import tqdm


def clean_empty_cell_lines(otsl: str) -> str:
    """
    Remove lines that contain only <ecel><ecel><nl> after </caption>, <nl>, or <otsl>.
    
    Example:
    <caption>Table 1: table</caption><ecel><ecel><nl><fcel>23<fcel>25<nl>
    becomes:
    <caption>Table 1: table</caption><fcel>23<fcel>25<nl>
    
    Pattern to match:
    - (</caption>|<nl>|<otsl>) followed by <ecel><ecel><nl>
    """
    # Pattern: match (</caption>|<nl>|<otsl>) followed by one or more <ecel> and then <nl>
    pattern = r'(</caption>|<nl>|<otsl>)(<ecel>)+<nl>'
    
    # Replace with just the capture group (</caption>|<nl>|<otsl>)
    cleaned = re.sub(pattern, r'\1', otsl)
    
    return cleaned

html_files = os.listdir("../html")

for html_file in tqdm(html_files):
    html_path = os.path.join("../html", html_file)
    otsl_list = html_to_otsl_enhanced_latex(html_path=html_path)
    if len(otsl_list) ==1:
        otsl = otsl_list[0]

        # Clean empty cell lines
        otsl = clean_empty_cell_lines(otsl)

        otsl_file_name = "../otsl/" + html_file.replace(".html", ".otsl")
        with open(otsl_file_name, "w") as f:
            f.write(otsl)
    else:
        print(f"File {html_file} produced {len(otsl_list)} OTSL entries.")
        exit(1)
    