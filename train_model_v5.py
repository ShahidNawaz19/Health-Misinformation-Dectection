"""
MedVerify AI - Model Training Pipeline (v5 - with stemming)
=============================================================
Adds a lightweight stemmer (no external library needed) so that
word forms like "prevent/prevents/prevented" or "cure/cures/cured"
are treated as the SAME feature. This meaningfully reduces the
model's sensitivity to exact wording, which matters a lot on a
small dataset like this one.

Also switches min_df back to 1 (from 2) - with only ~310 rows,
many valid domain words appear just once, and min_df=2 was
silently deleting them from the vocabulary entirely.
"""

import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# ----------------------------------------------------------------------------
# STEP 0 - Paths
# ----------------------------------------------------------------------------
PROJECT_DIR = r"C:\Users\LENOVO\Desktop\datascience project"
DATA_PATH = os.path.join(PROJECT_DIR, "health_misinfo_dataset_v3_curated.csv")
os.chdir(PROJECT_DIR)

# ----------------------------------------------------------------------------
# Stemmer - imported from a SHARED module (text_utils.py) so the pickled
# vectorizer can be loaded later by medverify_app.py without errors.
# text_utils.py must exist in this same folder.
# ----------------------------------------------------------------------------
from text_utils import simple_stem, stemmed_tokenizer


# ----------------------------------------------------------------------------
# STEP 1 - Load & Inspect Data
# ----------------------------------------------------------------------------
df = pd.read_csv(DATA_PATH)
print("=" * 60)
print("STEP 1: DATA INSPECTION")
print("=" * 60)
print(f"Total rows: {len(df)}")
print(f"Class balance:\n{df['label'].value_counts()}")

# ----------------------------------------------------------------------------
# STEP 2 - Clean Text
# ----------------------------------------------------------------------------
df['claim_clean'] = df['claim'].astype(str).str.strip().str.lower()
df = df.drop_duplicates(subset='claim_clean').reset_index(drop=True)
X_text = df['claim_clean']
y = df['label'].values

# ----------------------------------------------------------------------------
# STEP 3 - Train / Test Split
# ----------------------------------------------------------------------------
X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text, y, test_size=0.2, random_state=42, stratify=y
)

# ----------------------------------------------------------------------------
# STEP 4 - Vectorize (with stemming tokenizer, min_df=1)
# ----------------------------------------------------------------------------
tfidf = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english',
    min_df=1,
    sublinear_tf=True,
    tokenizer=stemmed_tokenizer
)
X_train = tfidf.fit_transform(X_train_text)
X_test = tfidf.transform(X_test_text)
print("\n" + "=" * 60)
print("STEP 4: VECTORIZATION")
print("=" * 60)
print(f"Vocabulary size: {len(tfidf.vocabulary_)}")

# ----------------------------------------------------------------------------
# STEP 5 - Cross-Validation
# ----------------------------------------------------------------------------
model = SVC(kernel='linear', probability=True, random_state=42, class_weight='balanced')
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
print("\n" + "=" * 60)
print("STEP 5: CROSS-VALIDATION")
print("=" * 60)
print(f"SVM CV accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

# ----------------------------------------------------------------------------
# STEP 6 - Fit Final Model
# ----------------------------------------------------------------------------
model.fit(X_train, y_train)

# ----------------------------------------------------------------------------
# STEP 7 - Evaluate
# ----------------------------------------------------------------------------
y_pred = model.predict(X_test)
print("\n" + "=" * 60)
print("STEP 7: TEST SET EVALUATION")
print("=" * 60)
print(f"Test Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
print(classification_report(y_test, y_pred, target_names=['Credible', 'Misinformation']))
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print("                 Predicted Credible   Predicted Misinfo")
print(f"Actual Credible        {cm[0][0]:<20} {cm[0][1]}")
print(f"Actual Misinfo         {cm[1][0]:<20} {cm[1][1]}")

# ----------------------------------------------------------------------------
# STEP 8 - Bias Check
# ----------------------------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 8: TOP SIGNAL WORDS (bias check)")
print("=" * 60)
feature_names = np.array(tfidf.get_feature_names_out())
coefs = model.coef_.toarray()[0]
top_misinfo = np.argsort(coefs)[-10:][::-1]
top_credible = np.argsort(coefs)[:10]
print("Words pushing toward MISINFORMATION:")
for i in top_misinfo:
    print(f"  {feature_names[i]:20s} weight={coefs[i]:.3f}")
print("\nWords pushing toward CREDIBLE:")
for i in top_credible:
    print(f"  {feature_names[i]:20s} weight={coefs[i]:.3f}")

# ----------------------------------------------------------------------------
# STEP 9 - Manual Sanity Check
# ----------------------------------------------------------------------------
print("\n" + "=" * 60)
print("STEP 9: MANUAL SANITY CHECK")
print("=" * 60)
test_claims = [
    "Smoking causes lung cancer",
    "HPV causes cervical cancer",
    "Vaccines cause autism",
    "Exercise reduces heart disease",
    "Bleach cures COVID-19",
    "Drinking warm water cures diabetes",
    "Essential oils cure all infections",
    "Regular flossing prevents gum disease",
    "Chickenpox is caused by the varicella-zoster virus.",
]
for claim in test_claims:
    vec = tfidf.transform([claim.strip().lower()])
    pred = model.predict(vec)[0]
    proba = model.predict_proba(vec)[0]
    confidence = max(proba) * 100
    label = "Credible" if pred == 0 else "Misinformation"
    nonzero_terms = vec.nnz
    flag = ""
    if confidence < 65:
        flag = "  <-- ⚠️ low confidence, treat as uncertain"
    elif nonzero_terms <= 1:
        flag = "  <-- ⚠️ almost no matching vocabulary"
    print(f"{label:15s} ({confidence:5.1f}%) | terms_matched={nonzero_terms:2d} | {claim}{flag}")

# ----------------------------------------------------------------------------
# STEP 10 - Save Model (the stemming tokenizer function is saved INSIDE
# the vectorizer object via joblib, but your app.py must define the same
# stemmed_tokenizer function before loading the pickle, or joblib will
# fail to find it. See note below.)
# ----------------------------------------------------------------------------
joblib.dump(model, 'svm_model.pkl')
joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
print("\nSaved svm_model.pkl and tfidf_vectorizer.pkl")
print("\n⚠️ IMPORTANT: medverify_app.py must have this line BEFORE loading")
print("   tfidf_vectorizer.pkl:  from text_utils import stemmed_tokenizer, simple_stem")
print("   (text_utils.py must sit in the same folder as the app)")
