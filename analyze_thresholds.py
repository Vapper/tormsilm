from classifiers.relevance_classifier import WeatherRelevanceClassifier
import json
from typing import Dict, List, Tuple
from collections import defaultdict

def analyze_confidence_distribution(input_file: str):
    """
    Analyze the confidence score distribution of articles and their relevance.
    """
    # Initialize classifier
    classifier = WeatherRelevanceClassifier()
    
    # Read input data
    print(f"Reading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # Store results for different confidence levels
    confidence_buckets = defaultdict(list)
    confidence_thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    # Process articles
    print(f"Analyzing {len(articles)} articles...")
    for article in articles:
        # Get classification
        result = classifier.classify(article.get('text', ''))
        
        if result['relevant']:
            confidence = result['confidence']
            # Store article info in appropriate buckets
            for threshold in confidence_thresholds:
                if confidence >= threshold:
                    confidence_buckets[threshold].append({
                        'date': article['date'],
                        'url': article['url'],
                        'confidence': confidence,
                        'categories': result['categories']
                    })
    
    # Print analysis
    print("\nConfidence Threshold Analysis:")
    print("-" * 60)
    
    for threshold in confidence_thresholds:
        articles = confidence_buckets[threshold]
        print(f"\nThreshold ≥ {threshold}:")
        print(f"Number of relevant articles: {len(articles)}")
        
        # Calculate average confidence
        if articles:
            avg_confidence = sum(a['confidence'] for a in articles) / len(articles)
            print(f"Average confidence: {avg_confidence:.2f}")
        
        # Analyze categories at this threshold
        categories = defaultdict(int)
        for article in articles:
            for cat in article['categories']:
                categories[cat['name']] += 1
        
        if categories:
            print("\nCategory distribution:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"- {cat}: {count}")
    
    # Sample analysis of borderline cases
    print("\nSample Borderline Cases (0.55 - 0.65 confidence):")
    print("-" * 60)
    
    borderline_cases = [
        article for article in confidence_buckets[0.5] 
        if 0.55 <= article['confidence'] <= 0.65
    ]
    
    for case in borderline_cases[:5]:  # Show first 5 examples
        print(f"\nURL: {case['url']}")
        print(f"Confidence: {case['confidence']}")
        print("Categories:", [cat['name'] for cat in case['categories']])
    
    # Recommend threshold
    recommend_threshold(confidence_buckets)

def recommend_threshold(confidence_buckets: Dict[float, List[Dict]]):
    """
    Analyze the results and recommend an optimal confidence threshold.
    """
    print("\nThreshold Recommendation Analysis:")
    print("-" * 60)
    
    thresholds = sorted(confidence_buckets.keys())
    changes = []
    
    for i in range(len(thresholds) - 1):
        current_count = len(confidence_buckets[thresholds[i]])
        next_count = len(confidence_buckets[thresholds[i + 1]])
        difference = current_count - next_count
        percentage = (difference / current_count * 100) if current_count > 0 else 0
        
        changes.append({
            'threshold': thresholds[i + 1],
            'articles_dropped': difference,
            'percentage_dropped': percentage
        })
    
    print("\nImpact of increasing threshold:")
    for change in changes:
        print(f"\nFrom {change['threshold']-0.1} to {change['threshold']}:")
        print(f"Articles dropped: {change['articles_dropped']}")
        print(f"Percentage dropped: {change['percentage_dropped']:.1f}%")
    
    # Find optimal threshold based on drop rates
    optimal = next(
        (change for change in changes 
         if change['percentage_dropped'] < 30 and change['articles_dropped'] < 50),
        changes[0]
    )
    
    print(f"\nRecommended confidence threshold: {optimal['threshold']}")
    print("Reasoning:")
    print(f"- At this threshold, the drop in articles ({optimal['percentage_dropped']:.1f}%) ")
    print("  is reasonable while maintaining good quality results")
    print(f"- {len(confidence_buckets[optimal['threshold']])} articles would be classified as relevant")

if __name__ == "__main__":
    input_file = "r_proto/data/err_viker_uudised_2023_transcript.json"
    analyze_confidence_distribution(input_file)
