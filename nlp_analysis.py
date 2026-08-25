import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

DB_NAME = "scd_workforce.db"

# Core workforce topics reference text for TF-IDF relevance modeling
HR_REFERENCE_DOC = """
onboarding orientation navigator school training class schedule course program workshops
manager lead director supervisor administrator communication conversation check-in discussion feedback
workload schedule stress burnout teaching course prep grading administrative operations
compensation pay salary wages benefits hourly rate incentives career development growth promotion
"""

# Simple keyword matching to confirm themes
THEME_KEYWORDS = {
    "onboarding clarity": ["onboard", "orient", "new hire", "first week", "welcome", "transition"],
    "manager communication": ["manager", "lead", "director", "supervisor", "communicat", "check-in", "feedback", "support", "restructur"],
    "event schedules": ["event", "schedule", "calendar", "workshop", "time", "conflict", "session", "attend", "invite"],
    "compensation": ["pay", "salary", "compensation", "benefit", "rate", "incentive", "merit", "wage"],
    "workload": ["workload", "burnout", "stress", "grading", "prep", "lecture", "teach", "overhead", "staffing"]
}

# Self-contained rules-based sentiment analyzer mimicking VADER compound scores
class CustomSentimentIntensityAnalyzer:
    def __init__(self):
        self.pos_words = {
            "good", "great", "excellent", "awesome", "perfect", "clear", "welcoming", "organized", "seamless",
            "support", "satisfied", "competitive", "merit", "fair", "reward", "manageable", "balance", "love", "friendly",
            "well", "proactive", "satisfied", "easy"
        }
        self.neg_words = {
            "lost", "lacking", "rushed", "disorganized", "poor", "rarely", "rescheduled", "hard", "delayed",
            "slow", "low", "exited", "burnout", "overload", "short-staffing", "burn", "stress", "conflict",
            "impossible", "last-minute", "worst", "bad", "terrible", "waste", "boring", "disappoint", "frustrat",
            "burnout", "overhead", "difficult"
        }
    
    def polarity_scores(self, text):
        words = text.lower().replace(".", "").replace(",", "").replace("!", "").split()
        pos_count = sum(1 for w in words if any(pw in w for pw in self.pos_words))
        neg_count = sum(1 for w in words if any(nw in w for nw in self.neg_words))
        
        total = pos_count + neg_count
        if total == 0:
            compound = 0.0
        else:
            # Scale compound score between -1.0 and 1.0
            compound = (pos_count - neg_count) / total
            
        return {'compound': compound}

def analyze_sentiment_and_relevance():
    print("Starting NLP Analysis Pipeline...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Fetch all feedback comments
    cursor.execute("SELECT feedback_id, raw_text FROM Fact_Sentiment_Feedback")
    rows = cursor.fetchall()
    
    if not rows:
        print("No feedback found in database. Please run data_generation.py first.")
        conn.close()
        return
        
    feedback_ids = [row[0] for row in rows]
    texts = [row[1] for row in rows]
    
    # Initialize custom sentiment analyzer
    analyzer = CustomSentimentIntensityAnalyzer()
    
    # Compute TF-IDF Relevance Scores
    print("Fitting TF-IDF vectorizer for relevance guardrails...")
    vectorizer = TfidfVectorizer(stop_words='english')
    # Fit vectorizer on all texts + HR reference document
    all_docs = texts + [HR_REFERENCE_DOC]
    tfidf_matrix = vectorizer.fit_transform(all_docs)
    
    # Extract comment vectors and reference document vector
    comment_vectors = tfidf_matrix[:-1]
    reference_vector = tfidf_matrix[-1]
    
    # Calculate cosine similarity of each comment to the HR reference document
    similarities = cosine_similarity(comment_vectors, reference_vector).flatten()
    
    # Normalize similarity scores between 0.0 and 1.0
    max_sim = np.max(similarities) if len(similarities) > 0 else 1.0
    min_sim = np.min(similarities) if len(similarities) > 0 else 0.0
    sim_range = max_sim - min_sim
    if sim_range == 0:
        sim_range = 1.0
    normalized_similarities = (similarities - min_sim) / sim_range
    
    # Process each comment
    updated_records = []
    
    print(f"Scoring {len(texts)} comments...")
    for idx, (fid, text) in enumerate(zip(feedback_ids, texts)):
        # 1. Sentiment Score
        sentiment_scores = analyzer.polarity_scores(text)
        compound = sentiment_scores['compound']
        
        # Classify sentiment
        if compound >= 0.05:
            sentiment_class = "Positive"
        elif compound <= -0.05:
            sentiment_class = "Negative"
        else:
            sentiment_class = "Neutral"
            
        # 2. Relevance Score
        relevance_score = float(normalized_similarities[idx])
        
        # 3. Theme Classification
        text_lower = text.lower()
        matched_theme = "other / outlier"
        
        # Keyword matching scoring to assign themes
        theme_scores = {}
        for theme, keywords in THEME_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                theme_scores[theme] = score
                
        if theme_scores:
            # Assign the theme with the highest matching keywords
            matched_theme = max(theme_scores, key=theme_scores.get)
        elif relevance_score < 0.2:
            matched_theme = "other / outlier"
            
        updated_records.append((compound, sentiment_class, relevance_score, matched_theme, fid))
        
    # Bulk update in SQLite
    cursor.executemany("""
        UPDATE Fact_Sentiment_Feedback
        SET sentiment_score = ?,
            sentiment_class = ?,
            relevance_score = ?,
            theme = ?
        WHERE feedback_id = ?
    """, updated_records)
    
    conn.commit()
    conn.close()
    
    print("NLP Analysis complete. Database updated.")
    
    # Log sample output
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT raw_text, theme, sentiment_class, sentiment_score, relevance_score 
        FROM Fact_Sentiment_Feedback 
        LIMIT 5
    """)
    samples = cursor.fetchall()
    print("\nSample processed records:")
    for sample in samples:
        print(f"Text: '{sample[0][:60]}...' | Theme: {sample[1]} | Sentiment: {sample[2]} ({sample[3]:.2f}) | Relevance: {sample[4]:.2f}")
    conn.close()

if __name__ == "__main__":
    analyze_sentiment_and_relevance()
