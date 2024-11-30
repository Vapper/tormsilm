from news_classifier import NewsEventClassifier, process_news_file
import json

def format_location(loc):
    return f"{loc['name']} ({loc['type']}, confidence: {loc['confidence']:.1f})"

def format_damage(damage):
    return f"{damage['type']} (confidence: {damage['confidence']:.1f})"

def format_duration(duration):
    if duration:
        return f"{duration['value']} {duration['unit']} (confidence: {duration['confidence']:.1f})"
    return "Not specified"

# Test the classifier with sample data
if __name__ == "__main__":
    file_path = "r_proto/data/err_viker_uudised_2023_transcript_sample.json"
    results = process_news_file(file_path)
    
    # Print results in a readable format
    for result in results:
        print("\nArticle Date:", result['date'])
        print("URL:", result['url'])
        
        # Print locations
        print("\nLocations:")
        for loc in result['classification']['locations']:
            print(f"- {format_location(loc)}")
        
        # Print severity
        severity = result['classification']['severity']
        print("\nSeverity:")
        print(f"- Scale: {severity['scale']}")
        print(f"- Affected customers: {severity['affected_customers'] or 'Not specified'}")
        print(f"- Duration: {format_duration(severity['duration'])}")
        print(f"- Confidence: {severity['confidence']:.1f}")
        
        # Print damage types
        print("\nDamage Types:")
        for damage in result['classification']['damage_types']:
            print(f"- {format_damage(damage)}")
        
        print("-" * 80)
