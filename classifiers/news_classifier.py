import spacy
import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class NewsEventClassifier:
    def __init__(self):
        # Load multilingual model
        self.nlp = spacy.load("xx_ent_wiki_sm")
        
        # Define Estonian counties and major cities with variations
        self.locations = {
            'Harjumaa': ['Harjumaa', 'Harjumaale', 'Harjumaalt', 'Harju'],
            'Hiiumaa': ['Hiiumaa', 'Hiiumaale', 'Hiiumaalt', 'Hiiu'],
            'Ida-Virumaa': ['Ida-Virumaa', 'Ida-Virumaale', 'Ida-Virumaalt', 'Ida-Viru'],
            'Jõgevamaa': ['Jõgevamaa', 'Jõgevamaale', 'Jõgevamaalt', 'Jõgeva'],
            'Järvamaa': ['Järvamaa', 'Järvamaale', 'Järvamaalt', 'Järva'],
            'Läänemaa': ['Läänemaa', 'Läänemaale', 'Läänemaalt', 'Lääne'],
            'Lääne-Virumaa': ['Lääne-Virumaa', 'Lääne-Virumaale', 'Lääne-Virumaalt', 'Lääne-Viru'],
            'Põlvamaa': ['Põlvamaa', 'Põlvamaale', 'Põlvamaalt', 'Põlva'],
            'Pärnumaa': ['Pärnumaa', 'Pärnumaale', 'Pärnumaalt', 'Pärnu'],
            'Raplamaa': ['Raplamaa', 'Raplamaale', 'Raplamaalt', 'Rapla'],
            'Saaremaa': ['Saaremaa', 'Saaremaale', 'Saaremaalt', 'Saare'],
            'Tartumaa': ['Tartumaa', 'Tartumaale', 'Tartumaalt', 'Tartu'],
            'Valgamaa': ['Valgamaa', 'Valgamaale', 'Valgamaalt', 'Valga'],
            'Viljandimaa': ['Viljandimaa', 'Viljandimaale', 'Viljandimaalt', 'Viljandi'],
            'Võrumaa': ['Võrumaa', 'Võrumaale', 'Võrumaalt', 'Võru'],
        }
        
        # Regional terms
        self.regions = {
            'Põhja-Eesti': ['Põhja-Eesti', 'Põhja-Eestis', 'Põhja-Eestisse'],
            'Lõuna-Eesti': ['Lõuna-Eesti', 'Lõuna-Eestis', 'Lõuna-Eestisse'],
            'Ida-Eesti': ['Ida-Eesti', 'Ida-Eestis', 'Ida-Eestisse'],
            'Lääne-Eesti': ['Lääne-Eesti', 'Lääne-Eestis', 'Lääne-Eestisse'],
            'Kagu-Eesti': ['Kagu-Eesti', 'Kagu-Eestis', 'Kagu-Eestisse'],
            'Kirde-Eesti': ['Kirde-Eesti', 'Kirde-Eestis', 'Kirde-Eestisse'],
        }
        
        # Words to exclude from location detection
        self.location_stopwords = {
            'aga', 'aastal', 'igal', 'tähendab', 'vahter', 'kuigi', 'läinud', 'nädalavahetusel'
        }
        
        # Define damage-related keywords with confidence scores
        self.damage_patterns = {
            'elektrikatkestus': {'type': 'power_outage', 'confidence': 1.0},
            'elektrita': {'type': 'power_outage', 'confidence': 1.0},
            'vooluta': {'type': 'power_outage', 'confidence': 1.0},
            'elektrivarustus': {'type': 'power_outage', 'confidence': 0.8},
            'murdunud puu': {'type': 'fallen_trees', 'confidence': 1.0},
            'murdunud puud': {'type': 'fallen_trees', 'confidence': 1.0},
            'puu murdus': {'type': 'fallen_trees', 'confidence': 1.0},
            'puud murdusid': {'type': 'fallen_trees', 'confidence': 1.0},
            'katkenud liin': {'type': 'broken_line', 'confidence': 1.0},
            'katkenud liinid': {'type': 'broken_line', 'confidence': 1.0},
            'liinirikked': {'type': 'power_lines', 'confidence': 0.9},
            'elektriliinid': {'type': 'power_lines', 'confidence': 0.8},
            'raske lumi': {'type': 'heavy_snow', 'confidence': 1.0},
            'tugev lumesadu': {'type': 'heavy_snowfall', 'confidence': 1.0},
            'lumetorm': {'type': 'snow_storm', 'confidence': 1.0},
            'torm': {'type': 'storm', 'confidence': 0.9},
            'tormikahjustused': {'type': 'storm_damage', 'confidence': 1.0},
            'rikked': {'type': 'malfunction', 'confidence': 0.7},
            'üleujutus': {'type': 'flooding', 'confidence': 1.0},
            'tulvavesi': {'type': 'flooding', 'confidence': 0.9},
        }

        # Duration patterns
        self.duration_patterns = [
            (r'(?:veel\s)?(\d+)\s*(?:päeva|päev)', 'days'),
            (r'(?:veel\s)?(\d+)\s*(?:tundi|tund)', 'hours'),
            (r'(?:veel\s)?(\d+)\s*(?:minutit|minut)', 'minutes'),
        ]

        # Financial damage patterns
        self.financial_patterns = [
            # Euro amounts with decimals
            (r'(\d+(?:[.,]\d+)?)\s*(?:miljonit?)?\s*(?:tuhat?)?\s*(?:euro[t]?|€)', 'EUR'),
            # Thousands/millions with words
            (r'(?:umbes|ligi|üle|kokku)\s*(\d+(?:[.,]\d+)?)\s*(?:miljonit?|tuhat?)\s*(?:euro[t]?|€)', 'EUR'),
            # Damage cost mentions
            (r'(?:kahju|kahjustuste)\s*(?:suurus|maht)\s*(?:on|oli)\s*(\d+(?:[.,]\d+)?)\s*(?:miljonit?)?\s*(?:tuhat?)?\s*(?:euro[t]?|€)', 'EUR'),
            # Insurance claims
            (r'kindlustushüvitis[e]?\s*(?:summa|maht)\s*(?:on|oli)\s*(\d+(?:[.,]\d+)?)\s*(?:miljonit?)?\s*(?:tuhat?)?\s*(?:euro[t]?|€)', 'EUR')
        ]

    def extract_severity(self, text: str) -> Dict:
        """Extract severity indicators from text."""
        severity = {
            'affected_customers': None,
            'duration': None,
            'financial_damage': None,
            'scale': 'unknown',
            'confidence': 0.0
        }
        
        # Look for numbers of affected customers
        customer_patterns = [
            r'(\d+(?:,\d+)?(?:\s*000)?)\s*(?:klienti|majapidamist|tarbijat)',
            r'(?:umbes|ligi|üle|kokku)\s*(\d+(?:,\d+)?(?:\s*000)?)\s*(?:klienti|majapidamist|tarbijat)',
        ]
        
        for pattern in customer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Convert to integer, handling thousands
                    num = matches[0].replace(' ', '').replace(',', '')
                    if '000' in num:
                        num = float(num.replace('000', '')) * 1000
                    severity['affected_customers'] = int(float(num))
                    severity['confidence'] = max(severity['confidence'], 1.0)
                    
                    # Determine scale based on number of affected customers
                    if severity['affected_customers'] > 10000:
                        severity['scale'] = 'major'
                    elif severity['affected_customers'] > 1000:
                        severity['scale'] = 'moderate'
                    else:
                        severity['scale'] = 'minor'
                    break
                except ValueError:
                    continue

        # Extract financial damage
        for pattern, currency in self.financial_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Clean and convert the number
                    num = matches[0].replace(' ', '').replace(',', '.')
                    value = float(num)
                    
                    # Handle millions and thousands
                    if 'miljon' in text.lower():
                        value *= 1_000_000
                    elif 'tuhat' in text.lower():
                        value *= 1_000
                    
                    severity['financial_damage'] = {
                        'amount': value,
                        'currency': currency,
                        'confidence': 0.9
                    }
                    
                    # Update overall severity scale based on financial damage
                    if value >= 1_000_000:  # Over 1M EUR
                        severity['scale'] = 'major'
                        severity['confidence'] = max(severity['confidence'], 0.9)
                    elif value >= 100_000:  # Over 100K EUR
                        if severity['scale'] != 'major':
                            severity['scale'] = 'moderate'
                        severity['confidence'] = max(severity['confidence'], 0.8)
                    break
                except ValueError:
                    continue
        
        # Extract duration
        duration_info = self.extract_duration(text)
        if duration_info:
            severity['duration'] = duration_info
            
            # Update confidence based on duration
            if duration_info['value'] > 48 and severity['scale'] != 'major':  # Over 48 hours
                severity['scale'] = 'moderate'
                severity['confidence'] = max(severity['confidence'], 0.7)
        
        return severity

    def extract_duration(self, text: str) -> Optional[Dict]:
        """Extract duration information from text."""
        for pattern, unit in self.duration_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    value = int(matches[0])
                    return {
                        'value': value,
                        'unit': unit,
                        'confidence': 0.9
                    }
                except ValueError:
                    continue
        return None

    def extract_locations(self, text: str) -> List[Dict]:
        """Extract location mentions from text."""
        doc = self.nlp(text)
        locations = []
        seen = set()
        
        # First, check for regions
        for region, variants in self.regions.items():
            for variant in variants:
                if variant.lower() in text.lower() and region not in seen:
                    locations.append({
                        'name': region,
                        'type': 'region',
                        'confidence': 0.9
                    })
                    seen.add(region)
        
        # Then check for counties and their variations
        for county, variants in self.locations.items():
            for variant in variants:
                if variant.lower() in text.lower() and county not in seen:
                    locations.append({
                        'name': county,
                        'type': 'county',
                        'confidence': 1.0
                    })
                    seen.add(county)
        
        # Add locations from NER that aren't in stopwords
        for ent in doc.ents:
            if (ent.label_ in ['LOC', 'GPE'] and 
                ent.text.lower() not in self.location_stopwords and 
                ent.text not in seen):
                locations.append({
                    'name': ent.text,
                    'type': 'other',
                    'confidence': 0.7
                })
                seen.add(ent.text)
        
        return locations

    def extract_damage_types(self, text: str) -> List[Dict]:
        """Extract damage types from text."""
        damage_types = []
        text_lower = text.lower()
        seen = set()
        
        for pattern, info in self.damage_patterns.items():
            if pattern.lower() in text_lower and info['type'] not in seen:
                damage_types.append({
                    'type': info['type'],
                    'confidence': info['confidence']
                })
                seen.add(info['type'])
        
        return damage_types

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
