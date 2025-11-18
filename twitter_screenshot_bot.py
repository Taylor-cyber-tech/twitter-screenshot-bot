import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configuration from environment variables
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', 'elonmusk')
YOUR_EMAIL = os.environ.get('YOUR_EMAIL')
YOUR_EMAIL_PASSWORD = os.environ.get('YOUR_EMAIL_PASSWORD')

def take_profile_screenshot(username):
    """
    Take a screenshot of the user's Twitter profile showing recent tweets
    """
    print(f"Taking screenshot of @{username}'s profile...")
    
    profile_url = f"https://x.com/{username}"
    filename = f"profile_{username}.png"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1200, 'height': 2400},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            print(f"Navigating to {profile_url}...")
            page.goto(profile_url, wait_until='networkidle', timeout=30000)
            
            # Wait for tweets to load
            print("Waiting for content to load...")
            time.sleep(5)
            
            # Try to scroll down a bit to load more tweets
            page.evaluate("window.scrollTo(0, 800)")
            time.sleep(2)
            
            # Take screenshot
            print("Taking screenshot...")
            page.screenshot(path=filename, full_page=False)
            
            browser.close()
            print(f"✅ Screenshot saved: {filename}")
            return filename, profile_url
            
    except Exception as e:
        print(f"❌ Error taking screenshot: {e}")
        return None, profile_url

def send_email(username, screenshot_file, profile_url):
    """
    Send email with profile screenshot
    """
    print(f"Sending email to {YOUR_EMAIL}...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = YOUR_EMAIL
    msg['To'] = YOUR_EMAIL
    msg['Subject'] = f"Twitter Updates: @{username} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Email body
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #1DA1F2;">📸 Recent Tweets from @{username}</h2>
        <p>Here's a snapshot of their recent activity:</p>
        
        <div style="margin: 20px 0; padding: 15px; background-color: #f5f8fa; border-radius: 8px;">
            <p><strong>Profile:</strong> <a href="{profile_url}">{profile_url}</a></p>
            <p><strong>Captured:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <p style="color: #666; margin-top: 30px;">
            Screenshot is attached below. This bot runs automatically every 12 hours.
        </p>
        
        <hr style="border: 1px solid #e1e8ed; margin: 20px 0;">
        <p style="font-size: 12px; color: #999;">
            Automated by your Twitter Screenshot Bot 🤖
        </p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    # Attach screenshot
    if screenshot_file and os.path.exists(screenshot_file):
        with open(screenshot_file, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename=f'{username}_tweets.png')
            msg.attach(img)
        print("✅ Screenshot attached to email")
    else:
        print("⚠️ No screenshot to attach")
    
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
    print("Twitter Screenshot Bot Starting...")
    print(f"Target Account: @{TWITTER_HANDLE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Validate environment variables
    if not all([YOUR_EMAIL, YOUR_EMAIL_PASSWORD]):
        print("❌ ERROR: Missing required environment variables!")
        print("Required: YOUR_EMAIL, YOUR_EMAIL_PASSWORD")
        return
    
    # Take screenshot of profile
    screenshot_file, profile_url = take_profile_screenshot(TWITTER_HANDLE)
    
    # Send email
    if screenshot_file:
        send_email(TWITTER_HANDLE, screenshot_file, profile_url)
        
        # Cleanup
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            print(f"🗑️ Cleaned up: {screenshot_file}")
    else:
        print("❌ No screenshot captured, skipping email")
    
    print("=" * 60)
    print("✅ Bot finished successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

6. **Commit changes**

---

### Step 2: Update `requirements.txt`

1. Click on **`requirements.txt`**
2. Click **Edit**
3. Replace with just this one line:
```
playwright==1.40.0
