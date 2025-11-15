#!/usr/bin/env python3
"""
VIBE SCORE GENERATOR - Multi-City Compatible

Generates neighborhood vibe scores from Airbnb review text using:
- Sentiment analysis (TextBlob)
- Topic modeling (LDA)
- Aspect-based sentiment extraction
- Confidence-weighted scoring

Converted from vibescore.ipynb with minimal changes for multi-city compatibility.

Author: Vibe-Aware Pricing Team
Date: 2025-11-08
"""

import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.preprocessing import StandardScaler
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

CITY = 'austin'  # Change this to: 'london', 'nyc', or 'austin'
SAMPLE_SIZE = 100000  # Number of reviews to sample for analysis
RANDOM_SEED = 42

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / f'data/{CITY.lower()}/raw'

# Input files (auto-detect city suffix)
LISTINGS_FILE = DATA_DIR / f'listings_{CITY.capitalize()}.csv'
REVIEWS_FILE = DATA_DIR / f'reviews_{CITY.capitalize()}.csv'
NEIGHBORHOODS_FILE = DATA_DIR / f'neighbourhoods_{CITY.capitalize()}.csv'

# Output files
OUTPUT_DIR = DATA_DIR
OUTPUT_VIBE_SCORES = OUTPUT_DIR / '01_neighborhood_vibe_scores.csv'
OUTPUT_VIBE_DIMENSIONS = OUTPUT_DIR / '01_neighborhood_vibe_dimensions.csv'
OUTPUT_VIBE_FEATURES = OUTPUT_DIR / '01_vibe_features_for_modeling.csv'

print("=" * 80)
print(f"VIBE SCORE GENERATOR - {CITY.upper()}")
print("=" * 80)
print()

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("[1/9] Loading datasets...")

listings = pd.read_csv(LISTINGS_FILE)
reviews = pd.read_csv(REVIEWS_FILE)
neighborhoods = pd.read_csv(NEIGHBORHOODS_FILE)

print(f"\n  Datasets loaded:")
print(f"    Listings:       {len(listings):,} records")
print(f"    Reviews:        {len(reviews):,} records")
print(f"    Neighborhoods:  {len(neighborhoods):,} unique areas")

# Auto-detect neighborhood column
neighborhood_cols = [col for col in listings.columns if 'neighbourhood' in col.lower()]
if 'neighbourhood_cleansed' in listings.columns:
    listing_neighborhood_col = 'neighbourhood_cleansed'
elif 'neighbourhood' in listings.columns:
    listing_neighborhood_col = 'neighbourhood'
else:
    listing_neighborhood_col = neighborhood_cols[0]

# Find review text column
text_col_candidates = ['comments', 'review', 'text', 'review_text', 'comment']
text_column = None
for col in text_col_candidates:
    if col in reviews.columns:
        text_column = col
        break

if not text_column:
    raise ValueError(f"No review text column found. Expected one of: {text_col_candidates}")

print(f"\n  Detected columns:")
print(f"    Neighborhood: '{listing_neighborhood_col}'")
print(f"    Review text: '{text_column}'")

non_null = reviews[text_column].notna().sum()
print(f"    Reviews with text: {non_null:,} ({non_null/len(reviews)*100:.1f}%)")
print()

# ============================================================================
# STEP 2: PREPARE DATA
# ============================================================================

print("[2/9] Preparing data...")

listid = listings[['id', listing_neighborhood_col]].copy()
listid.rename(columns={listing_neighborhood_col: 'neighbourhood'}, inplace=True)

joinedreviews = reviews.merge(
    listid,
    left_on='listing_id',
    right_on='id',
    how='left'
)

# Keep only reviews with text and neighborhood
joinedreviews = joinedreviews[
    joinedreviews[text_column].notna() &
    joinedreviews['neighbourhood'].notna()
].copy()

print(f"  ✓ Reviews with text + neighborhood: {len(joinedreviews):,}")
print(f"  ✓ Unique neighborhoods: {joinedreviews['neighbourhood'].nunique()}")

if 'date' in joinedreviews.columns:
    joinedreviews['date'] = pd.to_datetime(joinedreviews['date'], errors='coerce')
    print(f"  ✓ Date range: {joinedreviews['date'].min().date()} to {joinedreviews['date'].max().date()}")

print()

# ============================================================================
# STEP 3: TEXT PREPROCESSING
# ============================================================================

print("[3/9] Preprocessing review texts...")

def preprocess_text(text):
    """Clean text for NLP analysis"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

joinedreviews['text_clean'] = joinedreviews[text_column].apply(preprocess_text)
joinedreviews['word_count'] = joinedreviews['text_clean'].str.split().str.len()
joinedreviews = joinedreviews[joinedreviews['word_count'] >= 5].copy()

print(f"  ✓ Cleaned {len(joinedreviews):,} reviews (min 5 words)")
print(f"  ✓ Avg words per review: {joinedreviews['word_count'].mean():.0f}")

# Sample for processing if needed
if len(joinedreviews) > SAMPLE_SIZE:
    print(f"\n  Sampling {SAMPLE_SIZE:,} reviews for analysis...")
    sampledrev = joinedreviews.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED)
else:
    sampledrev = joinedreviews.copy()
    print(f"\n  Using all {len(sampledrev):,} reviews (below sample limit)")

print()

# ============================================================================
# STEP 4: SENTIMENT ANALYSIS
# ============================================================================

print("[4/9] Analyzing sentiment...")

print(f"\n  Sample of actual review text (first 3 reviews):")
for i, text in enumerate(sampledrev[text_column].head(3)):
    print(f"    Review {i+1}: {str(text)[:100]}...")

def analyze_sentiment_textblob(text):
    """Analyze sentiment using TextBlob"""
    if not text or len(str(text).strip()) < 5:
        return {'polarity': 0, 'subjectivity': 0}
    try:
        blob = TextBlob(str(text))
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    except Exception as e:
        return {'polarity': 0, 'subjectivity': 0}

print("\n  Analyzing sentiment on original review text...")
sentiments = []
nzc = 0

for i, row in sampledrev.iterrows():
    sentiment = analyze_sentiment_textblob(row[text_column])
    sentiments.append(sentiment)

    if sentiment['polarity'] != 0 or sentiment['subjectivity'] != 0:
        nzc += 1

    if len(sentiments) % 10000 == 0:
        print(f"    Analyzed {len(sentiments):,} reviews (non-zero: {nzc})...")

sampledrev['sentiment_polarity'] = [s['polarity'] for s in sentiments]
sampledrev['sentiment_subjectivity'] = [s['subjectivity'] for s in sentiments]

print(f"\n  ✓ Sentiment analysis complete")
print(f"    Reviews analyzed: {len(sentiments):,}")
print(f"    Non-zero sentiments: {nzc:,} ({nzc/len(sentiments)*100:.1f}%)")
print(f"    Mean polarity: {sampledrev['sentiment_polarity'].mean():.3f} (range: -1 to 1)")
print(f"    Mean subjectivity: {sampledrev['sentiment_subjectivity'].mean():.3f} (range: 0 to 1)")
print(f"    Polarity std: {sampledrev['sentiment_polarity'].std():.3f}")

print(f"\n  Sentiment distribution:")
print(f"    Positive (>0.1): {(sampledrev['sentiment_polarity'] > 0.1).sum():,}")
print(f"    Neutral (-0.1 to 0.1): {((sampledrev['sentiment_polarity'] >= -0.1) & (sampledrev['sentiment_polarity'] <= 0.1)).sum():,}")
print(f"    Negative (<-0.1): {(sampledrev['sentiment_polarity'] < -0.1).sum():,}")
print()

# ============================================================================
# STEP 5: TOPIC MODELING (LDA)
# ============================================================================

print("[5/9] Extracting latent topics...")

vibes = [
    'walkability', 'safety', 'nightlife', 'quietness', 'family_friendly',
    'local_authentic', 'convenience', 'food_scene', 'liveliness', 'charm'
]

n_topics = len(vibes)
print(f"  Extracting {n_topics} latent topics from reviews...")

# Create TF-IDF features
tfidf = TfidfVectorizer(
    max_features=1000,
    max_df=0.8,
    min_df=5,
    stop_words='english',
    ngram_range=(1, 2)
)

tfidf_matrix = tfidf.fit_transform(sampledrev['text_clean'])
print(f"  ✓ Created TF-IDF matrix: {tfidf_matrix.shape}")

# LDA Topic Modeling
lda = LatentDirichletAllocation(
    n_components=n_topics,
    max_iter=20,
    learning_method='online',
    random_state=RANDOM_SEED,
    n_jobs=-1
)

print(f"  Training LDA model with {n_topics} topics...")
doc_topic_dist = lda.fit_transform(tfidf_matrix)

# Display top words per topic
feature_names = tfidf.get_feature_names_out()
print("\n  Top words per topic:")
for topic_idx, topic in enumerate(lda.components_):
    top_words_idx = topic.argsort()[-10:][::-1]
    top_words = [feature_names[i] for i in top_words_idx]
    print(f"    Topic {topic_idx}: {', '.join(top_words[:5])}")

# Assign topic distributions to reviews
for i in range(n_topics):
    sampledrev[f'topic_{i}_score'] = doc_topic_dist[:, i]

print(f"\n  ✓ Topic modeling complete")
print(f"    Each review has probability distribution over {n_topics} topics")
print()

# ============================================================================
# STEP 6: ASPECT SENTIMENT ANALYSIS
# ============================================================================

print("[6/9] Extracting aspect-based sentiments...")

ASPECT_KEYWORDS = {
    'walkability': ['walk', 'walking', 'walkable', 'foot', 'steps', 'distance'],
    'safety': ['safe', 'secure', 'safety', 'dangerous', 'unsafe', 'worried'],
    'nightlife': ['nightlife', 'bars', 'clubs', 'party', 'pub', 'drinks'],
    'quietness': ['quiet', 'peaceful', 'calm', 'noisy', 'loud', 'noise'],
    'family_friendly': ['family', 'kids', 'children', 'child', 'playground'],
    'local_authentic': ['local', 'authentic', 'traditional', 'touristy', 'tourist'],
    'convenience': ['convenient', 'close', 'near', 'metro', 'tram', 'transport'],
    'food_scene': ['restaurant', 'food', 'cafe', 'coffee', 'dining', 'eat'],
    'liveliness': ['lively', 'vibrant', 'busy', 'bustling', 'energetic', 'dead'],
    'charm': ['charming', 'beautiful', 'lovely', 'pretty', 'ugly', 'attractive']
}

def extract_aspect_sentiment(text, keywords):
    """Extract sentiment around specific aspect keywords"""
    if not text:
        return {'mentioned': False, 'sentiment': 0, 'count': 0}

    text_lower = text.lower()
    words = text_lower.split()

    mentions = []
    for i, word in enumerate(words):
        if any(kw in word for kw in keywords):
            start = max(0, i - 5)
            end = min(len(words), i + 6)
            context = ' '.join(words[start:end])
            sentiment = TextBlob(context).sentiment.polarity
            mentions.append(sentiment)

    if mentions:
        return {
            'mentioned': True,
            'sentiment': np.mean(mentions),
            'count': len(mentions)
        }
    else:
        return {'mentioned': False, 'sentiment': 0, 'count': 0}

for aspect, keywords in ASPECT_KEYWORDS.items():
    print(f"  Processing {aspect}...")
    aspect_results = sampledrev['text_clean'].apply(
        lambda x: extract_aspect_sentiment(x, keywords)
    )

    sampledrev[f'{aspect}_mentioned'] = [r['mentioned'] for r in aspect_results]
    sampledrev[f'{aspect}_sentiment'] = [r['sentiment'] for r in aspect_results]
    sampledrev[f'{aspect}_count'] = [r['count'] for r in aspect_results]

print("  ✓ Aspect-based sentiment extraction complete")
print()

# ============================================================================
# STEP 7: AGGREGATE TO NEIGHBORHOOD LEVEL
# ============================================================================

print("[7/9] Aggregating to neighborhood level...")

agg_dict = {
    'sentiment_polarity': ['mean', 'std'],
    'sentiment_subjectivity': 'mean',
    'word_count': ['mean', 'count']
}

for aspect in ASPECT_KEYWORDS.keys():
    agg_dict[f'{aspect}_sentiment'] = 'mean'
    agg_dict[f'{aspect}_count'] = 'sum'

for i in range(n_topics):
    agg_dict[f'topic_{i}_score'] = 'mean'

neighborhood_vibes = sampledrev.groupby('neighbourhood').agg(agg_dict)

# Flatten column names
new_cols = []
for col in neighborhood_vibes.columns:
    if isinstance(col, tuple):
        new_cols.append(f'{col[0]}_{col[1]}' if col[1] else col[0])
    else:
        new_cols.append(col)

neighborhood_vibes.columns = new_cols
neighborhood_vibes.reset_index(inplace=True)

# Create comprehensive rename map
rename_map = {
    'sentiment_polarity_mean': 'sentiment_mean',
    'sentiment_polarity_std': 'sentiment_std',
    'sentiment_subjectivity_mean': 'subjectivity',
    'word_count_mean': 'avg_review_length',
    'word_count_count': 'review_count'
}

# Add aspect column renames
for aspect in ASPECT_KEYWORDS.keys():
    rename_map[f'{aspect}_sentiment_mean'] = f'{aspect}_sentiment'
    rename_map[f'{aspect}_count_sum'] = f'{aspect}_count_sum'

neighborhood_vibes.rename(columns=rename_map, inplace=True)

print(f"  ✓ Aggregated to {len(neighborhood_vibes)} neighborhoods")
print()

# ============================================================================
# STEP 8: CALCULATE VIBE SCORES
# ============================================================================

print("[8/9] Calculating vibe scores...")

# Convert aspect sentiments to raw scores (0-10)
for aspect in ASPECT_KEYWORDS.keys():
    neighborhood_vibes[f'{aspect}_score_raw'] = (
        (neighborhood_vibes[f'{aspect}_sentiment'] + 1) * 5
    ).clip(0, 10)

# Calculate percentile ranks for each aspect (0-100 scale)
print("  Converting to percentile ranks for relative comparison...")
for aspect in ASPECT_KEYWORDS.keys():
    mask = neighborhood_vibes[f'{aspect}_count_sum'] > 0
    if mask.sum() > 0:
        neighborhood_vibes.loc[mask, f'{aspect}_score'] = (
            neighborhood_vibes.loc[mask, f'{aspect}_score_raw'].rank(pct=True) * 10
        )
    else:
        neighborhood_vibes[f'{aspect}_score'] = 5  # neutral if no data

# Show aspect distributions
aspect_mention_totals = {}
for aspect in ASPECT_KEYWORDS.keys():
    total = neighborhood_vibes[f'{aspect}_count_sum'].sum()
    aspect_mention_totals[aspect] = total

print("\n  Aspect mention frequencies:")
for aspect, total in sorted(aspect_mention_totals.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"    {aspect:20s}: {total:,} mentions")

# Convert sentiment to percentile rank
neighborhood_vibes['sentiment_score_raw'] = (
    (neighborhood_vibes['sentiment_mean'] + 1) * 5
).clip(0, 10)
neighborhood_vibes['sentiment_score'] = (
    neighborhood_vibes['sentiment_score_raw'].rank(pct=True) * 10
)

# Confidence score based on review volume
median_reviews = neighborhood_vibes['review_count'].median()
neighborhood_vibes['confidence'] = (
    neighborhood_vibes['review_count'] / median_reviews
).clip(0.5, 1.5)

# Consistency bonus
max_std = neighborhood_vibes['sentiment_std'].max()
if max_std > 0:
    neighborhood_vibes['consistency'] = 1 - (
        neighborhood_vibes['sentiment_std'] / max_std
    )
else:
    neighborhood_vibes['consistency'] = 1

# Base weights for different aspects
BASE_WEIGHTS = {
    'safety': 0.25,
    'convenience': 0.20,
    'walkability': 0.15,
    'charm': 0.10,
    'local_authentic': 0.10,
    'food_scene': 0.08,
    'liveliness': 0.05,
    'quietness': 0.03,
    'nightlife': 0.02,
    'family_friendly': 0.02
}

# Calculate weighted dimension score
neighborhood_vibes['weighted_dimension_score'] = 0
for aspect, weight in BASE_WEIGHTS.items():
    neighborhood_vibes['weighted_dimension_score'] += (
        neighborhood_vibes[f'{aspect}_score'] * weight
    )

# FINAL VIBE SCORE with confidence adjustment
neighborhood_vibes['vibe_score_raw'] = (
    neighborhood_vibes['weighted_dimension_score'] * 0.6 +
    neighborhood_vibes['sentiment_score'] * 0.4
)

# Apply confidence and consistency multipliers
neighborhood_vibes['vibe_score'] = (
    neighborhood_vibes['vibe_score_raw'] *
    neighborhood_vibes['confidence'] *
    (0.8 + neighborhood_vibes['consistency'] * 0.2)
) * 10

neighborhood_vibes['vibe_score'] = neighborhood_vibes['vibe_score'].clip(0, 100).round(1)

print(f"\n  ✓ Vibe scores calculated using:")
print(f"    • Percentile ranking (relative performance)")
print(f"    • Review volume confidence weighting")
print(f"    • Sentiment consistency adjustment")
print(f"\n  Statistics:")
print(f"    Mean: {neighborhood_vibes['vibe_score'].mean():.1f}")
print(f"    Std: {neighborhood_vibes['vibe_score'].std():.1f}")
print(f"    Range: [{neighborhood_vibes['vibe_score'].min():.1f}, {neighborhood_vibes['vibe_score'].max():.1f}]")
print(f"    Q1: {neighborhood_vibes['vibe_score'].quantile(0.25):.1f}")
print(f"    Median: {neighborhood_vibes['vibe_score'].median():.1f}")
print(f"    Q3: {neighborhood_vibes['vibe_score'].quantile(0.75):.1f}")
print()

# ============================================================================
# STEP 9: GENERATE INSIGHTS & SAVE OUTPUTS
# ============================================================================

print("[9/9] Generating insights and saving outputs...")

def get_top_characteristics(row):
    aspect_data = []
    for aspect in ASPECT_KEYWORDS.keys():
        score = row[f'{aspect}_score']
        mentions = row[f'{aspect}_count_sum']
        if mentions > 0:
            aspect_data.append((aspect.replace('_', ' '), score, mentions))

    aspect_data.sort(key=lambda x: (x[1], x[2]), reverse=True)

    descriptors = []
    for aspect_name, score, _ in aspect_data[:3]:
        if score >= 7.5:
            descriptors.append(f"excellent {aspect_name}")
        elif score >= 6.5:
            descriptors.append(f"good {aspect_name}")
        elif score >= 5:
            descriptors.append(aspect_name)

    return ', '.join(descriptors) if descriptors else 'varied reviews'

neighborhood_vibes['key_characteristics'] = neighborhood_vibes.apply(
    get_top_characteristics, axis=1
)

def classify_sentiment(score):
    if score >= 0.6:
        return 'Very Positive'
    elif score >= 0.3:
        return 'Positive'
    elif score >= -0.1:
        return 'Neutral'
    elif score >= -0.4:
        return 'Negative'
    else:
        return 'Very Negative'

neighborhood_vibes['sentiment_category'] = neighborhood_vibes['sentiment_mean'].apply(
    classify_sentiment
)

# Save outputs
summary_cols = ['neighbourhood', 'vibe_score', 'key_characteristics',
                'sentiment_mean', 'sentiment_category', 'review_count']
summary = neighborhood_vibes[summary_cols].copy()
summary.columns = ['neighbourhood', 'vibe_score', 'characteristics',
                   'sentiment', 'sentiment_category', 'review_count']
summary = summary.sort_values('vibe_score', ascending=False)
summary.to_csv(OUTPUT_VIBE_SCORES, index=False)

dimension_cols = ['neighbourhood', 'vibe_score', 'review_count'] + \
                 [f'{aspect}_score' for aspect in ASPECT_KEYWORDS.keys()]
dimensions = neighborhood_vibes[dimension_cols].copy()
dimensions = dimensions.sort_values('vibe_score', ascending=False)
dimensions.to_csv(OUTPUT_VIBE_DIMENSIONS, index=False)

model_cols = ['neighbourhood', 'vibe_score', 'sentiment_mean', 'sentiment_std',
              'subjectivity', 'review_count', 'avg_review_length'] + \
             [f'{aspect}_score' for aspect in ASPECT_KEYWORDS.keys()]
model_features = neighborhood_vibes[model_cols].copy()
model_features.to_csv(OUTPUT_VIBE_FEATURES, index=False)

print("\n  ✓ Files saved:")
print(f"    1. {OUTPUT_VIBE_SCORES.name}")
print(f"    2. {OUTPUT_VIBE_DIMENSIONS.name}")
print(f"    3. {OUTPUT_VIBE_FEATURES.name}")

print()
print("=" * 80)
print(f"VIBE SCORE GENERATION COMPLETE - {CITY.upper()} ✅")
print("=" * 80)
print()
print(f"Summary for {CITY.capitalize()}:")
print(f"  • {len(neighborhood_vibes)} neighborhoods analyzed")
print(f"  • {len(sampledrev):,} reviews processed")
print(f"  • Vibe score range: {neighborhood_vibes['vibe_score'].min():.1f} - {neighborhood_vibes['vibe_score'].max():.1f}")
print(f"  • Mean vibe score: {neighborhood_vibes['vibe_score'].mean():.1f}")
print()
print(f"Top 5 neighborhoods by vibe score:")
for idx, row in summary.head(5).iterrows():
    print(f"  {row['neighbourhood']:30s} {row['vibe_score']:5.1f}  ({row['characteristics']})")
print()
print("=" * 80)
