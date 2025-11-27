#!/usr/bin/env python3
"""
Example usage of the Availability Checker
"""

from availability_checker import AvailabilityChecker

def example_single_check():
    """Example: Single availability check"""
    print("=== EXAMPLE 1: Single Check ===\n")
    
    checker = AvailabilityChecker()
    
    # Replace with your actual product URL
    url = "https://www.example.com/product"
    
    result = checker.check_availability(url)
    
    print(f"Product: {result.get('title', 'Unknown')}")
    print(f"Available: {result.get('available')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Price: {result.get('price', 'Not found')}")
    print()


def example_with_notification():
    """Example: Check with custom notification logic"""
    print("=== EXAMPLE 2: Check with Custom Notification ===\n")
    
    checker = AvailabilityChecker()
    url = "https://www.example.com/product"
    
    result = checker.check_availability(url)
    
    # Custom logic based on result
    if result.get('available'):
        print("🎉 GREAT NEWS! The product is in stock!")
        print(f"Product: {result.get('title')}")
        print(f"Price: {result.get('price')}")
        print(f"Link: {url}")
        # Here you could send an email, SMS, or push notification
    elif result.get('available') is False:
        print("😔 Product is currently out of stock")
        print("We'll keep checking for you...")
    else:
        print("⚠️  Could not determine availability")
        print(f"Confidence: {result.get('confidence')}")
    print()


def example_monitor_multiple_products():
    """Example: Checking multiple products"""
    print("=== EXAMPLE 3: Multiple Products ===\n")
    
    checker = AvailabilityChecker()
    
    products = [
        "https://www.example.com/product1",
        "https://www.example.com/product2",
        "https://www.example.com/product3",
    ]
    
    for i, url in enumerate(products, 1):
        print(f"Checking product {i}/{len(products)}...")
        result = checker.check_availability(url)
        
        status = "✅" if result.get('available') else "❌"
        title = result.get('title', 'Unknown')[:50]
        
        print(f"{status} {title}")
        print(f"   Confidence: {result['confidence']}")
        print()


def example_save_to_log():
    """Example: Saving results to a log file"""
    print("=== EXAMPLE 4: Save Results ===\n")
    
    checker = AvailabilityChecker()
    url = "https://www.example.com/product"
    
    result = checker.check_availability(url)
    checker.save_result(result, "product_checks.json")
    
    print("✅ Result saved to product_checks.json")
    print()


def main():
    print("\n" + "="*60)
    print("AVAILABILITY CHECKER - USAGE EXAMPLES")
    print("="*60 + "\n")
    
    print("Note: Replace example URLs with actual product URLs\n")
    
    # Uncomment the examples you want to run:
    
    # example_single_check()
    # example_with_notification()
    # example_monitor_multiple_products()
    # example_save_to_log()
    
    print("\n💡 TIP: Uncomment the examples in the script to run them")
    print("\nTo monitor a product continuously, use:")
    print('python availability_checker.py "YOUR_URL" --monitor --interval 300')
    print()


if __name__ == "__main__":
    main()
