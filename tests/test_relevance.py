from classifiers.relevance_classifier import WeatherRelevanceClassifier
import json

def test_with_sample():
    # Load sample data
    sample_file = "r_proto/data/err_viker_uudised_2023_transcript_sample.json"
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # Initialize classifier
    classifier = WeatherRelevanceClassifier()
    
    # Process each article
    for article in articles:
        print("\nArticle Date:", article['date'])
        print("URL:", article['url'])
        
        # Get classification
        result = classifier.classify(article.get('text', ''))
        
        # Print results
        print("\nRelevance Classification:")
        print(f"Relevant: {result['relevant']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Reason: {result['reason']}")
        
        if result['categories']:
            print("\nDetected Categories:")
            for category in result['categories']:
                print(f"\n- {category['name']}:")
                print(f"  Score: {category['score']}")
                print(f"  Matches: {', '.join(category['matches'])}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_with_sample()
