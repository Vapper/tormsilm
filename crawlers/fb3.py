from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
import requests
import pandas as pd
from datetime import datetime
import time

class FacebookGraphAPI:
    def __init__(self, app_id, app_secret, access_token):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.api_version = 'v18.0'  # Current stable version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/"
        
        # Initialize the API
        FacebookAdsApi.init(app_id, app_secret, access_token)

    def get_page_posts(self, page_id, limit=100):
        """Fetch posts from a specific page"""
        endpoint = f"{self.base_url}{page_id}/posts"
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'message,created_time,reactions.summary(total_count),'
                     'comments.summary(total_count),shares'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching page posts: {e}")
            return []

    def get_group_feed(self, group_id, limit=100):
        """Fetch posts from a group"""
        endpoint = f"{self.base_url}{group_id}/feed"
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'message,created_time,reactions.summary(total_count),'
                     'comments.summary(total_count)'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching group feed: {e}")
            return []

    def search_pages(self, query):
        """Search for pages related to a specific query"""
        endpoint = f"{self.base_url}search"
        params = {
            'access_token': self.access_token,
            'q': query,
            'type': 'page',
            'fields': 'id,name,fan_count,category'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error searching pages: {e}")
            return []

    def get_page_insights(self, page_id, metrics):
        """Get insights for a specific page"""
        endpoint = f"{self.base_url}{page_id}/insights"
        params = {
            'access_token': self.access_token,
            'metric': ','.join(metrics),
            'period': 'day'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching page insights: {e}")
            return []


def collect_estonian_weather_data():
    # Initialize with your credentials
    fb_api = FacebookGraphAPI(
        app_id='your_app_id',
        app_secret='your_app_secret',
        access_token='your_access_token'
    )
    
    # Estonian weather-related pages and groups
    weather_sources = {
        'pages': [
            'ilmateenistus',
            'DelfiIlm',
            'weather.estonia'
        ],
        'groups': [
            'eesti.ilm.weather',
            'EstonianWeatherWatchers'
        ]
    }
    
    # Search for weather-related pages in Estonian
    weather_pages = fb_api.search_pages('ilm eesti')
    
    all_data = []
    
    # Collect from known pages
    for page_id in weather_sources['pages']:
        posts = fb_api.get_page_posts(page_id)
        all_data.extend(posts)
        time.sleep(1)  # Rate limiting
        
    # Collect from groups (requires additional permissions)
    for group_id in weather_sources['groups']:
        posts = fb_api.get_group_feed(group_id)
        all_data.extend(posts)
        time.sleep(1)  # Rate limiting
        
    return all_data

def process_weather_data(data):
    """Process and clean the collected weather data"""
    processed_data = []
    
    for post in data:
        if not post.get('message'):
            continue
            
        processed_post = {
            'id': post.get('id'),
            'message': post.get('message'),
            'created_time': post.get('created_time'),
            'reactions_count': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
            'comments_count': post.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares_count': post.get('shares', {}).get('count', 0) if 'shares' in post else 0
        }
        
        processed_data.append(processed_post)
        
    return processed_data

def save_to_database(data, filename):
    """Save processed data to CSV"""
    df = pd.DataFrame(data)
    df.to_csv(f"{filename}_{datetime.now().strftime('%Y%m%d')}.csv", 
             encoding='utf-8-sig',
             index=False)