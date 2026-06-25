AI Health Misinformation Detection System
A machine learning web application built during an internship at SoftaVerse Tech House that detects whether a health claim is misinformation or credible using Natural Language Processing and SVM classifier.
About the Project
This project addresses the growing problem of health misinformation spread through social media and messaging platforms. The system analyzes any health-related claim entered by the user and predicts whether it is medically credible or misinformation, with confidence percentage.
Features
Real-time health claim analysis
SVM classifier trained on 922 health claims
TF-IDF vectorization with bigrams
Prediction history tracking
Stats dashboard (total checked, credible, misinformation count)
Dark themed modern UI built with Streamlit
Tech Stack
Python
Scikit-learn (SVM, TF-IDF)
Streamlit
Pandas, NumPy
Joblib, SciPy

Project Structure
datascience project/
├── app/app.py           Streamlit frontend
├── model/               Trained SVM model & vectorizer
├── data/                Dataset (922 rows)
├── charts/              Visualization charts
├── notebook/            Jupyter notebook
└── Run App.bat          One-click launcher

Double click Run App.bat
cd app
streamlit run app.py

Dataset
922 rows, balanced classes
Topics: vaccines, cancer, diabetes, mental health, heart disease, diet, exercise, infectious diseases
Label: 0 = Credible, 1 = Misinformation

Developed by: Shahid
Organization: SoftaVerse Tech House
Internship Project: AI Health Misinformation Detection
