# 🔬 MedVerify AI — Health Misinformation Detection Engine

**Live Demo:** [https://health-misinfo-check.streamlit.app/](https://health-misinfo-check.streamlit.app/)

MedVerify AI is a machine learning–powered web application that analyzes health-related claims and classifies them as **Credible** or **Misinformation**, using a trained NLP model combined with an AI-generated explanation for each result.

---

## ✨ Features

- **Single Claim Analysis** — Enter any health claim and get an instant credibility verdict with a confidence score.
- **AI-Generated Explanations** — Each prediction is accompanied by a natural-language explanation (powered by the Groq API) describing *why* the claim was classified that way, with reference to trusted sources (WHO, CDC, NIH).
- **Bulk CSV Verification** — Upload a `.csv` file with a `claim` column to classify multiple claims at once and download the results.
- **Platform Analytics Dashboard** — Live pie-chart breakdown of credible vs. misinformation claims analyzed in the current session.
- **PDF Report Export** — Download a formatted PDF report of any analyzed claim, including the AI explanation.
- **Recent Audit Log** — Quick view of the last few claims checked in the session.

---

## 🧠 How It Works

1. The claim text is cleaned and tokenized using a lightweight custom **stemmer** (`text_utils.py`), so that word forms like *prevent / prevents / prevented* are treated as the same feature.
2. The text is converted into numerical features using a **TF-IDF vectorizer** (unigrams + bigrams).
3. A **Support Vector Machine (SVM)** classifier predicts whether the claim is Credible or Misinformation, along with a confidence score.
4. The Groq LLM API (`openai/gpt-oss-120b` model) generates a short, structured explanation for the result.

> **Note:** This is a machine learning model trained on a curated dataset of health claims. It is a decision-support tool, **not a substitute for professional medical advice**. Always verify important health information with a qualified healthcare provider or trusted sources like WHO/CDC.

---

## 🛠️ Tech Stack

| Component            | Technology                          |
|-----------------------|--------------------------------------|
| Frontend / App        | [Streamlit](https://streamlit.io)   |
| ML Model              | Scikit-learn (SVM, TF-IDF)          |
| AI Explanations       | Groq API (`openai/gpt-oss-120b`)    |
| Data Handling         | Pandas                              |
| Visualization         | Plotly Express                      |
| PDF Reports           | ReportLab                           |
| Deployment            | Streamlit Community Cloud           |

---

## 📁 Project Structure

```
datascience project/
├── app.py                              # Main Streamlit application
├── text_utils.py                       # Shared stemming/tokenizer utilities (required by both training & app)
├── train_model_v5.py                   # Model training script
├── health_misinfo_dataset_v3_curated.csv   # Training dataset (curated, style-neutral)
├── svm_model.pkl                       # Trained SVM classifier
├── tfidf_vectorizer.pkl                # Trained TF-IDF vectorizer
├── requirements.txt                    # Python dependencies
├── .streamlit/
│   ├── config.toml                     # App theme configuration
│   └── secrets.toml                    # API keys (NOT committed to GitHub)
└── README.md
```

---

## ⚙️ Installation & Local Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd "datascience project"
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up your Groq API key**

Create a file at `.streamlit/secrets.toml` (this file is git-ignored and never uploaded) with:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

**4. Run the app**
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🔁 Retraining the Model

If you want to retrain the model on updated data:
```bash
python train_model_v5.py
```
This regenerates `svm_model.pkl` and `tfidf_vectorizer.pkl` using `health_misinfo_dataset_v3_curated.csv`, and prints cross-validation accuracy, a confusion matrix, and a bias/sanity check on sample claims.

---

## 📊 Model Performance

- **Cross-validation accuracy:** ~82%
- **Test set accuracy:** ~81%
- Verified on a held-out set of real-world health claims not seen during training (e.g., correctly distinguishes *"Smoking causes lung cancer"* as credible from *"Vaccines cause autism"* as misinformation).
- Predictions with low vocabulary overlap or borderline confidence (<65%) are flagged so results can be interpreted with appropriate caution.

---

## ⚠️ Known Limitations

- The model is trained on a relatively small, curated dataset (~310 claims) and may be less reliable on claims involving topics or phrasing very different from the training data.
- As a bag-of-words style model, it does not fully understand sentence structure or negation.
- AI explanations depend on the Groq API being available and configured; if the API key is missing, the app still functions but explanations will show a fallback message.

---

## 👤 Credits

**Developed by:** Shahid Nawaz
**Organization:** SoftaVerse Tech House

---

## 📄 License

This project is developed for educational purposes as part of a machine learning training program.
