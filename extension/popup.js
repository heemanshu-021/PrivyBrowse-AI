// PrivyBrowse AI - Extension Popup Logic
document.addEventListener('DOMContentLoaded', async () => {
  const engineStatusEl = document.getElementById('engine-status');
  const pageHostEl = document.getElementById('page-host');
  const statusMsgEl = document.getElementById('status-message');
  const btnAnalyze = document.getElementById('btn-analyze');
  const btnAnalyzeText = document.getElementById('btn-analyze-text');
  const btnDashboard = document.getElementById('btn-dashboard');
  const btnStart = document.getElementById('btn-start');
  const btnPause = document.getElementById('btn-pause');
  const btnStop = document.getElementById('btn-stop');

  function showMessage(text, type) {
    if (!statusMsgEl) return;
    statusMsgEl.className = `status-message ${type}`;
    statusMsgEl.textContent = text;
  }

  function hideMessage() {
    if (!statusMsgEl) return;
    statusMsgEl.className = 'status-message hidden';
    statusMsgEl.textContent = '';
  }

  // 1. Detect Active Tab Hostname
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      try {
        const urlObj = new URL(tab.url);
        pageHostEl.textContent = urlObj.hostname || 'Local Frame';
      } catch {
        pageHostEl.textContent = tab.url.substring(0, 24);
      }
    } else {
      pageHostEl.textContent = 'No Active Tab';
    }
  } catch (e) {
    if (pageHostEl) pageHostEl.textContent = 'Unknown Host';
  }

  // 2. Check Backend Health
  try {
    chrome.runtime.sendMessage({ type: 'CONNECTION_STATUS' }, (res) => {
      if (chrome.runtime.lastError || !res || !res.connected) {
        if (engineStatusEl) {
          engineStatusEl.className = 'status-pill status-offline';
          engineStatusEl.textContent = 'OFFLINE';
        }
      } else {
        if (engineStatusEl) {
          engineStatusEl.className = 'status-pill status-online';
          engineStatusEl.textContent = 'ONLINE';
        }
      }
    });
  } catch {
    if (engineStatusEl) {
      engineStatusEl.className = 'status-pill status-offline';
      engineStatusEl.textContent = 'OFFLINE';
    }
  }

  // 3. Analyze Page Action
  if (btnAnalyze) {
    btnAnalyze.addEventListener('click', async () => {
      hideMessage();
      btnAnalyze.disabled = true;
      if (btnAnalyzeText) btnAnalyzeText.textContent = 'Analyzing Page...';
      showMessage('Capturing viewport and extracting safe DOM...', 'info');

      chrome.runtime.sendMessage({ type: 'ANALYZE_PAGE' }, (response) => {
        btnAnalyze.disabled = false;
        if (btnAnalyzeText) btnAnalyzeText.textContent = 'Analyze Page';

        if (chrome.runtime.lastError) {
          showMessage(`Error: ${chrome.runtime.lastError.message}`, 'error');
          return;
        }

        if (response && response.success) {
          const count = response.context?.elements?.length || 0;
          showMessage(`✓ Success! Extracted ${count} interactive controls safely.`, 'success');
        } else {
          showMessage(response?.error || 'Page analysis failed.', 'error');
        }
      });
    });
  }

  if (btnStart) btnStart.addEventListener('click', () => showMessage('Agent loop active.', 'info'));
  if (btnPause) btnPause.addEventListener('click', () => showMessage('Agent loop paused.', 'info'));
  if (btnStop) btnStop.addEventListener('click', () => showMessage('Agent loop stopped.', 'info'));

  if (btnDashboard) {
    btnDashboard.addEventListener('click', () => {
      chrome.tabs.create({ url: 'http://localhost:5173' });
    });
  }
});
