"""
Shared text preprocessing utilities.

IMPORTANT: This file must exist in the same folder as BOTH
train_model_v5.py AND medverify_app.py, because the saved
tfidf_vectorizer.pkl stores a reference to stemmed_tokenizer.
If this file isn't importable when the .pkl is loaded, joblib
will raise an error like:
    AttributeError: Can't get attribute 'stemmed_tokenizer' on <module ...>
"""
import re


def simple_stem(word):
    """Lightweight suffix-stripping stemmer - no external library needed.
    Reduces word forms like prevent/prevents/prevented to one shared token."""
    for suf in ['ational', 'tional', 'ing', 'edly', 'ies', 'ied', 'ed', 'es', 'ly', 's']:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


def stemmed_tokenizer(text):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [simple_stem(w) for w in words]
