import facebook_scraper
import requests
import pandas as pd
from datetime import datetime

class FacebookWeatherCollector:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0/"
        
    def get_group_posts(self, group_id, limit=100):
        endpoint = f"{self.base_url}{group_id}/feed"
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'message,created_time,reactions.summary(total_count),comments.summary(total_count)'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json().get('data', [])
        except Exception as e:
            print(f"Viga postituste kogumisel: {e}")
            return []

    def search_pages(self, query):
        endpoint = f"{self.base_url}search"
        params = {
            'access_token': self.access_token,
            'q': query,
            'type': 'page',
            'fields': 'id,name,fan_count'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json().get('data', [])
        except Exception as e:
            print(f"Viga lehtede otsingul: {e}")
            return []