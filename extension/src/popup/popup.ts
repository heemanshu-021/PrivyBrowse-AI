document.addEventListener('DOMContentLoaded', async () => {
  const engineStatusEl = document.getElementById('engine-status')!;
  const pageHostEl = document.getElementById('page-host')!;
  const statusMsgEl = document.getElementById('status-message')!;
  const btnAnalyze = document.getElementById('btn-analyze') as HTMLButtonElement;
  const btnAnalyzeText = document.getElementById('btn-analyze-text')!;
  const btnDashboard = document.getElementById('btn-dashboard')!;
  const btnStart = document.getElementById('btn-start')!;
  const btnPause = document.getElementById('btn-pause')!;
  const btnStop = document.getElementById('btn-stop')!;

  function showMessage(text: string, type: 'info' | 'success' | 'error') {
    statusMsgEl.className = `status-message ${type}`;
    statusMsgEl.textContent = text;
  }

  function hideMessage() {
    statusMsgEl.className = 'status-message hidden';
    statusMsgEl.textContent = '';
  }

  // 1. Detect Active Tab
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
    pageHostEl.textContent = 'Unknown Host';
  }

  // 2. Check Backend Health
  try {
    chrome.runtime.sendMessage({ type: 'CONNECTION_STATUS' }, (res) => {
      if (chrome.runtime.lastError || !res || !res.connected) {
        engineStatusEl.className = 'status-pill status-offline';
        engineStatusEl.textContent = 'OFFLINE';
      } else {
        engineStatusEl.className = 'status-pill status-online';
        engineStatusEl.textContent = 'ONLINE';
      }
    });
  } catch {
    engineStatusEl.className = 'status-pill status-offline';
    engineStatusEl.textContent = 'OFFLINE';
  }

  // 3. Analyze Page Trigger
  btnAnalyze.addEventListener('click', async () => {
    hideMessage();
    btnAnalyze.disabled = true;
    btnAnalyzeText.textContent = 'Analyzing Page...';
    showMessage('Capturing viewport and extracting safe DOM...', 'info');

    chrome.runtime.sendMessage({ type: 'ANALYZE_PAGE' }, (response) => {
      btnAnalyze.disabled = false;
      btnAnalyzeText.textContent = 'Analyze Page';

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

  // 4. Agent Control Actions
  btnStart.addEventListener('click', () => {
    showMessage('Agent loop started.', 'info');
  });

  btnPause.addEventListener('click', () => {
    showMessage('Agent paused.', 'info');
  });

  btnStop.addEventListener('click', () => {
    showMessage('Agent stopped.', 'info');
  });

  // 5. Open Web App Dashboard
  btnDashboard.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:5173' });
  });
});
