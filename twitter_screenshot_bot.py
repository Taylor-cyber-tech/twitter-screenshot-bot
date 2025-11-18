import os
import smtplib
import time
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup

# Configuration from environment variables
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', 'elonmusk')
YOUR_EMAIL = os.environ.get('YOUR_EMAIL')
YOUR_EMAIL_PASSWORD = os.environ.get('YOUR_EMAIL_PASSWORD')

# Nitter instances (public Twitter mirrors)
NITTER_INSTANCES = [
    'https://nitter.net',
    'https://nitter.privacydev.net',
    'https://nitter.poast.org',
]

def get_recent_tweets_from_nitter(username, hours=12):
    """
    Scrape recent tweets from Nitter (Twitter mirror)
    """
    print(f"Fetching tweets from @{username} via Nitter...")
    
    tweets = []
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    for nitter_url in NITTER_INSTANCES:
        try:
            print(f"Trying Nitter instance: {nitter_url}")
            url = f"{nitter_url}/{username}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all tweet containers
            tweet_items = soup.find_all('div', class_='timeline-item')
            
            print(f"Found {len(tweet_items)} tweet items")
            
            for item in tweet_items:
                try:
                    # Get tweet link
                    link_elem = item.find('a', class_='tweet-link')
                    if not link_elem:
                        continue
                    
                    tweet_path = link_elem.get('href', '')
                    if not tweet_path:
                        continue
                    
                    # Extract tweet ID from path (format: /username/status/1234567890)
                    match = re.search(r'/status/(\d+)', tweet_path)
                    if not match:
                        continue
                    
                    tweet_id = match.group(1)
                    
                    # Get tweet text
                    tweet_content = item.find('div', class_='tweet-content')
                    tweet_text = tweet_content.get_text(strip=True) if tweet_content else 'No text'
                    
                    # Get tweet date
                    date_elem = item.find('span', class_='tweet-date')
                    tweet_date = date_elem.get('title', '') if date_elem else ''
                    
                    # Try to parse date (Nitter uses various formats)
                    tweet_time = None
                    if tweet_date:
                        try:
                            # Try parsing ISO format
                            tweet_time = datetime.fromisoformat(tweet_date.replace('Z', '+00:00'))
                            tweet_time = tweet_time.replace(tzinfo=None)
                        except:
                            # If parsing fails, include tweet anyway
                            tweet_time = datetime.utcnow()
                    else:
                        tweet_time = datetime.utcnow()
                    
                    # Check if tweet is recent enough
                    if tweet_time >= time_threshold:
                        # Construct real Twitter URL
                        twitter_url = f"https://x.com/{username}/status/{tweet_id}"
                        
                        tweets.append({
                            'id': tweet_id,
                            'text': tweet_text,
                            'url': twitter_url,
                            'created_at': tweet_date or 'Recent',
                        })
                
                except Exception as e:
                    print(f"Error parsing tweet: {e}")
                    continue
            
            if tweets:
                print(f"✅ Successfully fetched {len(tweets)} recent tweets")
                return tweets
            else:
                print(f"No recent tweets found on this instance, trying next...")
                
        except Exception as e:
            print(f"Error with {nitter_url}: {e}")
            continue
    
    print(f"Found {len(tweets)} tweets total")
    return tweets

def take_screenshot(url, filename):
    """
    Take a screenshot of a tweet using Playwright
    """
    print(f"Taking screenshot of {url}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1200, 'height': 1400},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Go to the tweet URL
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for tweet to load
            time.sleep(4)
            
            # Try to find and screenshot the tweet
            try:
                # Find the article element (tweet container)
                tweet_element = page.locator('article').first
                if tweet_element:
                    tweet_element.screenshot(path=filename)
                    print(f"✅ Screenshot saved: {filename}")
                else:
                    # Fallback: screenshot visible area
                    page.screenshot(path=filename, full_page=False)
                    print(f"✅ Screenshot saved (fallback): {filename}")
            except:
                # Last resort: screenshot the page
                page.screenshot(path=filename, full_page=False)
                print(f"✅ Screenshot saved (page): {filename}")
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Error taking screenshot: {e}")
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
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f8fa;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 12px;">
            <h2 style="color: #1DA1F2; margin-bottom: 20px;">📸 Recent Tweets from @{TWITTER_HANDLE}</h2>
            <p style="color: #666;">Found {len(tweets)} tweets in the last 12 hours:</p>
            <hr style="border: 1px solid #e1e8ed; margin: 20px 0;">
    """
    
    for i, tweet in enumerate(tweets, 1):
        body += f"""
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #e1e8ed; border-radius: 8px; background-color: #f9fafb;">
            <h3 style="color: #14171a; margin-top: 0;">Tweet #{i}</h3>
            <p style="color: #657786; font-size: 14px;"><strong>Posted:</strong> {tweet['created_at']}</p>
            <p style="color: #14171a; line-height: 1.5;">{tweet['text'][:200]}{'...' if len(tweet['text']) > 200 else ''}</p>
            <p><a href="{tweet['url']}" style="color: #1DA1F2; text-decoration: none;">🔗 View on Twitter/X</a></p>
            <p style="color: #999; font-size: 12px;"><em>Screenshot attached below</em></p>
        </div>
        """
    
    body += """
            <hr style="border: 1px solid #e1e8ed; margin: 20px 0;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                Automated by your Twitter Screenshot Bot 🤖<br>
                Runs every 12 hours automatically
            </p>
        </div>
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
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def main():
    """
    Main function to orchestrate the bot
    """
    print("=" * 60)
    print("Twitter Screenshot Bot Starting (Nitter Method)...")
    print(f"Target Account: @{TWITTER_HANDLE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Validate environment variables
    if not all([YOUR_EMAIL, YOUR_EMAIL_PASSWORD]):
        print("❌ ERROR: Missing required environment variables!")
        print("Required: YOUR_EMAIL, YOUR_EMAIL_PASSWORD")
        return
    
    # Step 1: Get recent tweets from Nitter
    tweets = get_recent_tweets_from_nitter(TWITTER_HANDLE, hours=12)
    
    if not tweets:
        print("⚠️ No recent tweets found. Exiting.")
        return
    
    # Step 2: Take screenshots
    screenshots = []
    for i, tweet in enumerate(tweets[:5], 1):  # Limit to 5 tweets max
        filename = f"tweet_{i}_{tweet['id']}.png"
        if take_screenshot(tweet['url'], filename):
            screenshots.append(filename)
        time.sleep(2)  # Small delay between screenshots
    
    # Step 3: Send email
    if screenshots:
        send_email(tweets, screenshots)
    else:
        print("⚠️ No screenshots captured. Skipping email.")
    
    # Cleanup: Remove screenshot files
    for screenshot_file in screenshots:
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            print(f"🗑️ Cleaned up: {screenshot_file}")
    
    print("=" * 60)
    print("✅ Bot finished successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
