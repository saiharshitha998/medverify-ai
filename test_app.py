"""
MediVerify AI - Comprehensive Automated Test Suite
===================================================
Tests all Flask endpoints, verification logic, SQLite database operations,
and ML prediction accuracy using Flask's test client.
"""

import unittest
import json
from app import app
from database import get_connection

class MediVerifyTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_home_page(self):
        """Test Dashboard route returns 200 OK and expected content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Medicine Authenticity Verification System', response.data)
        self.assertIn(b'Total Verifications', response.data)

    def test_verify_page(self):
        """Test Medicine Verification page loads form inputs."""
        response = self.client.get('/verify')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Verify Medicine', response.data)
        self.assertIn(b'medicine_name', response.data)
        self.assertIn(b'batch_number', response.data)

    def test_history_page(self):
        """Test Verification History page loads SQLite table."""
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Medicine Verification History', response.data)

    def test_analytics_page(self):
        """Test Analytics page loads charts & ML evaluation metrics."""
        response = self.client.get('/analytics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Machine Learning Model Evaluation', response.data)
        self.assertIn(b'Model Accuracy', response.data)
        self.assertIn(b'Precision Score', response.data)

    def test_about_page(self):
        """Test About page loads architecture and regulatory disclaimer."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About MediVerify AI Project', response.data)
        self.assertIn(b'Critical Regulatory Disclaimer', response.data)

    def test_api_chart_data(self):
        """Test chart data endpoint returns expected JSON structures."""
        response = self.client.get('/api/chart-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('charts', data)
        self.assertIn('ml_metrics', data)
        self.assertIn('verdicts', data['charts'])
        self.assertIn('accuracy', data['ml_metrics'])

    def test_api_verify_genuine(self):
        """Test API verification with genuine medicine returns 'Verified'."""
        payload = {
            'medicine_name': 'Paracetamol 650mg',
            'batch_number': 'CIP20491',
            'manufacturer': 'Cipla Ltd',
            'mfg_date': '2024-01-15',
            'exp_date': '2027-01-14'
        }
        response = self.client.post('/api/verify',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['success'])
        self.assertEqual(data['result']['status'], 'Verified')
        self.assertIn('Cipla Ltd', data['result']['explanation'])
        self.assertIn('disclaimer', data['result'])

    def test_api_verify_suspicious_manufacturer(self):
        """Test API verification with mismatched manufacturer returns 'Suspicious'."""
        payload = {
            'medicine_name': 'Azithral 500mg',
            'batch_number': 'ALM33921',
            'manufacturer': 'Cipla Ltd', # Incorrect! Authorized is Alembic Pharmaceuticals
            'mfg_date': '2024-03-01',
            'exp_date': '2027-03-01'
        }
        response = self.client.post('/api/verify',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['success'])
        self.assertEqual(data['result']['status'], 'Suspicious')
        self.assertIn('inconsistencies', data['result']['explanation'].lower())

    def test_api_verify_suspicious_dates(self):
        """Test API verification with invalid date sequence returns 'Suspicious'."""
        payload = {
            'medicine_name': 'Pan 40mg',
            'batch_number': 'ALK67123',
            'manufacturer': 'Alkem Laboratories',
            'mfg_date': '2024-05-10',
            'exp_date': '2023-05-10' # Expiry is BEFORE manufacturing date!
        }
        response = self.client.post('/api/verify',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['success'])
        self.assertEqual(data['result']['status'], 'Suspicious')

    def test_api_verify_not_found(self):
        """Test API verification with unknown medicine returns 'Not Found'."""
        payload = {
            'medicine_name': 'FakeUnknownMed 999mg',
            'batch_number': 'FAKE123',
            'manufacturer': 'BlackMarket Labs',
            'mfg_date': '2024-01-01',
            'exp_date': '2026-01-01'
        }
        response = self.client.post('/api/verify',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(data['success'])
        self.assertEqual(data['result']['status'], 'Not Found')
        self.assertIn('not found', data['result']['explanation'].lower())

    def test_sqlite_persistence(self):
        """Ensure test verifications are recorded in SQLite."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM verification_history WHERE medicine_name = 'Paracetamol 650mg'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0)

if __name__ == '__main__':
    unittest.main()
