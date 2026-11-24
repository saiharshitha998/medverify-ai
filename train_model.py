"""
Medicine Authenticity Verification Using Machine Learning
Model Training & Evaluation Script
=========================================================
Trains a Machine Learning classification model on pharmaceutical verification
features derived from authentic reference registries and regulatory anomaly patterns.
Calculates Accuracy, Precision, Recall, and F1-score and exports the trained model.
"""

import os
import json
import math
import random
import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import joblib

def calculate_entropy(text):
    """Calculates Shannon entropy of a string (batch number character randomness)."""
    if not text:
        return 0.0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    return -sum([p * math.log2(p) for p in prob if p > 0])

def extract_features(medicine_name, manufacturer, batch_number, mfg_date_str, exp_date_str, ref_df):
    """
    Extracts a numerical feature vector characterizing authenticity consistency.
    """
    med_name_clean = str(medicine_name).strip().lower()
    mfg_clean = str(manufacturer).strip().lower()
    batch_clean = str(batch_number).strip().upper()
    
    # 1. Match against reference records
    exact_med = ref_df[ref_df['medicine_name'].str.lower() == med_name_clean]
    if exact_med.empty:
        # Partial match
        matches = ref_df[ref_df['medicine_name'].str.lower().str.contains(med_name_clean.split()[0], na=False)]
        ref_record = matches.iloc[0] if not matches.empty else None
    else:
        ref_record = exact_med.iloc[0]

    # Feature 1: Medicine Registry Match (1.0 exact/high, 0.5 partial, 0.0 unknown)
    if not exact_med.empty:
        name_match_score = 1.0
    elif ref_record is not None:
        name_match_score = 0.6
    else:
        name_match_score = 0.0

    # Feature 2: Manufacturer Match
    if ref_record is not None:
        ref_mfg = str(ref_record['manufacturer']).strip().lower()
        if ref_mfg == mfg_clean:
            mfg_match_score = 1.0
        elif mfg_clean in ref_mfg or ref_mfg in mfg_clean:
            mfg_match_score = 0.8
        else:
            mfg_match_score = 0.0
    else:
        mfg_match_score = 0.0

    # Feature 3: Batch Prefix Match
    if ref_record is not None and pd.notna(ref_record.get('batch_prefix')):
        expected_prefix = str(ref_record['batch_prefix']).strip().upper()
        batch_prefix_match = 1.0 if batch_clean.startswith(expected_prefix) else 0.0
    else:
        batch_prefix_match = 0.5 if len(batch_clean) >= 3 else 0.0

    # Feature 4: Batch Structure Valid (alphanumeric, length 6-12, uppercase)
    has_letters = any(c.isalpha() for c in batch_clean)
    has_digits = any(c.isdigit() for c in batch_clean)
    no_special = batch_clean.isalnum()
    length_ok = 5 <= len(batch_clean) <= 12
    batch_format_valid = 1.0 if (has_letters and has_digits and no_special and length_ok) else 0.0

    # Feature 5 & 6: Shelf Life Calculation & Sequence
    try:
        mfg_date = datetime.datetime.strptime(str(mfg_date_str).strip(), "%Y-%m-%d").date()
        exp_date = datetime.datetime.strptime(str(exp_date_str).strip(), "%Y-%m-%d").date()
        
        days_diff = (exp_date - mfg_date).days
        months_diff = days_diff / 30.44
        date_sequence_valid = 1.0 if days_diff > 0 else 0.0
    except Exception:
        months_diff = -1.0
        date_sequence_valid = 0.0

    # Feature 7: Shelf Life Deviation from standard regulatory norms (typically 24 to 36 months)
    standard_shelf_life = float(ref_record['standard_shelf_life_months']) if ref_record is not None else 36.0
    if months_diff > 0:
        shelf_life_deviation = abs(months_diff - standard_shelf_life)
        # Check if shelf life is within standard stability limits (6 to 60 months max)
        shelf_life_valid = 1.0 if (6.0 <= months_diff <= 60.0 and shelf_life_deviation <= 14.0) else 0.0
    else:
        shelf_life_deviation = 99.0
        shelf_life_valid = 0.0

    # Feature 8: Batch Shannon Entropy
    batch_entropy = calculate_entropy(batch_clean)

    return [
        name_match_score,
        mfg_match_score,
        batch_prefix_match,
        batch_format_valid,
        date_sequence_valid,
        shelf_life_valid,
        round(months_diff, 2),
        round(shelf_life_deviation, 2),
        round(batch_entropy, 3)
    ]

def generate_synthetic_surveillance_dataset(ref_df, n_samples=1400):
    """
    Constructs a calibrated dataset of verified and suspicious pharmaceutical records
    representing real-world surveillance patterns.
    """
    random.seed(42)
    np.random.seed(42)
    records = []

    med_list = ref_df.to_dict('records')

    for i in range(n_samples):
        # 50% Verified, 50% Suspicious / Anomaly cases
        is_verified = (i % 2 == 0)
        ref = random.choice(med_list)

        if is_verified:
            # Genuine authorized record
            med_name = ref['medicine_name']
            manufacturer = ref['manufacturer']
            prefix = ref['batch_prefix']
            batch_num = f"{prefix}{random.randint(10000, 99999)}"
            
            # Realistic manufacturing date within last 2 years
            start_date = datetime.date(2023, 1, 1)
            random_days = random.randint(0, 700)
            mfg_date = start_date + datetime.timedelta(days=random_days)
            
            # Standard shelf life months
            shelf_months = int(ref['standard_shelf_life_months'])
            # Add small realistic variance
            variance = random.choice([-2, -1, 0, 1, 2])
            shelf_months = max(12, shelf_months + variance)
            exp_date = mfg_date + datetime.timedelta(days=int(shelf_months * 30.44))

            # Introduce 3.5% realistic real-world noise (e.g. legacy batch formatting, minor data entry discrepancy)
            if random.random() < 0.035:
                batch_num = f"{prefix}-{random.randint(1000, 9999)}" # Hyphenated legacy batch

            label = 1 # Verified
        else:
            # Suspicious / Counterfeit / Inconsistent anomaly
            anomaly_type = random.choice([
                "mismatched_manufacturer",
                "invalid_batch_prefix",
                "illegal_batch_chars",
                "negative_shelf_life",
                "excessive_shelf_life",
                "unrealistic_short_shelf_life",
                "repetitive_batch",
                "subtle_batch_mismatch"
            ])
            med_name = ref['medicine_name']
            
            if anomaly_type == "mismatched_manufacturer":
                # Pick a completely different manufacturer
                other_ref = random.choice([m for m in med_list if m['manufacturer'] != ref['manufacturer']])
                manufacturer = other_ref['manufacturer']
                batch_num = f"{ref['batch_prefix']}{random.randint(10000, 99999)}"
                mfg_date = datetime.date(2024, 2, 1)
                exp_date = mfg_date + datetime.timedelta(days=int(ref['standard_shelf_life_months'] * 30.44))

            elif anomaly_type == "invalid_batch_prefix":
                manufacturer = ref['manufacturer']
                # Wrong prefix (e.g. FAKE, XYZ, or 999)
                batch_num = f"XYZ{random.randint(10000, 99999)}"
                mfg_date = datetime.date(2024, 3, 1)
                exp_date = mfg_date + datetime.timedelta(days=int(ref['standard_shelf_life_months'] * 30.44))

            elif anomaly_type == "illegal_batch_chars":
                manufacturer = ref['manufacturer']
                batch_num = f"{ref['batch_prefix']}#{random.randint(10, 99)}*"
                mfg_date = datetime.date(2024, 1, 1)
                exp_date = mfg_date + datetime.timedelta(days=int(ref['standard_shelf_life_months'] * 30.44))

            elif anomaly_type == "negative_shelf_life":
                manufacturer = ref['manufacturer']
                batch_num = f"{ref['batch_prefix']}{random.randint(10000, 99999)}"
                mfg_date = datetime.date(2024, 6, 1)
                # Expiry is BEFORE manufacturing date (glaring counterfeit relabeling error)
                exp_date = datetime.date(2023, 6, 1)

            elif anomaly_type == "excessive_shelf_life":
                manufacturer = ref['manufacturer']
                batch_num = f"{ref['batch_prefix']}{random.randint(10000, 99999)}"
                mfg_date = datetime.date(2024, 1, 1)
                # 10 years shelf life (counterfeit stability violation)
                exp_date = datetime.date(2034, 1, 1)

            elif anomaly_type == "unrealistic_short_shelf_life":
                manufacturer = ref['manufacturer']
                batch_num = f"{ref['batch_prefix']}{random.randint(10000, 99999)}"
                mfg_date = datetime.date(2024, 1, 1)
                # Only 10 days shelf life
                exp_date = mfg_date + datetime.timedelta(days=10)

            elif anomaly_type == "subtle_batch_mismatch":
                manufacturer = ref['manufacturer']
                # Subtly wrong batch length or slight suffix deviation
                batch_num = f"{ref['batch_prefix']}9" # Too short
                mfg_date = datetime.date(2024, 1, 1)
                exp_date = mfg_date + datetime.timedelta(days=int(ref['standard_shelf_life_months'] * 30.44))

            elif anomaly_type == "repetitive_batch":
                manufacturer = ref['manufacturer']
                batch_num = "AAAA0000"
                mfg_date = datetime.date(2024, 1, 1)
                exp_date = mfg_date + datetime.timedelta(days=730)

            label = 0 # Suspicious

        features = extract_features(
            med_name, manufacturer, batch_num,
            mfg_date.strftime("%Y-%m-%d"),
            exp_date.strftime("%Y-%m-%d"),
            ref_df
        )

        records.append({
            'medicine_name': med_name,
            'manufacturer': manufacturer,
            'batch_number': batch_num,
            'mfg_date': mfg_date.strftime("%Y-%m-%d"),
            'exp_date': exp_date.strftime("%Y-%m-%d"),
            'features': features,
            'label': label
        })

    return records

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'medicines_reference.csv')
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)

    print(f"[*] Loading reference dataset from: {data_path}")
    ref_df = pd.read_csv(data_path)
    print(f"[*] Reference catalog contains {len(ref_df)} registered pharmaceutical formulations.")

    print("[*] Generating calibrated surveillance verification dataset...")
    records = generate_synthetic_surveillance_dataset(ref_df, n_samples=1500)
    
    feature_names = [
        'name_match_score',
        'mfg_match_score',
        'batch_prefix_match',
        'batch_format_valid',
        'date_sequence_valid',
        'shelf_life_valid',
        'shelf_life_months',
        'shelf_life_deviation',
        'batch_entropy'
    ]

    X = np.array([r['features'] for r in records])
    y = np.array([r['label'] for r in records])

    print(f"[*] Total dataset size: {X.shape[0]} samples with {X.shape[1]} features.")
    print(f"[*] Label distribution: {np.bincount(y)} (0: Suspicious, 1: Verified)")

    # 80-20 Train-Test Split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"[*] Train set size: {X_train.shape[0]}, Test set size: {X_test.shape[0]}")

    # Train and evaluate multiple models
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=6, random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42)
    }

    results = {}
    best_model_name = "Random Forest"
    best_model = None
    best_f1 = 0.0

    print("\n" + "="*50)
    print(" MODEL PERFORMANCE EVALUATION COMPARISON")
    print("="*50)

    for name, clf in models.items():
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        results[name] = {
            'accuracy': round(float(acc), 4),
            'precision': round(float(prec), 4),
            'recall': round(float(rec), 4),
            'f1_score': round(float(f1), 4)
        }

        print(f"\nModel: {name}")
        print(f"  Accuracy : {acc * 100:.2f}%")
        print(f"  Precision: {prec * 100:.2f}%")
        print(f"  Recall   : {rec * 100:.2f}%")
        print(f"  F1-Score : {f1 * 100:.2f}%")

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = clf

    # Final detailed evaluation of the chosen best model
    print("\n" + "="*50)
    print(f" SELECTED BEST MODEL: {best_model_name}")
    print("="*50)
    
    y_test_pred = best_model.predict(X_test)
    cm = confusion_matrix(y_test, y_test_pred)
    class_report = classification_report(y_test, y_test_pred, target_names=['Suspicious', 'Verified'], output_dict=True)

    print("Confusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y_test, y_test_pred, target_names=['Suspicious', 'Verified']))

    # Feature Importance (if tree-based)
    feature_importances = {}
    if hasattr(best_model, 'feature_importances_'):
        for fname, imp in zip(feature_names, best_model.feature_importances_):
            feature_importances[fname] = round(float(imp), 4)
            print(f"  {fname:25s}: {imp:.4f}")

    # Save model artifact
    model_path = os.path.join(models_dir, 'model.pkl')
    joblib.dump(best_model, model_path)
    print(f"\n[+] Saved trained model to: {model_path}")

    # Export full metrics to JSON
    metrics_data = {
        'model_name': best_model_name,
        'all_models_comparison': results,
        'accuracy': results[best_model_name]['accuracy'],
        'precision': results[best_model_name]['precision'],
        'recall': results[best_model_name]['recall'],
        'f1_score': results[best_model_name]['f1_score'],
        'confusion_matrix': cm.tolist(),
        'classification_report': class_report,
        'feature_importances': feature_importances,
        'feature_names': feature_names,
        'test_samples_count': int(len(y_test)),
        'train_samples_count': int(len(y_train)),
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    metrics_path = os.path.join(models_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=4)
    print(f"[+] Saved evaluation metrics to: {metrics_path}")
    print("[+] Model training pipeline completed successfully!")

if __name__ == '__main__':
    main()
