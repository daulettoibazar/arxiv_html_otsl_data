#!/usr/bin/env python3
"""
Script to remove HTML files with issues and their corresponding .jpeg and .tex files.

Checks HTML files for:
- More than one <caption> tag
- More than one <tbody> tag

If issues are found, removes the HTML file and corresponding files in other directories.
"""

import os
import sys
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('html_removal.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Set up directory paths."""
    base_dir = Path(__file__).parent
    html_dir = base_dir / "tables" / "html"
    images_dir = base_dir / "tables" / "images"
    tex_dir = base_dir / "tables" / "tex_files"
    
    return html_dir, images_dir, tex_dir

def check_html_issues(html_file_path):
    """
    Check if HTML file has issues.
    
    Args:
        html_file_path (Path): Path to HTML file
        
    Returns:
        tuple: (has_issues, issues_list)
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        issues = []
        
        # Check for multiple <caption> tags
        captions = soup.find_all('caption')
        if len(captions) > 1:
            issues.append(f"Multiple <caption> tags found: {len(captions)}")
        
        # Check for multiple <tbody> tags
        tbodies = soup.find_all('tbody')
        if len(tbodies) > 1:
            issues.append(f"Multiple <tbody> tags found: {len(tbodies)}")
        
        return len(issues) > 0, issues
    
    except Exception as e:
        logger.error(f"Error reading {html_file_path}: {e}")
        return False, []

def get_corresponding_files(html_file_path, images_dir, tex_dir):
    """
    Get corresponding .jpeg and .tex files for the HTML file.
    
    Args:
        html_file_path (Path): Path to HTML file
        images_dir (Path): Directory containing image files
        tex_dir (Path): Directory containing tex files
        
    Returns:
        tuple: (jpeg_file_path, tex_file_path) or (None, None) if not found
    """
    html_name = html_file_path.stem  # filename without extension
    
    # Look for corresponding .jpeg file
    jpeg_file = images_dir / f"{html_name}.jpeg"
    if not jpeg_file.exists():
        jpeg_file = None
    
    # Look for corresponding .tex file
    tex_file = tex_dir / f"{html_name}.tex"
    if not tex_file.exists():
        tex_file = None
    
    return jpeg_file, tex_file

def remove_files(html_file, jpeg_file, tex_file):
    """
    Remove the specified files.
    
    Args:
        html_file (Path): HTML file to remove
        jpeg_file (Path or None): JPEG file to remove
        tex_file (Path or None): TEX file to remove
    """
    removed_files = []
    
    # Remove HTML file
    try:
        html_file.unlink()
        removed_files.append(str(html_file))
        logger.info(f"Removed HTML file: {html_file}")
    except Exception as e:
        logger.error(f"Error removing HTML file {html_file}: {e}")
    
    # Remove JPEG file if it exists
    if jpeg_file and jpeg_file.exists():
        try:
            jpeg_file.unlink()
            removed_files.append(str(jpeg_file))
            logger.info(f"Removed JPEG file: {jpeg_file}")
        except Exception as e:
            logger.error(f"Error removing JPEG file {jpeg_file}: {e}")
    
    # Remove TEX file if it exists
    if tex_file and tex_file.exists():
        try:
            tex_file.unlink()
            removed_files.append(str(tex_file))
            logger.info(f"Removed TEX file: {tex_file}")
        except Exception as e:
            logger.error(f"Error removing TEX file {tex_file}: {e}")
    
    return removed_files

def main():
    """Main function to process HTML files and remove problematic ones."""
    logger.info("Starting HTML file processing...")
    
    # Setup directories
    html_dir, images_dir, tex_dir = setup_directories()
    
    # Check if directories exist
    if not html_dir.exists():
        logger.error(f"HTML directory not found: {html_dir}")
        return
    
    if not images_dir.exists():
        logger.warning(f"Images directory not found: {images_dir}")
    
    if not tex_dir.exists():
        logger.warning(f"TEX directory not found: {tex_dir}")
    
    # Get all HTML files
    html_files = list(html_dir.glob("*.html"))
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Statistics
    total_processed = 0
    total_with_issues = 0
    total_removed = 0
    
    # Process each HTML file
    for html_file in tqdm(html_files):
        total_processed += 1
        logger.debug(f"Processing: {html_file.name}")
        
        # Check for issues
        has_issues, issues = check_html_issues(html_file)
        
        if has_issues:
            total_with_issues += 1
            logger.warning(f"Issues found in {html_file.name}: {'; '.join(issues)}")
            
            # Get corresponding files
            jpeg_file, tex_file = get_corresponding_files(html_file, images_dir, tex_dir)
            
            # Log what will be removed
            files_to_remove = [str(html_file)]
            if jpeg_file:
                files_to_remove.append(str(jpeg_file))
            if tex_file:
                files_to_remove.append(str(tex_file))
            
            logger.info(f"Removing files: {', '.join(files_to_remove)}")
            
            # Remove files
            removed_files = remove_files(html_file, jpeg_file, tex_file)
            total_removed += len(removed_files)
        
        # Progress update every 100 files
        if total_processed % 100 == 0:
            logger.info(f"Progress: {total_processed}/{len(html_files)} files processed")
    
    # Final statistics
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total HTML files processed: {total_processed}")
    logger.info(f"Files with issues found: {total_with_issues}")
    logger.info(f"Total files removed: {total_removed}")
    logger.info(f"Percentage with issues: {(total_with_issues/total_processed)*100:.2f}%")
    
    if total_with_issues > 0:
        logger.info(f"Check 'html_removal.log' for detailed information about removed files.")

if __name__ == "__main__":
    main()
