/**
 * MediVerify AI - Analytics Charts Initialization
 * Uses Chart.js to render verification distributions, manufacturer breakdown,
 * verification timeline, and ML model feature importances.
 */

document.addEventListener('DOMContentLoaded', async function () {
  const verdictCanvas = document.getElementById('verdictChart');
  const mfgCanvas = document.getElementById('mfgChart');
  const timelineCanvas = document.getElementById('timelineChart');
  const featuresCanvas = document.getElementById('featuresChart');

  if (!verdictCanvas && !mfgCanvas && !timelineCanvas && !featuresCanvas) {
    return; // Not on the analytics page
  }

  try {
    const res = await fetch('/api/chart-data');
    const data = await res.json();
    const charts = data.charts;
    const mlMetrics = data.ml_metrics;

    // 1. Verdict Distribution Doughnut Chart
    if (verdictCanvas && charts && charts.verdicts) {
      new Chart(verdictCanvas, {
        type: 'doughnut',
        data: {
          labels: ['Verified', 'Suspicious', 'Not Found'],
          datasets: [{
            data: [
              charts.verdicts['Verified'] || 0,
              charts.verdicts['Suspicious'] || 0,
              charts.verdicts['Not Found'] || 0
            ],
            backgroundColor: [
              '#0d9488', // Teal
              '#dc2626', // Red/Danger
              '#64748b'  // Slate Gray
            ],
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 14, font: { family: 'Inter', size: 12 } } },
            tooltip: {
              callbacks: {
                label: function (ctx) {
                  const val = ctx.raw;
                  return ` ${ctx.label}: ${val} record(s)`;
                }
              }
            }
          },
          cutout: '68%'
        }
      });
    }

    // 2. Top Pharmaceutical Manufacturers Bar Chart
    if (mfgCanvas && charts && charts.top_manufacturers) {
      new Chart(mfgCanvas, {
        type: 'bar',
        data: {
          labels: charts.top_manufacturers.labels,
          datasets: [{
            label: 'Verifications Checked',
            data: charts.top_manufacturers.counts,
            backgroundColor: '#1e3a8a',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0, font: { family: 'Inter' } },
              grid: { color: '#f1f5f9' }
            },
            x: {
              ticks: { font: { family: 'Inter', size: 11 } },
              grid: { display: false }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }

    // 3. Verification Activity Timeline Line Chart
    if (timelineCanvas && charts && charts.timeline) {
      new Chart(timelineCanvas, {
        type: 'line',
        data: {
          labels: charts.timeline.dates,
          datasets: [
            {
              label: 'Verified',
              data: charts.timeline.verified,
              borderColor: '#0d9488',
              backgroundColor: 'rgba(13, 148, 136, 0.1)',
              tension: 0.3,
              fill: true
            },
            {
              label: 'Suspicious',
              data: charts.timeline.suspicious,
              borderColor: '#dc2626',
              backgroundColor: 'rgba(220, 38, 38, 0.1)',
              tension: 0.3,
              fill: true
            },
            {
              label: 'Not Found',
              data: charts.timeline.not_found,
              borderColor: '#64748b',
              backgroundColor: 'rgba(100, 116, 139, 0.1)',
              tension: 0.3,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 },
              grid: { color: '#f1f5f9' }
            },
            x: {
              grid: { display: false }
            }
          },
          plugins: {
            legend: { position: 'top', labels: { boxWidth: 14 } }
          }
        }
      });
    }

    // 4. ML Model Feature Importance Horizontal Bar Chart
    if (featuresCanvas && mlMetrics && mlMetrics.feature_importances) {
      const featNames = Object.keys(mlMetrics.feature_importances).map(k => {
        return k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      });
      const featVals = Object.values(mlMetrics.feature_importances);

      new Chart(featuresCanvas, {
        type: 'bar',
        data: {
          labels: featNames,
          datasets: [{
            label: 'Feature Weight / Importance',
            data: featVals,
            backgroundColor: '#0f766e',
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              beginAtZero: true,
              ticks: { font: { family: 'Inter' } },
              grid: { color: '#f1f5f9' }
            },
            y: {
              ticks: { font: { family: 'Inter', size: 11 } },
              grid: { display: false }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }

  } catch (err) {
    console.error('Error rendering analytics charts:', err);
  }
});
