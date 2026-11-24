"""
MediVerify AI - Flask Application Backend
==========================================
Main web server providing medicine authenticity verification,
analytics, history logs, and machine learning inference.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from database import (
    init_db, add_verification_record, get_history, 
    get_stats, get_chart_data, clear_all_history
)
from ml_pipeline import MedicineVerifier

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mediverify-secure-token-2026'

# Initialize database and verification engine
init_db()
verifier = MedicineVerifier()

@app.route('/')
def home():
    """Home / Dashboard page with welcome message and verification stats."""
    stats = get_stats()
    recent_history = get_history(limit=6)
    registered_meds = verifier.get_registered_medicines()
    return render_template(
        'index.html',
        stats=stats,
        recent_history=recent_history,
        total_registered_meds=len(registered_meds)
    )

@app.route('/verify', methods=['GET'])
def verify_page():
    """Medicine Verification Form page."""
    registered_meds = verifier.get_registered_medicines()
    return render_template('verify.html', registered_meds=registered_meds)

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """API endpoint to execute medicine verification and log to SQLite."""
    data = request.get_json(silent=True) or request.form

    med_name = data.get('medicine_name', '').strip()
    batch_num = data.get('batch_number', '').strip()
    manufacturer = data.get('manufacturer', '').strip()
    mfg_date = data.get('mfg_date', '').strip()
    exp_date = data.get('exp_date', '').strip()

    if not med_name or not batch_num or not manufacturer or not mfg_date or not exp_date:
        return jsonify({
            'success': False,
            'message': 'Please fill in all required verification fields.'
        }), 400

    # Run verification pipeline
    result = verifier.verify(
        medicine_name=med_name,
        batch_number=batch_num,
        manufacturer=manufacturer,
        mfg_date_str=mfg_date,
        exp_date_str=exp_date
    )

    # Save to SQLite database
    record_id = add_verification_record(
        medicine_name=med_name,
        batch_number=batch_num,
        manufacturer=manufacturer,
        mfg_date=mfg_date,
        exp_date=exp_date,
        result=result['status'],
        explanation=result['explanation'],
        confidence=result.get('confidence', 95.0)
    )

    return jsonify({
        'success': True,
        'record_id': record_id,
        'result': result
    })

@app.route('/history')
def history_page():
    """Verification History page showing SQLite log table."""
    filter_result = request.args.get('filter', 'all')
    search_query = request.args.get('q', '').strip()
    history = get_history(limit=100, filter_result=filter_result, search_query=search_query)
    stats = get_stats()
    return render_template(
        'history.html',
        history=history,
        stats=stats,
        current_filter=filter_result,
        search_query=search_query
    )

@app.route('/analytics')
def analytics_page():
    """Analytics page with interactive charts & ML performance metrics."""
    stats = get_stats()
    ml_metrics = verifier.get_metrics()
    return render_template(
        'analytics.html',
        stats=stats,
        ml_metrics=ml_metrics
    )

@app.route('/about')
def about_page():
    """About page with technical architecture, problem statement, and disclaimers."""
    registered_meds = verifier.get_registered_medicines()
    return render_template('about.html', registered_count=len(registered_meds))

@app.route('/api/chart-data')
def api_chart_data():
    """Returns JSON data for frontend Chart.js rendering."""
    chart_data = get_chart_data()
    ml_metrics = verifier.get_metrics()
    return jsonify({
        'charts': chart_data,
        'ml_metrics': ml_metrics
    })

@app.route('/api/clear-history', methods=['POST'])
def api_clear_history():
    """Resets verification history."""
    clear_all_history()
    return jsonify({'success': True, 'message': 'History cleared successfully.'})

@app.route('/api/medicines')
def api_medicines():
    """Returns list of registered medicines."""
    return jsonify(verifier.get_registered_medicines())

if __name__ == '__main__':
    print("=" * 60)
    print(" MediVerify AI - Medicine Authenticity Verification Server")
    print(" Running at: http://127.0.0.1:5000/")
    print(" Press Ctrl+C to stop the server.")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
