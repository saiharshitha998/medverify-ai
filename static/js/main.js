/**
 * MediVerify AI - Frontend Interactive Controller
 * Handles live verification AJAX requests, sample presets, and UI events.
 */

document.addEventListener('DOMContentLoaded', function () {
  // --- Verification Form Submission ---
  const verifyForm = document.getElementById('medicineVerifyForm');
  const verifyBtn = document.getElementById('verifySubmitBtn');
  const resultCard = document.getElementById('verificationResultCard');
  const resultAlert = document.getElementById('formAlert');

  if (verifyForm) {
    verifyForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      // UI Loading state
      if (verifyBtn) {
        verifyBtn.disabled = true;
        verifyBtn.innerHTML = '<span class="spinner"></span> Verifying with ML Engine...';
      }
      if (resultAlert) {
        resultAlert.style.display = 'none';
      }

      const payload = {
        medicine_name: document.getElementById('medicine_name').value.trim(),
        batch_number: document.getElementById('batch_number').value.trim(),
        manufacturer: document.getElementById('manufacturer').value.trim(),
        mfg_date: document.getElementById('mfg_date').value.trim(),
        exp_date: document.getElementById('exp_date').value.trim()
      };

      try {
        const response = await fetch('/api/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
          displayVerificationResult(data.result);
        } else {
          showFormAlert(data.message || 'Verification failed. Please check inputs.');
        }
      } catch (err) {
        console.error('Verification error:', err);
        showFormAlert('Network error occurred while connecting to MediVerify AI server.');
      } finally {
        if (verifyBtn) {
          verifyBtn.disabled = false;
          verifyBtn.innerHTML = 'Verify Medicine';
        }
      }
    });
  }

  function showFormAlert(message) {
    if (!resultAlert) return;
    resultAlert.textContent = message;
    resultAlert.style.display = 'block';
  }

  function displayVerificationResult(res) {
    if (!resultCard) return;

    // Reset classes
    resultCard.className = 'result-card';

    const statusBadge = document.getElementById('resultStatusBadge');
    const confidenceText = document.getElementById('resultConfidenceText');
    const explanationText = document.getElementById('resultExplanation');
    const detailsList = document.getElementById('resultDetailsList');
    const disclaimerText = document.getElementById('resultDisclaimerText');

    let badgeClass = '';
    let badgeIcon = '';

    if (res.status === 'Verified') {
      badgeClass = 'badge-verified';
      badgeIcon = '✓';
      resultCard.classList.add('status-verified');
    } else if (res.status === 'Suspicious') {
      badgeClass = 'badge-suspicious';
      badgeIcon = '⚠';
      resultCard.classList.add('status-suspicious');
    } else {
      badgeClass = 'badge-notfound';
      badgeIcon = '?';
      resultCard.classList.add('status-notfound');
    }

    if (statusBadge) {
      statusBadge.className = `result-badge-large ${badgeClass}`;
      statusBadge.innerHTML = `<span>${badgeIcon}</span> ${res.status}`;
    }

    if (confidenceText) {
      confidenceText.textContent = `Confidence: ${res.confidence}%`;
    }

    if (explanationText) {
      explanationText.textContent = res.explanation;
    }

    if (detailsList) {
      detailsList.innerHTML = '';
      if (res.details && res.details.length > 0) {
        res.details.forEach(detail => {
          const li = document.createElement('li');
          li.innerHTML = `<strong>•</strong> <span>${detail}</span>`;
          detailsList.appendChild(li);
        });
      }
    }

    if (disclaimerText) {
      disclaimerText.textContent = res.disclaimer;
    }

    resultCard.style.display = 'block';
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // --- Sample Preset Loaders for Quick College Project Demonstration ---
  window.loadSample = function (type) {
    const medInput = document.getElementById('medicine_name');
    const batchInput = document.getElementById('batch_number');
    const mfgInput = document.getElementById('manufacturer');
    const mfgDateInput = document.getElementById('mfg_date');
    const expDateInput = document.getElementById('exp_date');

    if (!medInput) return;

    if (type === 'verified') {
      medInput.value = 'Paracetamol 650mg';
      batchInput.value = 'CIP20491';
      mfgInput.value = 'Cipla Ltd';
      mfgDateInput.value = '2024-01-15';
      expDateInput.value = '2027-01-14';
    } else if (type === 'suspicious_mfg') {
      // Mismatched manufacturer (Azithral is Alembic, not Cipla)
      medInput.value = 'Azithral 500mg';
      batchInput.value = 'ALM33921';
      mfgInput.value = 'Cipla Ltd';
      mfgDateInput.value = '2024-03-01';
      expDateInput.value = '2027-03-01';
    } else if (type === 'suspicious_dates') {
      // Expiry is before manufacturing date
      medInput.value = 'Pan 40mg';
      batchInput.value = 'ALK67123';
      mfgInput.value = 'Alkem Laboratories';
      mfgDateInput.value = '2024-05-10';
      expDateInput.value = '2023-05-10';
    } else if (type === 'suspicious_shelf_life') {
      // Excessive shelf life (12 years)
      medInput.value = 'Dolo 650mg';
      batchInput.value = 'MIC89301';
      mfgInput.value = 'Micro Labs Ltd';
      mfgDateInput.value = '2024-01-01';
      expDateInput.value = '2036-01-01';
    } else if (type === 'not_found') {
      medInput.value = 'NonExistentFormula 100mg';
      batchInput.value = 'UNKNOWN12';
      mfgInput.value = 'Random Pharma Care';
      mfgDateInput.value = '2024-02-01';
      expDateInput.value = '2026-02-01';
    }

    if (resultCard) {
      resultCard.style.display = 'none';
    }
  };

  // --- Reset/Clear Form ---
  window.resetVerifyForm = function () {
    if (verifyForm) verifyForm.reset();
    if (resultCard) resultCard.style.display = 'none';
    if (resultAlert) resultAlert.style.display = 'none';
  };

  // --- Clear History Action ---
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', async function () {
      if (confirm('Are you sure you want to clear all verification history records?')) {
        try {
          const resp = await fetch('/api/clear-history', { method: 'POST' });
          const json = await resp.json();
          if (json.success) {
            window.location.reload();
          }
        } catch (e) {
          alert('Could not clear history.');
        }
      }
    });
  }
});
