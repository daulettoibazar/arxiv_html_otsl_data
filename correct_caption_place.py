#!/usr/bin/env python3
"""
Script to correct caption placement in HTML files based on corresponding TEX files.

This script:
1. Iterates over HTML files that contain <caption> tags
2. Reads the corresponding TEX file to determine caption placement
3. Adjusts HTML structure to match TEX caption placement (before or after table content)
"""

import os
import sys
import re
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('caption_correction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Set up directory paths."""
    base_dir = Path(__file__).parent
    html_dir = base_dir / "tables" / "html"
    tex_dir = base_dir / "tables" / "tex_files"
    
    return html_dir, tex_dir

def get_caption_position_from_tex(tex_file_path):
    """
    Determine caption position in TEX file relative to tabular environment.
    
    Args:
        tex_file_path (Path): Path to TEX file
        
    Returns:
        str: 'before' if caption comes before tabular, 'after' if after, 'none' if no caption
    """
    try:
        with open(tex_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Strip LaTeX comments (unescaped %)
        content = re.sub(r'(?<!\\)%.*', '', content)
        
        # Find positions of \caption and tabular environments
        # Support optional short caption: \caption[short]{long}
        # (Keep simple and robust)
        caption_pattern = r'\\caption(?:\[[^\]]*\])?\s*\{'
        # Match any of common table-like environments
        tabular_pattern = r'\\begin\{(tabular|tabularx|longtable|array)\}'
        
        caption_match = re.search(caption_pattern, content)
        if not caption_match:
            return 'none'
        
        caption_pos = caption_match.start()
        
        # Find the earliest tabular environment
        tabular_match = re.search(tabular_pattern, content)
        tabular_pos = tabular_match.start() if tabular_match else None
        
        if tabular_pos is None:
            logger.warning(f"No tabular environment found in {tex_file_path}")
            return 'none'
        
        # Compare positions
        if caption_pos < tabular_pos:
            return 'before'
        else:
            return 'after'
    
    except Exception as e:
        logger.error(f"Error reading TEX file {tex_file_path}: {e}")
        return 'none'

def has_caption_in_html(html_file_path):
    """
    Check if HTML file has a caption tag.
    
    Args:
        html_file_path (Path): Path to HTML file
        
    Returns:
        bool: True if has caption, False otherwise
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        captions = soup.find_all('caption')
        
        return len(captions) > 0
    
    except Exception as e:
        logger.error(f"Error reading HTML file {html_file_path}: {e}")
        return False

def correct_caption_placement(html_file_path, caption_position):
    """
    Correct caption placement in HTML file based on desired position.
    
    Args:
        html_file_path (Path): Path to HTML file
        caption_position (str): 'before' or 'after'
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the table and caption
        table = soup.find('table')
        if not table:
            logger.warning(f"No table found in {html_file_path}")
            return False
        
        captions = table.find_all('caption')
        if len(captions) == 0:
            logger.warning(f"No caption found in {html_file_path}")
            return False
        
        if len(captions) > 1:
            logger.warning(f"Multiple captions found in {html_file_path}, skipping")
            return False
        
        caption = captions[0]
        
        # Determine current position based on direct child tag order only
        current_position = 'unknown'
        direct_tag_children = [c for c in table.children if isinstance(c, Tag)]
        
        try:
            cap_idx = direct_tag_children.index(caption)
            if cap_idx == 0:
                current_position = 'before'
            elif cap_idx == len(direct_tag_children) - 1:
                current_position = 'after'
            else:
                current_position = 'middle'
        except ValueError:
            # Caption is not a direct child; treat as unknown and move explicitly
            current_position = 'unknown'
        
        # If already in correct position, no change needed
        if current_position == caption_position:
            logger.debug(f"Caption already in correct position ({caption_position}) for {html_file_path}")
            return False
        
        # Move caption to correct position (idempotent and robust)
        caption.extract()  # Remove from current position
        if caption_position == 'before':
            # Insert at the very beginning of the table contents
            table.insert(0, caption)
        else:  # caption_position == 'after'
            # Append at the end of the table contents
            table.append(caption)
        
        # Write back to file
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logger.info(f"Moved caption from {current_position} to {caption_position} in {html_file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error correcting caption placement in {html_file_path}: {e}")
        return False

def get_corresponding_tex_file(html_file_path, tex_dir):
    """
    Get corresponding TEX file for the HTML file.
    
    Args:
        html_file_path (Path): Path to HTML file
        tex_dir (Path): Directory containing tex files
        
    Returns:
        Path or None: Path to TEX file if found, None otherwise
    """
    html_name = html_file_path.stem  # filename without extension
    tex_file = tex_dir / f"{html_name}.tex"
    
    if tex_file.exists():
        return tex_file
    else:
        return None

def main():
    """Main function to process HTML files and correct caption placement."""
    logger.info("Starting caption placement correction...")
    
    # Setup directories
    html_dir, tex_dir = setup_directories()
    
    # Check if directories exist
    if not html_dir.exists():
        logger.error(f"HTML directory not found: {html_dir}")
        return
    
    if not tex_dir.exists():
        logger.error(f"TEX directory not found: {tex_dir}")
        return
    
    # Get all HTML files
    html_files = list(html_dir.glob("*.html"))
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Statistics
    total_processed = 0
    total_with_captions = 0
    total_corrected = 0
    caption_position_stats = {'before': 0, 'after': 0, 'none': 0}
    
    # Process each HTML file
    for html_file in tqdm(html_files, desc="Processing HTML files"):
        total_processed += 1
        logger.debug(f"Processing: {html_file.name}")
        
        # Check if HTML has caption
        if not has_caption_in_html(html_file):
            logger.debug(f"No caption found in {html_file.name}, skipping")
            continue
        
        total_with_captions += 1
        
        # Get corresponding TEX file
        tex_file = get_corresponding_tex_file(html_file, tex_dir)
        if not tex_file:
            logger.warning(f"No corresponding TEX file found for {html_file.name}")
            continue
        
        # Determine caption position from TEX
        caption_position = get_caption_position_from_tex(tex_file)
        caption_position_stats[caption_position] += 1
        
        if caption_position == 'none':
            logger.warning(f"No caption found in TEX file {tex_file.name}")
            continue
        
        # Correct caption placement in HTML
        was_corrected = correct_caption_placement(html_file, caption_position)
        if was_corrected:
            total_corrected += 1
        
        # Progress update every 100 files
        if total_processed % 100 == 0:
            logger.info(f"Progress: {total_processed}/{len(html_files)} files processed")
    
    # Final statistics
    logger.info("=" * 60)
    logger.info("CAPTION CORRECTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total HTML files processed: {total_processed}")
    logger.info(f"HTML files with captions: {total_with_captions}")
    logger.info(f"Files corrected: {total_corrected}")
    logger.info(f"Caption positions in TEX files:")
    logger.info(f"  - Before tabular: {caption_position_stats['before']}")
    logger.info(f"  - After tabular: {caption_position_stats['after']}")
    logger.info(f"  - No caption found: {caption_position_stats['none']}")
    
    if total_corrected > 0:
        logger.info(f"Check 'caption_correction.log' for detailed information about corrections.")

if __name__ == "__main__":
    main()
