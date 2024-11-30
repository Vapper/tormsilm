from typing import Dict, List, Optional
import re

class WeatherRelevanceClassifier:
    def __init__(self):
        # Keywords related to severe weather and its effects
        self.weather_patterns = {
            # Weather conditions
            'severe_weather': {
                'words': [
                    'torm', 'orkaan', 'tugev tuul', 'lumetorm', 'äike', 
                    'paduvihm', 'tugev vihm', 'rahe', 'üleujutus', 'tulvavesi',
                    'tugev lumesadu', 'jäide', 'ekstreemsed ilmastikuolud'
                ],
                'weight': 1.0
            },
            # Infrastructure damage
            'infrastructure_damage': {
                'words': [
                    'elektrikatkestus', 'elektrita', 'vooluta', 'liinid', 
                    'murdunud puu', 'murdunud puud', 'katkenud liin',
                    'katkenud liinid', 'üleujutatud', 'kahjustused',
                    'infrastruktuuri kahjustused', 'teed suletud',
                    'liiklustakistused'
                ],
                'weight': 1.0
            },
            # Emergency services
            'emergency_response': {
                'words': [
                    'päästjad', 'päästeamet', 'häirekeskus', 'evakueerimine',
                    'kriisikomisjon', 'elektrilevi', 'avariibrigaad'
                ],
                'weight': 0.8
            },
            # Impact descriptions
            'impact': {
                'words': [
                    'kahjustada', 'häiritud', 'takistatud', 'ohtlik',
                    'raskendatud', 'katkestus', 'kriis', 'oht', 'hoiatus'
                ],
                'weight': 0.6
            }
        }
        
        # Keywords that might indicate non-relevance
        self.negative_patterns = [
            'spordivõistlus', 'kontsert', 'etendus', 'festival',
            'ilmaennustus', 'ilmateade', 'prognoos', 'kultuurisündmus'
        ]
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {
            category: {
                'patterns': [re.compile(rf'\b{word}\b', re.IGNORECASE) 
                           for word in info['words']],
                'weight': info['weight']
            }
            for category, info in self.weather_patterns.items()
        }
        
        self.compiled_negative_patterns = [
            re.compile(rf'\b{pattern}\b', re.IGNORECASE) 
            for pattern in self.negative_patterns
        ]

    def classify(self, text: str) -> Dict:
        """
        Classify if the text is about severe weather effects.
        Returns a dictionary with classification details.
        """
        if not text:
            return {
                'relevant': False,
                'confidence': 1.0,
                'categories': [],
                'reason': 'Empty text'
            }

        # Check for negative patterns first
        for pattern in self.compiled_negative_patterns:
            if pattern.search(text):
                return {
                    'relevant': False,
                    'confidence': 0.8,
                    'categories': [],
                    'reason': 'Contains non-relevant context'
                }

        # Initialize scores
        category_scores = {}
        matches_found = False
        total_weight = 0
        
        # Check each category
        for category, info in self.compiled_patterns.items():
            category_matches = []
            for pattern in info['patterns']:
                matches = pattern.findall(text.lower())
                if matches:
                    category_matches.extend(matches)
                    matches_found = True
            
            if category_matches:
                score = len(category_matches) * info['weight']
                category_scores[category] = {
                    'score': score,
                    'matches': category_matches
                }
                total_weight += score

        # Calculate confidence and determine relevance
        if not matches_found:
            return {
                'relevant': False,
                'confidence': 0.9,
                'categories': [],
                'reason': 'No relevant patterns found'
            }

        # Calculate normalized scores and overall confidence
        normalized_scores = {}
        for category, info in category_scores.items():
            normalized_score = info['score'] / total_weight if total_weight > 0 else 0
            normalized_scores[category] = {
                'score': normalized_score,
                'matches': info['matches']
            }

        # Determine overall confidence based on number and variety of matches
        num_categories = len([s for s in normalized_scores.values() if s['score'] > 0.1])
        base_confidence = min(0.5 + (num_categories * 0.15), 1.0)
        
        # Adjust confidence based on total matches
        total_matches = sum(len(info['matches']) for info in normalized_scores.values())
        match_confidence = min(0.5 + (total_matches * 0.1), 1.0)
        
        final_confidence = (base_confidence + match_confidence) / 2

        return {
            'relevant': True,
            'confidence': round(final_confidence, 2),
            'categories': [
                {
                    'name': category,
                    'score': round(info['score'], 2),
                    'matches': info['matches']
                }
                for category, info in normalized_scores.items()
                if info['score'] > 0.1  # Only include significant categories
            ],
            'reason': 'Multiple weather-related patterns found' if num_categories > 1 
                     else 'Weather-related patterns found'
        }

def is_weather_relevant(text: str) -> bool:
    """
    Simple helper function that just returns whether the text is relevant.
    """
    classifier = WeatherRelevanceClassifier()
    result = classifier.classify(text)
    return result['relevant']
