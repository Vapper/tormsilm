from classifiers.news_classifier import NewsEventClassifier
import pytest

def test_financial_extraction():
    classifier = NewsEventClassifier()
    
    # Test cases with expected results
    test_cases = [
        {
            'text': 'Tormikahjustuste suurus oli 1.5 miljonit eurot.',
            'expected': {
                'amount': 1_500_000,
                'currency': 'EUR',
                'confidence': 0.9
            }
        },
        {
            'text': 'Kindlustushüvitise summa oli 500000€.',
            'expected': {
                'amount': 500_000,
                'currency': 'EUR',
                'confidence': 0.9
            }
        },
        {
            'text': 'Kahju ulatus üle 2,5 miljoni euro.',
            'expected': {
                'amount': 2_500_000,
                'currency': 'EUR',
                'confidence': 0.9
            }
        },
        {
            'text': 'Elektrilevi hindab kahjustuste suuruseks ligi 800 tuhat eurot.',
            'expected': {
                'amount': 800_000,
                'currency': 'EUR',
                'confidence': 0.9
            }
        },
        {
            'text': 'Tormist põhjustatud kahju on hinnanguliselt 50000 eurot.',
            'expected': {
                'amount': 50_000,
                'currency': 'EUR',
                'confidence': 0.9
            }
        }
    ]
    
    print("\nTesting Financial Damage Extraction:")
    print("-" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input text: {case['text']}")
        
        # Get classification
        result = classifier.extract_severity(case['text'])
        financial_damage = result.get('financial_damage')
        
        print("\nExtracted Result:")
        print(f"Financial Damage: {financial_damage}")
        
        # Verify results
        assert financial_damage is not None, "Failed to extract financial damage"
        assert financial_damage['currency'] == case['expected']['currency'], \
            f"Currency mismatch: got {financial_damage['currency']}, expected {case['expected']['currency']}"
        assert abs(financial_damage['amount'] - case['expected']['amount']) < 0.01, \
            f"Amount mismatch: got {financial_damage['amount']}, expected {case['expected']['amount']}"
        assert abs(financial_damage['confidence'] - case['expected']['confidence']) < 0.01, \
            f"Confidence mismatch: got {financial_damage['confidence']}, expected {case['expected']['confidence']}"
        
        # Check severity scale based on amount
        if financial_damage['amount'] >= 1_000_000:
            assert result['scale'] == 'major', \
                f"Expected 'major' scale for amount {financial_damage['amount']}"
        elif financial_damage['amount'] >= 100_000:
            assert result['scale'] in ['major', 'moderate'], \
                f"Expected at least 'moderate' scale for amount {financial_damage['amount']}"

def test_edge_cases():
    classifier = NewsEventClassifier()
    
    edge_cases = [
        # No financial information
        'Torm põhjustas palju kahju.',
        
        # Invalid number format
        'Kahju suurus oli kolm miljonit eurot.',
        
        # Mixed units
        'Kahju oli 1.5 miljonit ja 500 tuhat eurot.',
        
        # Multiple currencies (should take first valid match)
        'Kahju oli 100000€ või 120000 dollarit.',
        
        # Negative amounts (should be ignored)
        'Kahju ei ületanud -500000 eurot.'
    ]
    
    print("\nTesting Edge Cases:")
    print("-" * 60)
    
    for i, text in enumerate(edge_cases, 1):
        print(f"\nEdge Case {i}:")
        print(f"Input text: {text}")
        
        result = classifier.extract_severity(text)
        financial_damage = result.get('financial_damage')
        
        print(f"Financial Damage: {financial_damage}")
        
        if i == 1:  # No financial information
            assert financial_damage is None, \
                "Should not extract financial damage when no valid amount is present"

def test_combined_severity():
    classifier = NewsEventClassifier()
    
    # Test case with multiple severity indicators
    text = """Torm jättis 15000 klienti elektrita. 
              Kahjustuste kogumaht ulatus 2.5 miljoni euroni. 
              Elektrikatkestus kestis mõnes piirkonnas kuni 3 päeva."""
    
    print("\nTesting Combined Severity Indicators:")
    print("-" * 60)
    print(f"Input text: {text}")
    
    result = classifier.extract_severity(text)
    print("\nExtracted Result:")
    print(f"Scale: {result['scale']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Affected Customers: {result['affected_customers']}")
    print(f"Financial Damage: {result['financial_damage']}")
    print(f"Duration: {result['duration']}")
    
    # Verify combined severity assessment
    assert result['scale'] == 'major', "Expected 'major' scale due to multiple severe indicators"
    assert result['confidence'] > 0.9, "Expected high confidence due to multiple indicators"

if __name__ == "__main__":
    try:
        test_financial_extraction()
        test_edge_cases()
        test_combined_severity()
        print("\nAll tests passed successfully! ✅")
    except AssertionError as e:
        print(f"\nTest failed! ❌\nError: {str(e)}")
