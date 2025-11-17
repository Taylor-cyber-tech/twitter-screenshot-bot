import os
import smtplib
import json
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import requests

# Configuration from environment variables
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', 'elonmusk')  # Default for testing
YOUR_EMAIL = os.environ.get('YOUR_EMAIL')
YOUR_EMAIL_PASSWORD = os.environ.get('YOUR_EMAIL_PASSWORD')  # Gmail App Password
APIFY_API_TOKEN = os.environ.get('APIFY_API_TOKEN')

def get_recent_tweets(username, hours=12):
    """
    Fetch tweets from the last X hours using Apify Twitter Scraper
    """
    print(f"Fetching tweets from @{username} in the last {hours} hours...")
    
    # Apify Actor for Twitter scraping (free tier: 100 requests/month)
    apify_url = "https://api.apify.com/v2/acts/apidojo~tweet-scraper/run-sync-get-dataset-items"
    
    # Calculate time threshold
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    payload = {
        "handles": [username],
        "tweetsDesired": 50,  # Get more tweets to filter by time
        "proxyConfig": {"useApifyProxy": True}
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "token": APIFY_API_TOKEN
    }
    
    try:
        response = requests.post(apify_url, json=payload, headers=headers, params=params, timeout=120)
        response.raise_for_status()
        tweets = response.json()
        
        # Filter tweets by time
        recent_tweets = []
        for tweet in tweets:
            tweet_time = datetime.strptime(tweet.get('createdAt', ''), '%a %b %d %H:%M:%S %z %Y')
            # Remove timezone info for comparison
            tweet_time = tweet_time.replace(tzinfo=None)
            
            if tweet_time >= time_threshold:
                recent_tweets.append({
                    'id': tweet.get('id'),
                    'text': tweet.get('text'),
                    'url': f"https://twitter.com/{username}/status/{tweet.get('id')}",
                    'created_at': tweet.get('createdAt'),
                    'likes': tweet.get('likes', 0),
                    'retweets': tweet.get('retweets', 0)
                })
        
        print(f"Found {len(recent_tweets)} tweets in the last {hours} hours")
        return recent_tweets
        
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return []

def take_screenshot(url, filename):
    """
    Take a screenshot of a tweet using Playwright
    """
    print(f"Taking screenshot of {url}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1200, 'height': 800})
            page = context.new_page()
            
            # Go to the tweet URL
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for tweet to load
            time.sleep(3)
            
            # Try to find the tweet element and screenshot it
            try:
                # Twitter's article element contains the tweet
                tweet_element = page.locator('article').first
                tweet_element.screenshot(path=filename)
            except:
                # Fallback: screenshot the whole page
                page.screenshot(path=filename, full_page=False)
            
            browser.close()
            print(f"Screenshot saved: {filename}")
            return True
            
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False

def send_email(tweets, screenshots):
    """
    Send email with tweet screenshots
    """
    print(f"Sending email to {YOUR_EMAIL}...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = YOUR_EMAIL
    msg['To'] = YOUR_EMAIL
    msg['Subject'] = f"Twitter Updates: @{TWITTER_HANDLE} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Email body
    body = f"""
    <html>
    <body>
        <h2>Recent Tweets from @{TWITTER_HANDLE}</h2>
        <p>Found {len(tweets)} tweets in the last 12 hours:</p>
        <hr>
    """
    
    for i, tweet in enumerate(tweets, 1):
        body += f"""
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
            <h3>Tweet #{i}</h3>
            <p><strong>Posted:</strong> {tweet['created_at']}</p>
            <p><strong>Text:</strong> {tweet['text']}</p>
            <p><strong>Likes:</strong> {tweet['likes']} | <strong>Retweets:</strong> {tweet['retweets']}</p>
            <p><a href="{tweet['url']}">View on Twitter</a></p>
            <p><em>Screenshot attached below</em></p>
        </div>
        """
    
    body += """
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    # Attach screenshots
    for screenshot_file in screenshots:
        if os.path.exists(screenshot_file):
            with open(screenshot_file, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_file))
                msg.attach(img)
    
    # Send email via Gmail SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(YOUR_EMAIL, YOUR_EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    """
    Main function to orchestrate the bot
    """
    print("=" * 50)
    print("Twitter Screenshot Bot Starting...")
    print(f"Target Account: @{TWITTER_HANDLE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Validate environment variables
    if not all([YOUR_EMAIL, YOUR_EMAIL_PASSWORD, APIFY_API_TOKEN]):
        print("ERROR: Missing required environment variables!")
        print("Required: YOUR_EMAIL, YOUR_EMAIL_PASSWORD, APIFY_API_TOKEN")
        return
    
    # Step 1: Get recent tweets
    tweets = get_recent_tweets(TWITTER_HANDLE, hours=12)
    
    if not tweets:
        print("No recent tweets found. Exiting.")
        return
    
    # Step 2: Take screenshots
    screenshots = []
    for i, tweet in enumerate(tweets, 1):
        filename = f"tweet_{i}_{tweet['id']}.png"
        if take_screenshot(tweet['url'], filename):
            screenshots.append(filename)
    
    # Step 3: Send email
    if screenshots:
        send_email(tweets, screenshots)
    else:
        print("No screenshots captured. Skipping email.")
    
    # Cleanup: Remove screenshot files
    for screenshot_file in screenshots:
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            print(f"Cleaned up: {screenshot_file}")
    
    print("=" * 50)
    print("Bot finished successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
