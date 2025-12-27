import pandas as pd
import spacy
import os
import re
from kneed import KneeLocator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

INPUT_FILE = "chase_complaints_2025_full.csv"
LEMMA_CACHE = "chase_lemmatized_cache.csv"
FINAL_OUTPUT = "chase_manually_labeled_2025.csv"

def clean_redactions(text):
    # to remove redactions (XXXX) and whitespaces using regex
    if not isinstance(text, str): return ""
    text = re.sub(r'X{2,}[/-]X{2,}[/-]X{2,}', '', text)
    text = re.sub(r'X{2,}', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# since Lemmatizing is computationally expensive, we would like to save it up in some file for future use
if os.path.exists(LEMMA_CACHE):
    print(f"Loading existing cache: {LEMMA_CACHE}")
    df = pd.read_csv(LEMMA_CACHE)
else:
    df = pd.read_csv(INPUT_FILE)
    df = df[['complaint_what_happened', 'date_sent_to_company', 'submitted_via', 'state']].copy()
    df = df.dropna(subset=['complaint_what_happened'])
    
    # Cleaning redactions
    df['clean_text'] = df['complaint_what_happened'].apply(clean_redactions)
    avg_len = df['complaint_what_happened'].str.len().mean()
    df = df[df['complaint_what_happened'].str.len() < avg_len].copy() #filtering only short-form messages
    
    nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
    lemmas = []
    for doc in nlp.pipe(df['clean_text'].astype(str), batch_size=500):
        # remove punctuation and stop words
        tokens = [t.lemma_.lower() for t in doc if t.is_alpha and not t.is_stop]
        lemmas.append(" ".join(tokens))
    
    df['lemmatized_text'] = lemmas
    df.to_csv(LEMMA_CACHE, index=False) #for future use
    print(f"Cache saved to {LEMMA_CACHE}")

# TFD-ID
vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(df['lemmatized_text'].fillna(''))

# for K-Means clustering we will find optimal number of clusters using an elbow method
k_range = range(2, 11)
inertias = []
for k in k_range:
    km = KMeans(n_clusters=k, random_state=1, n_init=10).fit(X)
    inertias.append(km.inertia_)

kn = KneeLocator(k_range, inertias, curve='convex', direction='decreasing')
optimal_k = kn.elbow if kn.elbow else 5 #in case we wont find an optimal cluster size
print(f"Optimal clusters identified: {optimal_k}")

# Clustering using the optimal size
model = KMeans(n_clusters=optimal_k, random_state=1, n_init=10)
df['group_id'] = model.fit_predict(X)

# we would like to label groups manually using top lemmas and sample messages
terms = vectorizer.get_feature_names_out()
centroids = model.cluster_centers_.argsort()[:, ::-1]
manual_labels = {}

print(f"Optimal number of groups is {optimal_k}")
for i in range(optimal_k):
    # top words and 2 sample complaints for this cluster
    top_words = [terms[ind] for ind in centroids[i, :10]]
    examples = df[df['group_id'] == i]['complaint_what_happened'].head(2).tolist()
    
    print(f"{i}th group")
    print(f"Keywords: {', '.join(top_words)}")
    print(f"Sample 1: {examples[0][:]}...")
    print(f"Sample 2: {examples[1][:]}...")
    
    label = input(f"Enter a name for Group {i}: ")
    manual_labels[i] = label.strip()
    print("-" * 30)

# mapping labels
df['group_name'] = df['group_id'].map(manual_labels)
final_df = df[['complaint_what_happened', 'date_sent_to_company', 'submitted_via', 'state', 'group_id', 'group_name']]
final_df.to_csv(FINAL_OUTPUT, index=False)