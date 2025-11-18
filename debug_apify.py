import os
import requests
import json

# Configuration
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', 'mfu46')
APIFY_API_TOKEN = os.environ.get('APIFY_API_TOKEN')

print("=" * 60)
print("APIFY DEBUG SCRIPT")
print("=" * 60)
print(f"Twitter Handle: @{TWITTER_HANDLE}")
print(f"API Token: {'Present' if APIFY_API_TOKEN else 'MISSING'}")
print("=" * 60)

# Apify Actor for Twitter scraping
apify_url = "https://api.apify.com/v2/acts/apidojo~tweet-scraper/run-sync-get-dataset-items"

payload = {
    "handles": [TWITTER_HANDLE],
    "tweetsDesired": 5,  # Just get 5 tweets for debugging
    "proxyConfig": {"useApifyProxy": True}
}

headers = {
    "Content-Type": "application/json"
}

params = {
    "token": APIFY_API_TOKEN
}

try:
    print("\n📡 Sending request to Apify...")
    response = requests.post(apify_url, json=payload, headers=headers, params=params, timeout=120)
    response.raise_for_status()
    tweets = response.json()
    
    print(f"✅ Response received!")
    print(f"📊 Number of items: {len(tweets)}")
    print("=" * 60)
    
    if tweets and len(tweets) > 0:
        print("\n🔍 FIRST TWEET ANALYSIS:")
        print("=" * 60)
        
        first_tweet = tweets[0]
        
        # Print all available keys
        print("\n📝 Available fields:")
        for key in sorted(first_tweet.keys()):
            print(f"  - {key}")
        
        print("\n" + "=" * 60)
        print("🔍 DETAILED FIRST TWEET DATA:")
        print("=" * 60)
        print(json.dumps(first_tweet, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
        print("🎯 KEY FIELDS WE NEED:")
        print("=" * 60)
        
        # Check for various possible field names
        possible_id_fields = ['id', 'id_str', 'tweetId', 'tweet_id', 'rest_id', 'statusId']
        possible_url_fields = ['url', 'tweet_url', 'link', 'permalink']
        possible_text_fields = ['text', 'full_text', 'content', 'tweet_text']
        possible_date_fields = ['createdAt', 'created_at', 'timestamp', 'date']
        
        print("\n🆔 ID Fields:")
        for field in possible_id_fields:
            if field in first_tweet:
                print(f"  ✅ {field}: {first_tweet[field]}")
            else:
                print(f"  ❌ {field}: Not found")
        
        print("\n🔗 URL Fields:")
        for field in possible_url_fields:
            if field in first_tweet:
                print(f"  ✅ {field}: {first_tweet[field]}")
            else:
                print(f"  ❌ {field}: Not found")
        
        print("\n📝 Text Fields:")
        for field in possible_text_fields:
            if field in first_tweet:
                text_preview = str(first_tweet[field])[:50] + "..." if len(str(first_tweet[field])) > 50 else str(first_tweet[field])
                print(f"  ✅ {field}: {text_preview}")
            else:
                print(f"  ❌ {field}: Not found")
        
        print("\n📅 Date Fields:")
        for field in possible_date_fields:
            if field in first_tweet:
                print(f"  ✅ {field}: {first_tweet[field]}")
            else:
                print(f"  ❌ {field}: Not found")
        
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATION:")
        print("=" * 60)
        
        # Provide recommendation
        if 'url' in first_tweet or 'tweet_url' in first_tweet:
            url_field = 'url' if 'url' in first_tweet else 'tweet_url'
            print(f"✅ Use field '{url_field}' for tweet URLs")
        elif 'id' in first_tweet or 'id_str' in first_tweet:
            id_field = 'id' if 'id' in first_tweet else 'id_str'
            print(f"✅ Construct URL from field '{id_field}': https://x.com/{TWITTER_HANDLE}/status/{{id}}")
        else:
            print("⚠️ No clear ID or URL field found. May need alternative approach.")
        
    else:
        print("\n❌ No tweets returned by Apify!")
        print("Possible reasons:")
        print("  - Twitter account has no tweets")
        print("  - Account is private")
        print("  - Apify rate limit reached")
        print("  - Account name is incorrect")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
