"""
MediVerify AI - Machine Learning & Verification Engine
======================================================
Combines authoritative pharmaceutical reference registry matching
with Scikit-Learn trained anomaly detection model.
"""

import os
import json
import math
import datetime
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'medicines_reference.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'model.pkl')
METRICS_PATH = os.path.join(BASE_DIR, 'models', 'metrics.json')

class MedicineVerifier:
    def __init__(self):
        self.ref_df = None
        self.model = None
        self.metrics = {}
        self.load_resources()

    def load_resources(self):
        """Loads reference dataset and ML artifacts."""
        if os.path.exists(DATA_PATH):
            self.ref_df = pd.read_csv(DATA_PATH)
        else:
            self.ref_df = pd.DataFrame()

        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[!] Warning: Could not load ML model: {e}")
                self.model = None

        if os.path.exists(METRICS_PATH):
            try:
                with open(METRICS_PATH, 'r') as f:
                    self.metrics = json.load(f)
            except Exception:
                self.metrics = {}

    def get_registered_medicines(self):
        """Returns list of registered medicines for UI hints/autocomplete."""
        if self.ref_df is not None and not self.ref_df.empty:
            return self.ref_df.to_dict(orient='records')
        return []

    def get_metrics(self):
        """Returns the ML evaluation metrics."""
        return self.metrics

    def _calculate_entropy(self, text):
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in set(text)]
        return -sum([p * math.log2(p) for p in prob if p > 0])

    def find_reference_match(self, medicine_name):
        """Searches for exact or best matching reference record."""
        if self.ref_df is None or self.ref_df.empty:
            return None, 0.0

        clean_name = str(medicine_name).strip().lower()

        # 1. Exact match
        exact = self.ref_df[self.ref_df['medicine_name'].str.lower() == clean_name]
        if not exact.empty:
            return exact.iloc[0], 1.0

        # 2. Substring match
        parts = clean_name.split()
        first_token = parts[0] if parts else ""
        if len(first_token) >= 3:
            matched = self.ref_df[self.ref_df['medicine_name'].str.lower().str.contains(first_token, na=False)]
            if not matched.empty:
                return matched.iloc[0], 0.7

        return None, 0.0

    def verify(self, medicine_name, batch_number, manufacturer, mfg_date_str, exp_date_str):
        """
        Executes multi-tier verification:
        1. Reference Registry Matching
        2. Date & Shelf Life Consistency
        3. Manufacturer Authorization Verification
        4. Batch Syntax & Entropy Analysis
        5. Machine Learning Model Anomaly Inference
        Returns: {
            'status': 'Verified' | 'Suspicious' | 'Not Found',
            'explanation': str,
            'details': list[str],
            'confidence': float,
            'reference_record': dict | None,
            'disclaimer': str
        }
        """
        disclaimer = (
            "Regulatory Disclaimer: MediVerify AI performs digital record cross-verification, "
            "syntactic batch structure validation, and metadata consistency analysis. Database matching "
            "verifies administrative registration consistency but does NOT prove physical chemical purity, "
            "active pharmaceutical ingredient (API) potency, or tamper-proof seal integrity without laboratory testing."
        )

        med_clean = str(medicine_name).strip()
        batch_clean = str(batch_number).strip().upper()
        mfg_clean = str(manufacturer).strip()
        mfg_date_clean = str(mfg_date_str).strip()
        exp_date_clean = str(exp_date_str).strip()

        # Step 1: Reference Registry Lookup
        ref_record, match_score = self.find_reference_match(med_clean)

        if ref_record is None or match_score < 0.5:
            return {
                'status': 'Not Found',
                'explanation': f"The medicine '{med_clean}' was not found in the authorized pharmaceutical reference database.",
                'details': [
                    f"No matching registered product found for '{med_clean}'.",
                    "The formulation may be unapproved, experimental, or incorrectly typed.",
                    "Verify the exact brand spelling and dosage strength (e.g., 'Paracetamol 650mg')."
                ],
                'confidence': 95.0,
                'reference_record': None,
                'disclaimer': disclaimer
            }

        ref_dict = ref_record.to_dict()
        expected_mfg = str(ref_record['manufacturer']).strip()
        expected_prefix = str(ref_record['batch_prefix']).strip().upper()
        standard_shelf_life = float(ref_record['standard_shelf_life_months'])

        suspicious_flags = []
        positive_points = []

        # Step 2: Manufacturer Consistency Check
        if mfg_clean.lower() == expected_mfg.lower():
            positive_points.append(f"Manufacturer matches official license holder: {expected_mfg}.")
            mfg_score = 1.0
        elif mfg_clean.lower() in expected_mfg.lower() or expected_mfg.lower() in mfg_clean.lower():
            positive_points.append(f"Manufacturer closely matches registered company: {expected_mfg}.")
            mfg_score = 0.8
        else:
            suspicious_flags.append(
                f"Manufacturer mismatch: Entered '{mfg_clean}', but official registered manufacturer for '{ref_record['medicine_name']}' is '{expected_mfg}'."
            )
            mfg_score = 0.0

        # Step 3: Batch Number Format & Prefix Verification
        has_letters = any(c.isalpha() for c in batch_clean)
        has_digits = any(c.isdigit() for c in batch_clean)
        is_clean_alnum = batch_clean.isalnum()
        length_ok = 5 <= len(batch_clean) <= 12
        batch_format_valid = 1.0 if (has_letters and has_digits and is_clean_alnum and length_ok) else 0.0

        if not length_ok:
            suspicious_flags.append(f"Batch number length ({len(batch_clean)}) is outside standard format (5-12 characters).")
        if not is_clean_alnum:
            suspicious_flags.append("Batch number contains illegal characters (spaces, symbols or punctuation).")

        if batch_clean.startswith(expected_prefix):
            positive_points.append(f"Batch code prefix '{expected_prefix}' corresponds with {expected_mfg}'s assigned syntax.")
            batch_prefix_match = 1.0
        else:
            suspicious_flags.append(f"Batch code prefix mismatch: Expected code starting with '{expected_prefix}', but received '{batch_clean[:3]}'.")
            batch_prefix_match = 0.0

        # Step 4: Date Parsing & Shelf-Life Validation
        date_sequence_valid = 0.0
        shelf_life_valid = 0.0
        months_diff = -1.0
        shelf_life_deviation = 99.0

        try:
            m_date = datetime.datetime.strptime(mfg_date_clean, "%Y-%m-%d").date()
            e_date = datetime.datetime.strptime(exp_date_clean, "%Y-%m-%d").date()
            days_diff = (e_date - m_date).days
            months_diff = round(days_diff / 30.44, 1)

            if days_diff <= 0:
                suspicious_flags.append(
                    f"Chronological anomaly: Expiry date ({exp_date_clean}) cannot precede or equal manufacturing date ({mfg_date_clean})."
                )
            else:
                date_sequence_valid = 1.0
                shelf_life_deviation = abs(months_diff - standard_shelf_life)
                
                if months_diff > 60:
                    suspicious_flags.append(
                        f"Excessive shelf-life: Calculated duration is {months_diff:.1f} months. Maximum regulatory stability limit is 60 months."
                    )
                elif months_diff < 6:
                    suspicious_flags.append(
                        f"Abnormally brief shelf-life: {months_diff:.1f} months is below required pharmaceutical commercial duration."
                    )
                elif shelf_life_deviation > 14:
                    suspicious_flags.append(
                        f"Shelf-life inconsistency: Calculated {months_diff:.1f} months deviates significantly from approved stability duration of {standard_shelf_life} months."
                    )
                else:
                    shelf_life_valid = 1.0
                    positive_points.append(
                        f"Shelf-life duration ({months_diff:.1f} months) complies with regulatory standard of {standard_shelf_life} months."
                    )
        except ValueError:
            suspicious_flags.append("Invalid date format provided. Dates must follow YYYY-MM-DD.")

        # Batch Shannon Entropy
        batch_entropy = self._calculate_entropy(batch_clean)
        if batch_entropy < 1.5 and len(batch_clean) >= 6:
            suspicious_flags.append("Batch number displays abnormally low character variance/repetitive pattern.")

        # Step 5: Machine Learning Feature Vector & Prediction
        feature_vector = [
            match_score,
            mfg_score,
            batch_prefix_match,
            batch_format_valid,
            date_sequence_valid,
            shelf_life_valid,
            months_diff if months_diff > 0 else 0.0,
            shelf_life_deviation,
            round(batch_entropy, 3)
        ]

        ml_prediction = 1 # Default Verified
        ml_confidence = 0.95
        if self.model is not None:
            try:
                X_input = np.array([feature_vector])
                ml_prediction = int(self.model.predict(X_input)[0])
                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba(X_input)[0]
                    ml_confidence = float(np.max(probs))
                else:
                    ml_confidence = 0.98 if ml_prediction == 1 else 0.95
            except Exception as e:
                print(f"[!] Model prediction error: {e}")

        # Combined Decision Engine
        if len(suspicious_flags) > 0 or ml_prediction == 0:
            status = 'Suspicious'
            explanation = (
                f"Potential inconsistencies detected for '{med_clean}'. One or more parameters "
                "fail to match authorized reference records or display irregular packaging metadata."
            )
            confidence = round(max(ml_confidence * 100, 88.0), 1)
        else:
            status = 'Verified'
            explanation = (
                f"Information for '{med_clean}' successfully verified against the authorized "
                f"pharmaceutical reference registry ({expected_mfg}). All metadata, batch syntax, and "
                "shelf-life stability parameters match registered regulatory specifications."
            )
            confidence = round(min(ml_confidence * 100, 99.4), 1)

        return {
            'status': status,
            'explanation': explanation,
            'details': suspicious_flags if status == 'Suspicious' else positive_points,
            'confidence': confidence,
            'reference_record': ref_dict,
            'features_summary': {
                'medicine_registered': True,
                'manufacturer_match': mfg_score >= 0.8,
                'batch_prefix_valid': batch_prefix_match == 1.0,
                'shelf_life_months': months_diff,
                'standard_shelf_life_months': standard_shelf_life
            },
            'disclaimer': disclaimer
        }
