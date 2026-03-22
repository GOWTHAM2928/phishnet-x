// PhishNet X — Background Service Worker
// Handles auto-scanning of URLs on every tab update

const API_BASE = "http://localhost:8000";
const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes
const DEBOUNCE_MS = 800;

// In-memory scan cache: url -> { result, timestamp }
const scanCache = new Map();

// Debounce timers per tab
const debounceTimers = new Map();

// Current scan results per tab: tabId -> result
const tabResults = new Map();

// ─── Utility ──────────────────────────────────────────────

function getCached(url) {
  const entry = scanCache.get(url);
  if (!entry) return null;
  if (Date.now() - entry.timestamp > CACHE_DURATION_MS) {
    scanCache.delete(url);
    return null;
  }
  return entry.result;
}

function setCache(url, result) {
  scanCache.set(url, { result, timestamp: Date.now() });
  // Prevent memory leak — keep max 200 entries
  if (scanCache.size > 200) {
    const firstKey = scanCache.keys().next().value;
    scanCache.delete(firstKey);
  }
}

function shouldSkipUrl(url) {
  if (!url) return true;
  const skip = [
    "chrome://", "chrome-extension://", "about:", "data:",
    "file://", "javascript:", "edge://", "moz-extension://"
  ];
  return skip.some(prefix => url.startsWith(prefix));
}

function updateExtensionIcon(tabId, status) {
  const icons = {
    safe:       { color: "#22c55e", text: "✓" },
    suspicious: { color: "#f59e0b", text: "!" },
    phishing:   { color: "#ef4444", text: "✗" },
    scanning:   { color: "#6366f1", text: "…" },
    unknown:    { color: "#94a3b8", text: "?" }
  };

  const icon = icons[status] || icons.unknown;

  // Update badge
  chrome.action.setBadgeText({
    tabId,
    text: status === "safe" ? "✓" : status === "suspicious" ? "!" : status === "phishing" ? "✗" : "…"
  });

  chrome.action.setBadgeBackgroundColor({
    tabId,
    color: icon.color
  });
}

// ─── Core scan function ───────────────────────────────────

async function scanUrl(url, tabId) {
  // Check cache first
  const cached = getCached(url);
  if (cached) {
    tabResults.set(tabId, cached);
    updateExtensionIcon(tabId, cached.status);
    notifyContentScript(tabId, cached);
    return cached;
  }

  // Show scanning state
  updateExtensionIcon(tabId, "scanning");
  tabResults.set(tabId, { status: "scanning", url });

  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(8000) // 8s timeout
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();

    // Cache and store result
    setCache(url, result);
    tabResults.set(tabId, result);
    updateExtensionIcon(tabId, result.status);

    // Notify content script
    notifyContentScript(tabId, result);

    // Show notification for phishing/suspicious
    if (result.status === "phishing") {
      showNotification(url, result);
    }

    return result;

  } catch (error) {
    const errorResult = {
      url,
      status: "unknown",
      risk_score: 0,
      reasons: ["Could not connect to PhishNet X backend. Make sure the server is running."],
      error: error.message
    };
    tabResults.set(tabId, errorResult);
    updateExtensionIcon(tabId, "unknown");
    return errorResult;
  }
}

// ─── Content script communication ────────────────────────

function notifyContentScript(tabId, result) {
  chrome.tabs.sendMessage(tabId, {
    type: "PHISHNET_RESULT",
    data: result
  }).catch(() => {
    // Content script not ready yet — ignore
  });
}

// ─── Notification system ──────────────────────────────────

function showNotification(url, result) {
  const domain = new URL(url).hostname;
  chrome.notifications.create(`phish-${Date.now()}`, {
    type: "basic",
    iconUrl: "icons/icon48.png",
    title: "🚨 PhishNet X: Phishing Detected!",
    message: `${domain} — Risk Score: ${result.risk_score}/100\n${result.reasons?.[0] || ""}`,
    priority: 2
  });
}

// ─── Tab event listeners ──────────────────────────────────

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only scan when the URL is committed (page navigation)
  if (changeInfo.status !== "loading") return;
  if (!tab.url) return;
  if (shouldSkipUrl(tab.url)) return;

  const url = tab.url;

  // Debounce: cancel previous timer for this tab
  if (debounceTimers.has(tabId)) {
    clearTimeout(debounceTimers.get(tabId));
  }

  const timer = setTimeout(() => {
    debounceTimers.delete(tabId);
    scanUrl(url, tabId);
  }, DEBOUNCE_MS);

  debounceTimers.set(tabId, timer);
});

chrome.tabs.onRemoved.addListener((tabId) => {
  tabResults.delete(tabId);
  if (debounceTimers.has(tabId)) {
    clearTimeout(debounceTimers.get(tabId));
    debounceTimers.delete(tabId);
  }
});

// ─── Message handler (from popup/content scripts) ─────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  // Popup requesting current tab result
  if (message.type === "GET_RESULT") {
    const tabId = message.tabId;
    const result = tabResults.get(tabId);
    sendResponse({ result: result || null });
    return true;
  }

  // Popup requesting a manual scan
  if (message.type === "SCAN_URL") {
    const { url, tabId } = message;
    scanUrl(url, tabId).then(result => sendResponse({ result }));
    return true; // Keep channel open for async
  }

  // Chat message
  if (message.type === "CHAT") {
    const { userMessage, context } = message;
    fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage, context }),
      signal: AbortSignal.timeout(10000)
    })
    .then(r => r.json())
    .then(data => sendResponse({ reply: data.reply }))
    .catch(err => sendResponse({
      reply: "⚠️ Could not connect to the PhishNet X assistant. Please make sure the backend server is running at localhost:8000."
    }));
    return true;
  }
});
