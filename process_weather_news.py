from classifiers.relevance_classifier import WeatherRelevanceClassifier
from classifiers.news_classifier import NewsEventClassifier
import json
from typing import Dict, List
from datetime import datetime

def process_news_dataset(input_file: str, output_file: str, min_confidence: float = 0.6):
    """
    Process news articles with both relevance and detailed classification.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        min_confidence: Minimum confidence threshold for relevance (default: 0.6)
    """
    # Initialize classifiers
    relevance_classifier = WeatherRelevanceClassifier()
    news_classifier = NewsEventClassifier()
    
    # Read input data
    print(f"Reading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # Process articles
    results = []
    relevant_count = 0
    total_count = len(articles)
    
    print(f"Processing {total_count} articles...")
    for idx, article in enumerate(articles, 1):
        if idx % 100 == 0:
            print(f"Processed {idx}/{total_count} articles...")
        
        # First check relevance
        relevance = relevance_classifier.classify(article.get('text', ''))
        
        # If article is relevant with sufficient confidence, perform detailed classification
        if relevance['relevant'] and relevance['confidence'] >= min_confidence:
            detailed_classification = news_classifier.classify(article.get('text', ''))
            relevant_count += 1
            
            result = {
                'date': article.get('date'),
                'url': article.get('url'),
                'relevance': relevance,
                'classification': detailed_classification
            }
            results.append(result)
    
    # Sort results by date
    results.sort(key=lambda x: x['date'] if x['date'] else '')
    
    # Generate summary statistics
    summary = {
        'total_articles': total_count,
        'relevant_articles': relevant_count,
        'relevance_rate': round(relevant_count / total_count * 100, 2),
        'processing_date': datetime.now().isoformat(),
        'confidence_threshold': min_confidence
    }
    
    # Save results
    output_data = {
        'summary': summary,
        'results': results
    }
    
    print(f"\nSaving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total articles processed: {total_count}")
    print(f"Relevant articles found: {relevant_count}")
    print(f"Relevance rate: {summary['relevance_rate']}%")
    print(f"Results saved to: {output_file}")

def analyze_results(results_file: str):
    """
    Analyze the processed results and print interesting statistics.
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data['summary']
    results = data['results']
    
    print("\nDetailed Analysis:")
    print("-" * 40)
    
    # General statistics
    print("\nGeneral Statistics:")
    print(f"Total articles analyzed: {summary['total_articles']}")
    print(f"Weather-related articles: {summary['relevant_articles']}")
    print(f"Relevance rate: {summary['relevance_rate']}%")
    
    # Analyze locations
    locations = {}
    for result in results:
        for loc in result['classification']['locations']:
            name = loc['name']
            if name in locations:
                locations[name] += 1
            else:
                locations[name] = 1
    
    print("\nTop 10 Most Mentioned Locations:")
    sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]
    for loc, count in sorted_locations:
        print(f"- {loc}: {count} mentions")
    
    # Analyze damage types
    damage_types = {}
    for result in results:
        for damage in result['classification']['damage_types']:
            damage_type = damage['type']
            if damage_type in damage_types:
                damage_types[damage_type] += 1
            else:
                damage_types[damage_type] = 1
    
    print("\nDamage Types Distribution:")
    sorted_damages = sorted(damage_types.items(), key=lambda x: x[1], reverse=True)
    for damage, count in sorted_damages:
        print(f"- {damage}: {count} occurrences")

if __name__ == "__main__":
    input_file = "r_proto/data/err_viker_uudised_2023_transcript.json"
    output_file = "r_proto/data/weather_classified_news_2023.json"
    
    # Process the dataset
    process_news_dataset(input_file, output_file, min_confidence=0.65)
    
    # Analyze results
    analyze_results(output_file)
