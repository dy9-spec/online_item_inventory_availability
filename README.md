# Product Availability Checker

A simple but solid system to check product availability from retailer URLs.

## Features

- ✅ Check if a product is in stock or out of stock
- 🔄 Continuous monitoring with customizable intervals
- 📊 Confidence scoring for availability detection
- 💰 Price extraction
- 📝 Save results to JSON log
- 🔔 Alert on status changes

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests beautifulsoup4 lxml
```

## Usage

### Single Check

Check availability once:
```bash
python availability_checker.py "https://example.com/product-url"
```

### Continuous Monitoring

Monitor a product continuously (checks every 5 minutes by default):
```bash
python availability_checker.py "https://example.com/product-url" --monitor
```

Monitor with custom interval (e.g., every 2 minutes):
```bash
python availability_checker.py "https://example.com/product-url" --monitor --interval 120
```

Monitor with maximum number of checks:
```bash
python availability_checker.py "https://example.com/product-url" --monitor --max-checks 10
```

### Save Results

Save check results to a JSON file:
```bash
python availability_checker.py "https://example.com/product-url" --save
```

### Combining Options

Monitor and save results:
```bash
python availability_checker.py "https://example.com/product-url" --monitor --interval 300 --save
```

## How It Works

The system uses multiple strategies to determine availability:

1. **Text Pattern Matching**: Searches for common phrases like "in stock", "out of stock", "add to cart", "sold out"

2. **Button Analysis**: Checks for active "Add to Cart" buttons

3. **Price Detection**: Attempts to extract product price

4. **Confidence Scoring**: 
   - **High**: Clear indicators found (only in-stock or only out-of-stock signals)
   - **Medium**: Mixed signals detected
   - **Low**: No clear indicators found

## Example Output

```
============================================================
AVAILABILITY CHECK RESULT
============================================================
URL: https://example.com/product
Timestamp: 2024-11-27T10:30:45.123456
Product: Amazing Widget - Premium Edition
Status: ✅ IN STOCK
Confidence: high
Price: $299.99
Indicators: ['in stock', 'add to cart', 'active_add_to_cart_button']
============================================================
```

## Monitoring Example

```
Starting monitoring for: https://example.com/product
Check interval: 300 seconds

[Check #1] 2024-11-27 10:30:00
Product: Amazing Widget - Premium Edition
Status: ❌ OUT OF STOCK (Confidence: high)
Price: $299.99
Next check in 300 seconds...

------------------------------------------------------------
[Check #2] 2024-11-27 10:35:00
Product: Amazing Widget - Premium Edition
Status: ✅ IN STOCK (Confidence: high)
Price: $299.99

🔔 STATUS CHANGED! 🔔
Product is now AVAILABLE!

Next check in 300 seconds...
```

## Supported Retailers

The system is designed to work with most major retailers including:
- Amazon
- Best Buy
- Target
- Walmart
- Newegg
- And many more...

The pattern-matching approach adapts to different retailer websites automatically.

## Tips for Best Results

1. **Use direct product URLs**: Avoid URLs with tracking parameters when possible
2. **Adjust check interval**: Balance between responsiveness and server load
3. **Review confidence scores**: Low confidence may require manual verification
4. **Test first**: Do a single check before starting long-term monitoring

## Limitations

- Some retailers use JavaScript to load content dynamically (may require browser automation)
- Rate limiting: Be respectful of retailer servers (default 5-minute interval is recommended)
- CAPTCHA: Some sites may block automated requests
- False positives: In rare cases, mixed signals may occur

## Advanced Usage (Python Library)

You can also use it as a Python library:

```python
from availability_checker import AvailabilityChecker

checker = AvailabilityChecker()

# Single check
result = checker.check_availability("https://example.com/product")
print(f"Available: {result['available']}")
print(f"Confidence: {result['confidence']}")

# Monitor with custom logic
checker.monitor_product(
    url="https://example.com/product",
    check_interval=180,  # 3 minutes
    max_checks=20
)

# Save results
checker.save_result(result, "my_product_log.json")
```

## Troubleshooting

**Problem**: "Failed to fetch page"
- Check your internet connection
- The URL may be incorrect
- The retailer may be blocking automated requests

**Problem**: "Unknown" status with low confidence
- The retailer uses an unusual format
- Content may be loaded dynamically with JavaScript
- Try the URL in a browser to verify it works

**Problem**: Status changes frequently
- This could indicate real stock fluctuations
- Or mixed signals from the page (check indicators)

## Future Enhancements

Possible improvements you could add:
- Email/SMS notifications on status change
- Support for JavaScript-heavy sites (Selenium/Playwright)
- Database storage instead of JSON
- Multi-product monitoring
- Price change tracking
- Browser extension version

## License

Free to use and modify for personal use.
