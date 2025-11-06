### latex
import os, re, tempfile
from typing import List, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument, ContentLayer, TableItem


_OTSL_PATTERN = re.compile(r"<otsl>(.*?)</otsl>", re.DOTALL)


def _convert_math_tags_to_latex(soup):
    """
    Convert HTML math-related tags to LaTeX equivalents.
    Handles: <sup>, <sub>, <em>, <i>, <b>, <strong> within table cells.
    """
    # Process all table cells
    for cell in soup.find_all(['td', 'th']):
        _process_node_for_latex(cell)


def _process_node_for_latex(node):
    """
    Recursively process a node and convert math tags to LaTeX.
    """
    if isinstance(node, NavigableString):
        return
    
    # Process children first (depth-first)
    for child in list(node.children):
        if hasattr(child, 'name'):
            _process_node_for_latex(child)
    
    # Convert specific tags
    if node.name == 'sup':
        # <sup>2</sup> -> ^{2}
        content = node.get_text()
        node.replace_with(f"$^{{{content}}}$")
    
    elif node.name == 'sub':
        # <sub>i</sub> -> _{i}
        content = node.get_text()
        node.replace_with(f"$_{{{content}}}$")
    
    elif node.name in ['em', 'i']:
        # <em>x</em> -> x (no formatting)
        content = node.get_text()
        node.replace_with(content)
    
    elif node.name in ['b', 'strong']:
        # <b>R</b> -> R (no formatting)
        content = node.get_text()
        node.replace_with(content)
    
    elif node.name == 'span':
        # Check for common math classes
        classes = node.get('class', [])
        if any(c in ['math', 'formula', 'equation'] for c in classes):
            content = node.get_text()
            # Wrap in inline math mode
            node.replace_with(f"${content}$")


def html_to_otsl_enhanced_latex(html: Optional[str] = None, html_path: Optional[str] = None) -> List[str]:
    """
    Use Docling to export tables to OTSL, but first:
    1. Convert math-related HTML tags to LaTeX
    2. Move thead/tfoot rows into tbody (so Docling processes them correctly)
    3. Add caption inside <otsl> at the correct position (top or bottom)
    
    Returns: List of OTSL strings with format: 
        <otsl><caption>...</caption>...</otsl> (caption at top)
        <otsl>...<caption>...</caption></otsl> (caption at bottom)
    """
    if (html is None) == (html_path is None):
        raise ValueError("Provide exactly one of `html` or `html_path`.")

    # Read HTML content
    original_html = html
    if html_path is not None:
        with open(html_path, 'r', encoding='utf-8') as f:
            original_html = f.read()

    # Parse HTML
    soup = BeautifulSoup(original_html, 'html.parser')
    
    # Convert math tags to LaTeX FIRST
    _convert_math_tags_to_latex(soup)
    html_tables = soup.find_all('table')
    
    # Store captions and their positions (True = top, False = bottom)
    table_captions: List[Tuple[str, bool]] = []
    
    for table in html_tables:
        # Extract caption text and position
        caption = table.find('caption')
        caption_text = ""
        caption_at_top = True  # Default to top
        
        if caption:
            caption_text = caption.get_text(strip=True)
            # Determine position: check if caption comes before tbody/thead/tfoot
            caption_index = list(table.children).index(caption)
            first_data_element = table.find(['thead', 'tbody', 'tfoot', 'tr'])
            if first_data_element:
                data_index = list(table.children).index(first_data_element)
                caption_at_top = caption_index < data_index
        
        table_captions.append((caption_text, caption_at_top))
        
        # Get or create tbody
        tbody = table.find('tbody')
        if not tbody:
            tbody = soup.new_tag('tbody')
            table.append(tbody)
        
        # Move thead rows to the beginning of tbody
        thead = table.find('thead')
        if thead:
            thead_rows = thead.find_all('tr', recursive=False)
            for tr in reversed(thead_rows):  # Insert in reverse to maintain order
                tbody.insert(0, tr.extract())
            thead.decompose()  # Remove empty thead
        
        # Move tfoot rows to the end of tbody
        tfoot = table.find('tfoot')
        if tfoot:
            tfoot_rows = tfoot.find_all('tr', recursive=False)
            for tr in tfoot_rows:
                tbody.append(tr.extract())
            tfoot.decompose()  # Remove empty tfoot

    # Convert normalized HTML back to string
    normalized_html = str(soup)

    # Create temporary file for Docling conversion
    tmp_path = None
    fd, tmp_path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(normalized_html)

    # Use Docling to convert HTML
    conv = DocumentConverter()
    result = None
    err = None
    
    try:
        if hasattr(conv, "convert"):
            result = conv.convert(Path(str(tmp_path)))
    except Exception as e:
        err = e
    if result is None:
        try:
            if hasattr(conv, "convert_file"):
                result = conv.convert_file(str(tmp_path))
        except Exception as e:
            err = e
    if result is None:
        try:
            with open(str(tmp_path), "rb") as f:
                data = f.read()
            if hasattr(conv, "convert_bytes"):
                result = conv.convert_bytes(data, mime_type="text/html")
        except Exception as e:
            err = e
    
    if result is None:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise AttributeError(f"Could not convert HTML with DocumentConverter. Last error: {err}")

    doc: DoclingDocument = getattr(result, "document", result)

    # Extract OTSL from Docling
    otsl_blocks = []
    for node, _ in doc.iterate_items(
        with_groups=False,
        traverse_pictures=False,
        page_no=None,
        included_content_layers={ContentLayer.BODY, ContentLayer.FURNITURE},
    ):
        if isinstance(node, TableItem):
            try:
                doctags = node.export_to_doctags(doc, add_location=False)
            except TypeError:
                doctags = node.export_to_doctags(doc)
            
            m = _OTSL_PATTERN.search(doctags)
            if m:
                otsl_content = m.group(1) 
                # Content inside <otsl>...</otsl>
                # Clean up the content: remove newlines, text tags, unicode spaces, and consecutive $$
                cleaned_content = (otsl_content
                                 .replace('\n', '')
                                 .replace('<text>', '')
                                 .replace('</text>', '')
                                 .replace('\u2004', '')  # Three-Per-Em Space
                                 .replace('\u2005', '')  # Four-Per-Em Space
                                 .replace('\u2006', '')  # Six-Per-Em Space
                                 .replace('\u2007', '')  # Figure Space
                                 .replace('\u2008', '')  # Punctuation Space
                                 .replace('\u2009', '')  # Thin Space
                                 .replace('\u200A', '')  # Hair Space
                                 .replace('\u202F', '')  # Narrow No-Break Space
                                 .replace('\u205F', '')  # Medium Mathematical Space
                                 .replace('\u3000', '')  # Ideographic Space
                                 ) 
                # Remove consecutive $$ (double dollar signs)
                cleaned_content = re.sub(r'\$\$+', '', cleaned_content)
                otsl_blocks.append(cleaned_content)

    # Clean up temp file
    if tmp_path and os.path.exists(tmp_path):
        os.remove(tmp_path)

    # Add captions to OTSL blocks at the correct position
    enhanced_results = []
    
    for idx, otsl_content in enumerate(otsl_blocks):
        if idx < len(table_captions):
            caption_text, caption_at_top = table_captions[idx]
            
            if caption_text and '<caption>' not in otsl_content:
                caption_text = caption_text.replace("\n", " ")
                caption_tag = f"<caption>{caption_text}</caption>"
                if caption_at_top:
                    enhanced_results.append(f"<otsl>{caption_tag}{otsl_content}</otsl>")
                else:
                    enhanced_results.append(f"<otsl>{otsl_content}{caption_tag}</otsl>")
            else:
                enhanced_results.append(f"<otsl>{otsl_content}</otsl>")
        else:
            enhanced_results.append(f"<otsl>{otsl_content}</otsl>")

    return enhanced_results