from news_classifier import NewsEventClassifier, process_news_file
import json

# Test the classifier with sample data
if __name__ == "__main__":
    file_path = "r_proto/data/err_viker_uudised_2023_transcript_sample.json"
    results = process_news_file(file_path)
    
    # Print results in a readable format
    for result in results:
        print("\nArticle Date:", result['date'])
        print("URL:", result['url'])
        print("Locations:", result['classification']['locations'])
        print("Severity:", result['classification']['severity'])
        print("Damage Types:", result['classification']['damage_types'])
        print("-" * 50)
