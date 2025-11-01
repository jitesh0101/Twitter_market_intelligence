#!/usr/bin/env python3
"""
Generate sample tweet data for testing the analysis pipeline.
Use this if you want to test the analysis features without scraping.
"""

import pandas as pd
from datetime import datetime, timedelta
import random
from pathlib import Path

print("=" * 70)
print("SAMPLE DATA GENERATOR")
print("=" * 70)

# Sample content templates
BULLISH_TEMPLATES = [
    "#nifty50 showing strong momentum! Bulls in control ",
    "Great rally in #sensex today! Market looking bullish ",
    "#banknifty breakout confirmed! Buy on dips ",
    "Positive sentiment in #intraday trading. Strong support at key levels",
    "#nifty50 crossed resistance! Uptrend continues ",
]

BEARISH_TEMPLATES = [
    "#nifty50 under pressure. Bears taking control ",
    "Market crash alert! #sensex falling rapidly ️",
    "#banknifty breakdown. Sell on rallies recommended",
    "Negative sentiment in #intraday. Support levels breaking",
    "#sensex correction mode. Watch for further downside",
]

NEUTRAL_TEMPLATES = [
    "#nifty50 consolidating. Waiting for direction",
    "Mixed signals in #sensex. Market indecisive today",
    "#banknifty range-bound trading. No clear trend",
    "Sideways movement in #intraday. Low volatility session",
    "#nifty50 at key level. Breakout expected soon",
]

HASHTAGS = ["#nifty50", "#sensex", "#banknifty", "#intraday", "#trading", "#stockmarket"]
USERNAMES = [f"trader_{i}" for i in range(1, 21)]

def generate_tweets(num_tweets=100):
    """Generate sample tweets with realistic data."""
    tweets = []
    
    for i in range(num_tweets):
        # Random sentiment distribution: 40% bullish, 30% bearish, 30% neutral
        rand = random.random()
        if rand < 0.4:
            content = random.choice(BULLISH_TEMPLATES)
            base_likes = random.randint(50, 500)
        elif rand < 0.7:
            content = random.choice(BEARISH_TEMPLATES)
            base_likes = random.randint(30, 400)
        else:
            content = random.choice(NEUTRAL_TEMPLATES)
            base_likes = random.randint(20, 300)
        
        # Random timestamp within last 24 hours
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        timestamp = datetime.now() - timedelta(hours=hours_ago, minutes=minutes_ago)
        
        # Random engagement metrics
        likes = base_likes + random.randint(-50, 100)
        retweets = int(likes * random.uniform(0.1, 0.3))
        replies = int(likes * random.uniform(0.05, 0.15))
        views = int(likes * random.uniform(10, 50))
        
        # Random hashtags (2-4 per tweet)
        num_tags = random.randint(2, 4)
        tweet_hashtags = random.sample(HASHTAGS, num_tags)
        
        tweet = {
            'tweet_id': f'sample_tweet_{i:04d}',
            'username': random.choice(USERNAMES),
            'timestamp': timestamp.isoformat(),
            'content': content,
            'hashtags': tweet_hashtags,
            'hashtags_lower': [h.lower() for h in tweet_hashtags],
            'mentions': [f'@user{random.randint(1, 5)}'] if random.random() > 0.5 else [],
            'likes': max(0, likes),
            'retweets': max(0, retweets),
            'replies': max(0, replies),
            'views': max(0, views),
            'scraped_at': datetime.now().isoformat(),
            'is_valid': True
        }
        
        tweets.append(tweet)
    
    return tweets

def main():
    # Create data directories
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate tweets
    num_tweets = 200  # Generate 200 sample tweets
    print(f"\nGenerating {num_tweets} sample tweets...")
    tweets = generate_tweets(num_tweets)
    
    # Create DataFrame
    df = pd.DataFrame(tweets)
    
    # Calculate some stats
    bullish_count = len([t for t in tweets if any(word in t['content'].lower() 
                         for word in ['rally', 'bullish', 'breakout', 'momentum', 'bull'])])
    bearish_count = len([t for t in tweets if any(word in t['content'].lower() 
                         for word in ['crash', 'bearish', 'breakdown', 'pressure', 'bear'])])
    
    print(f"\nGenerated tweets:")
    print(f"  Total: {len(tweets)}")
    print(f"  Bullish: {bullish_count} ({bullish_count/len(tweets)*100:.1f}%)")
    print(f"  Bearish: {bearish_count} ({bearish_count/len(tweets)*100:.1f}%)")
    print(f"  Neutral: {len(tweets)-bullish_count-bearish_count}")
    
    # Save as raw data
    raw_path = raw_dir / "tweets_raw.parquet"
    df.to_parquet(raw_path, index=False)
    print(f"\n Saved raw data to: {raw_path}")
    
    # Also save as processed (since it's already clean)
    processed_path = processed_dir / "tweets_processed.parquet"
    df.to_parquet(processed_path, index=False)
    print(f" Saved processed data to: {processed_path}")
    
    # Show sample
    print("\nSample tweets:")
    print("-" * 70)
    for i in range(min(3, len(tweets))):
        print(f"{i+1}. {tweets[i]['content']}")
        print(f"   Engagement: {tweets[i]['likes']} likes, {tweets[i]['retweets']} retweets")
        print()
    
    print("=" * 70)
    print(" SAMPLE DATA GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Analyze the data: python main.py --analyze")
    print("  2. Visualize results: python main.py --visualize")
    print("  3. Or run both: python main.py --analyze --visualize")
    print("\nResults will be in: data/analysis/")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
