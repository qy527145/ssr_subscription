import requests
import cloudscraper
from config import *

__all__ = [
    'requests_obj'
]

if get_bool_config('COMMON', 'enable_clouds_scraper', False):
    requests_obj = cloudscraper.create_scraper()
else:
    requests_obj = requests
