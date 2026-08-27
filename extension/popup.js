document.getElementById("capture-btn").addEventListener("click", async () => {
  const btn = document.getElementById("capture-btn");
  btn.disabled = true;
  btn.textContent = "Processing locally...";
  
  chrome.runtime.sendMessage({
    type: "CAPTURE_AND_PROCESS",
    task: "Login or browse securely"
  }, (response) => {
    btn.disabled = false;
    btn.textContent = "Connect & Observe Page";
    
    if (chrome.runtime.lastError) {
      alert("Error: " + chrome.runtime.lastError.message);
      return;
    }
    
    if (response && response.success) {
      alert(`Success! Mapped ${response.data.fusedElements.length} elements. Protected ${response.data.piiEntities.length} PII nodes locally.`);
    } else {
      alert("Execution failed: " + (response ? response.error : "Unknown error"));
    }
  });
});
