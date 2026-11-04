// UVT Chrome Side Panel Controller
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggle-session-btn");
  const passThroughBtn = document.getElementById("pass-through-btn");
  const swapBtn = document.getElementById("swap-lang-btn");
  const sourceLang = document.getElementById("source-lang");
  const targetLang = document.getElementById("target-lang");
  const statusBadge = document.getElementById("connection-status");
  const transcriptFeed = document.getElementById("transcript-feed");

  let isConnected = false;
  let isPassThrough = false;

  // Swap Languages
  swapBtn.addEventListener("click", () => {
    const temp = sourceLang.value;
    sourceLang.value = targetLang.value;
    targetLang.value = temp;
  });

  // Toggle Connection
  toggleBtn.addEventListener("click", () => {
    isConnected = !isConnected;
    if (isConnected) {
      statusBadge.textContent = "Live Translating";
      statusBadge.classList.add("connected");
      toggleBtn.textContent = "Stop Session";
      toggleBtn.style.background = "#ef4444";
      addTranscriptItem("System", "UVT Session initialized with Google ADC authentication.", "sys");
    } else {
      statusBadge.textContent = "Disconnected";
      statusBadge.classList.remove("connected");
      toggleBtn.textContent = "Connect & Start Translation";
      toggleBtn.style.background = "#3b82f6";
      addTranscriptItem("System", "UVT Session stopped.", "sys");
    }
  });

  // Pass Through Mode
  passThroughBtn.addEventListener("click", () => {
    isPassThrough = !isPassThrough;
    passThroughBtn.style.borderColor = isPassThrough ? "#10b981" : "#334155";
    passThroughBtn.style.color = isPassThrough ? "#10b981" : "#f8fafc";
  });

  function addTranscriptItem(speaker, text, type = "user") {
    const emptyMsg = transcriptFeed.querySelector(".transcript-empty");
    if (emptyMsg) emptyMsg.remove();

    const div = document.createElement("div");
    div.style.marginBottom = "8px";
    div.style.fontSize = "13px";
    div.style.lineHeight = "1.4";

    if (type === "sys") {
      div.style.color = "#94a3b8";
      div.style.fontStyle = "italic";
      div.textContent = `[${speaker}] ${text}`;
    } else {
      div.innerHTML = `<strong>${speaker}:</strong> ${text}`;
    }

    transcriptFeed.appendChild(div);
    transcriptFeed.scrollTop = transcriptFeed.scrollHeight;
  }
});
