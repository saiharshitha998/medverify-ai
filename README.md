# MediVerify AI - Medicine Authenticity Verification Using Machine Learning

A complete, professional web application designed for **Medicine Authenticity Verification Using Machine Learning**. MediVerify AI allows healthcare workers, pharmacists, and consumers to cross-reference medicine packaging metadata against verified pharmaceutical reference registries and detect counterfeit or suspicious anomalies using a trained Scikit-Learn classification model.

---

## 🌟 Key Features

1. **Dashboard / Home**:
   - Live summary statistics cards: Total verifications, Verified rate (%), Suspicious rate (%), and Registered reference catalog count.
   - 3-step visual workflow explaining how MediVerify AI verifies medicine parameters.
   - Recent verification activity stream with color-coded status badges.

2. **Medicine Verification Engine**:
   - Simple, intuitive verification form:
     - **Medicine Name** (with registered medicine autocomplete)
     - **Batch Number**
     - **Manufacturer Name** (with registered company autocomplete)
     - **Manufacturing Date**
     - **Expiry Date**
   - **One-Click Quick Presets** for easy demonstration:
     - Genuine Verified Sample (e.g. Paracetamol 650mg, Cipla Ltd)
     - Suspicious: Mismatched Manufacturer (e.g. Azithral 500mg by Cipla Ltd instead of Alembic)
     - Suspicious: Chronological Date Error (Expiry precedes Manufacturing Date)
     - Suspicious: Excessive Shelf-Life (12 years duration, violating stability norms)
     - Not Found: Unregistered Formulation
   - Instant dynamic results card displaying **Verified**, **Suspicious**, or **Not Found** with confidence score, itemized analytical breakdown, and regulatory disclaimer.

3. **Verification History**:
   - Persistent logging of every check in a local SQLite database (`mediverify.db`).
   - Filter by status (*All*, *Verified*, *Suspicious*, *Not Found*).
   - Real-time search by medicine name, batch number, or manufacturer.
   - Option to clear history.

4. **Analytics & Machine Learning Performance**:
   - Interactive **Chart.js** visualizations:
     - Verdict Distribution Donut Chart
     - Verifications by Pharmaceutical Manufacturer Bar Chart
     - Verification Timeline Trend Line Chart
   - **ML Performance Dashboard**:
     - Evaluated **Accuracy**, **Precision**, **Recall**, and **F1-Score**.
     - $2 \times 2$ Confusion Matrix table (True Positives, True Negatives, False Positives, False Negatives).
     - Model Feature Importance chart (Shelf-life deviation, Manufacturer match, Batch prefix match, Shannon entropy).
     - Classifier benchmark comparison (Random Forest vs Decision Tree vs Logistic Regression).

5. **About Page & Regulatory Transparency**:
   - Comprehensive explanation of the counterfeit medicine crisis (WHO data).
   - Detailed two-tier architecture explanation.
   - Explicit safety disclaimer explaining why database matching does not prove physical chemical purity.

---

## 🛠 Technology Stack

- **Backend**: Python, Flask
- **Machine Learning**: Scikit-Learn, Pandas, NumPy, Joblib
- **Database**: SQLite3
- **Frontend**: HTML5, Modern CSS3 (White background, Teal & Dark Blue accents), Vanilla JavaScript
- **Visualizations**: Chart.js 4.4

*Note: Built strictly with native HTML/CSS/JS and Flask without React or Streamlit.*

---

## 📂 Project Directory Structure

```
mediverify_ai/
│
├── app.py                      # Main Flask application and API routes
├── database.py                 # SQLite schema, queries, and history management
├── ml_pipeline.py              # Feature extraction & two-tier verification logic
├── train_model.py              # Model training, test evaluation, and artifact generation
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation
│
├── data/
│   └── medicines_reference.csv # Reference catalog of approved medicines & manufacturers
│
├── models/
│   ├── model.pkl               # Trained Scikit-Learn classifier artifact
│   └── metrics.json            # Real computed evaluation metrics (Accuracy, Precision, Recall, F1)
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom Teal & Dark Blue responsive styling
│   └── js/
│       ├── main.js             # Form submission AJAX, presets, and UI handlers
│       └── charts.js           # Chart.js initialization for Analytics dashboard
│
└── templates/
    ├── base.html               # Master layout with top disclaimer, navbar, and footer
    ├── index.html              # Home / Dashboard
    ├── verify.html             # Medicine Verification form & live result card
    ├── history.html            # SQLite verification history table with filters
    ├── analytics.html          # Analytics charts & ML performance dashboard
    └── about.html              # Project documentation, architecture, and disclaimers
```

---

## 🚀 Installation & Running

### Step 1: Navigate to the Project Directory

```powershell
cd C:\Users\SIMRAN\.gemini\antigravity\scratch\mediverify_ai
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 3: (Optional) Re-Train the Machine Learning Model

The trained model and metrics are already saved in `models/`. If you wish to retrain:

```powershell
python train_model.py
```

### Step 4: Run the Flask Web Server

```powershell
python app.py
```

### Step 5: Open the Web Application

Open your web browser and navigate to:

👉 **http://127.0.0.1:5000/**

---

## 🎓 College Project Demonstration Guide

Use this walkthrough during your demonstration:

1. **Dashboard Tour**:
   - Open `http://127.0.0.1:5000/`.
   - Point out the clean teal & dark blue theme, live verification counters, and workflow diagram.
2. **Demonstrate Genuine Verification (Verified)**:
   - Click **Verify Medicine** in the top navigation.
   - Click the quick button **"✓ Genuine Verified Sample"** (Paracetamol 650mg, Batch: `CIP20491`, Manufacturer: `Cipla Ltd`, Dates: `2024-01-15` to `2027-01-14`).
   - Click **Verify Medicine**.
   - Show the green **Verified** badge (99%+ confidence), explanation, and compliance breakdown.
3. **Demonstrate Counterfeit Manufacturer Mismatch (Suspicious)**:
   - Click the quick button **"⚠ Suspicious: Mismatched Manufacturer"** (Azithral 500mg labeled under `Cipla Ltd` instead of the authorized license holder `Alembic Pharmaceuticals`).
   - Click **Verify Medicine**.
   - Show the red **Suspicious** badge highlighting the manufacturer mismatch.
4. **Demonstrate Chronological / Date Anomaly (Suspicious)**:
   - Click **"⚠ Suspicious: Expiry Precedes Mfg Date"** (Pan 40mg with Expiry `2023-05-10` and Mfg `2024-05-10`).
   - Click **Verify Medicine**.
   - Show how the date chronology check and ML feature catch this error.
5. **Demonstrate Unregistered Medicine (Not Found)**:
   - Click **"? Not Found: Unregistered Medicine"** (`NonExistentFormula 100mg`).
   - Show the gray **Not Found** badge indicating absence from authorized catalogs.
6. **Show SQLite History**:
   - Navigate to **Verification History**.
   - Demonstrate the newly logged records, search filter, and status pills.
7. **Show Analytics & Scikit-Learn Metrics**:
   - Navigate to **Analytics & ML**.
   - Highlight the interactive donut, bar, and timeline charts.
   - Showcase the **Accuracy (99.67%)**, **Precision (100.0%)**, **Recall (99.33%)**, and **F1-Score (99.67%)**, along with the Confusion Matrix and Feature Importances.
8. **Show About & Disclaimer**:
   - Navigate to **About Project**.
   - Explain the importance of the regulatory disclaimer: digital metadata verification versus physical chemical assay testing.

---

## ⚠️ Regulatory Disclaimer

*MediVerify AI performs digital record cross-verification, syntactic batch structure validation, and metadata consistency analysis. Database matching verifies administrative registration consistency but does **NOT** prove physical chemical purity, active pharmaceutical ingredient (API) potency, or tamper-proof seal integrity without laboratory testing.*
