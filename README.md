AI Health Misinformation Detection
A Machine Learning web application that detects whether a health claim is credible or misinformation.
Built for: SoftaVerse Tech House Internship
Developer: Shahid Nawaz
Helpers: Alya Ibrar, Laraib Asraf
Features
Real-time health claim classification
NLP-based text processing (TF-IDF)
Naive Bayes ML model (82.5% CV accuracy)
Security hardened input validation
Live prediction statistics
Recent checks history
Tech Stack
Python 3 | Scikit-learn | Streamlit | Pandas | Joblib
Setup
pip install -r requirements.txt
streamlit run app.py
Security Features (v2.0)
Input length validation (10–500 chars)
HTML injection prevention (XSS protection)
Character whitelist validation
Structured error handling & logging
