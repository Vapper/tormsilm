import spacy
import re
import json
from typing import Dict, List, Optional

class NewsEventClassifier:
    def __init__(self):
        # Load multilingual model
        self.nlp = spacy.load("xx_ent_wiki_sm")
        
        # Define Estonian counties and major cities
        self.locations = {
            'Harjumaa', 'Hiiumaa', 'Ida-Virumaa', 'Jõgevamaa', 'Järvamaa',
            'Läänemaa', 'Lääne-Virumaa', 'Põlvamaa', 'Pärnumaa', 'Raplamaa',
            'Saaremaa', 'Tartumaa', 'Valgamaa', 'Viljandimaa', 'Võrumaa',
            'Tallinn', 'Tartu', 'Pärnu', 'Narva', 'Kohtla-Järve'
        }
        
        # Define damage-related keywords
        self.damage_patterns = {
            'elektrikatkestus': 'power_outage',
            'elektrita': 'power_outage',
            'murdunud': 'fallen_objects',
            'katkenud': 'broken_line',
            'liinid': 'power_lines',
            'raske lumi': 'heavy_snow',
            'tugev lumesadu': 'heavy_snowfall',
            'torm': 'storm',
            'rikked': 'malfunction'
        }

    def extract_severity(self, text: str) -> Dict:
        """Extract severity indicators from text."""
        severity = {
            'affected_customers': None,
            'duration': None,
            'scale': 'unknown'
        }
        
        # Look for numbers of affected customers
        customer_pattern = r'(\d+(?:,\d+)?(?:\s*000)?)\s*(?:klienti|majapidamist|tarbijat)'
        matches = re.findall(customer_pattern, text, re.IGNORECASE)
        if matches:
            try:
                # Convert to integer, handling thousands
                num = matches[0].replace(' ', '').replace(',', '')
                if '000' in num:
                    num = float(num.replace('000', '')) * 1000
                severity['affected_customers'] = int(float(num))
                
                # Determine scale based on number of affected customers
                if severity['affected_customers'] > 10000:
                    severity['scale'] = 'major'
                elif severity['affected_customers'] > 1000:
                    severity['scale'] = 'moderate'
                else:
                    severity['scale'] = 'minor'
            except ValueError:
                pass
        
        return severity

    def extract_locations(self, text: str) -> List[str]:
        """Extract location mentions from text."""
        doc = self.nlp(text)
        locations = set()
        
        # Extract locations using spaCy NER
        for ent in doc.ents:
            if ent.label_ in ['LOC', 'GPE']:
                locations.add(ent.text)
        
        # Add locations from predefined list
        for loc in self.locations:
            if loc.lower() in text.lower():
                locations.add(loc)
        
        return list(locations)

    def extract_damage_types(self, text: str) -> List[str]:
        """Extract damage types from text."""
        damage_types = set()
        text_lower = text.lower()
        
        for pattern, damage_type in self.damage_patterns.items():
            if pattern.lower() in text_lower:
                damage_types.add(damage_type)
        
        return list(damage_types)

    def classify(self, text: str) -> Dict:
        """Classify the news text and extract all relevant information."""
        return {
            'locations': self.extract_locations(text),
            'severity': self.extract_severity(text),
            'damage_types': self.extract_damage_types(text)
        }

def process_news_file(file_path: str) -> List[Dict]:
    """Process a JSON file containing news articles."""
    classifier = NewsEventClassifier()
    results = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)
        
    for article in news_data:
        result = {
            'date': article.get('date'),
            'url': article.get('url'),
            'classification': classifier.classify(article.get('text', ''))
        }
        results.append(result)
    
    return results

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        results = process_news_file(file_path)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Please provide a path to the news JSON file as an argument.")
