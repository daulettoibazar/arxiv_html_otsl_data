## This repo contains utility scripts used to refine Arxiv standalone English and Arabic tables

### Repo strucutre:

* clean_html - clean HTML files in a given directory to compress html files from redundant: \n, \t and extra spaces.
* correct_caption_place.py - places captions in accurate place inside HTML files based on it tex source.
* create_otsl.py - main script that generates otsl formatted tables based on HTML input. Following refinments happen under the hood: replace HTML-specific math notations with latex notations before passing them to converter. Remove any full empty rows from output OTSL files.
* remove_inaccurate_html.py - this script deletes HTML files that contain >1 caption or tbody (caused by pandoc tex-> html conversion for very complex tables)
  
