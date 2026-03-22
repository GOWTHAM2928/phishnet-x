// PhishNet X — Content Script
// Injects overlay warnings on phishing/suspicious pages

(function () {
  "use strict";

  let warningBanner = null;
  let currentStatus = null;

  // ─── Banner creation ──────────────────────────────────

  function createBanner(result) {
    removeBanner();

    const { status, risk_score, reasons, url } = result;
    if (status === "scanning" || status === "unknown") return;

    // Green transient popup for safe sites
    if (status === "safe") {
      showSafePopup();
      return;
    }

    const isPhishing = status === "phishing";
    const isSuspicious = status === "suspicious";

    const banner = document.createElement("div");
    banner.id = "phishnet-x-banner";

    const colors = {
      phishing:   { bg: "#fef2f2", border: "#fca5a5", accent: "#dc2626", text: "#7f1d1d", icon: "🚨" },
      suspicious: { bg: "#fffbeb", border: "#fcd34d", accent: "#d97706", text: "#78350f", icon: "⚠️" }
    };

    const c = colors[status];
    const topReason = reasons?.[0] || "Suspicious patterns detected";
    const reasonsHtml = (reasons || []).slice(0, 3).map(r =>
      `<li style="margin:4px 0; font-size:12px; color:${c.text}; opacity:0.9;">• ${r}</li>`
    ).join("");

    banner.innerHTML = `
      <div id="phishnet-inner" style="
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 2147483647;
        background: ${c.bg};
        border-bottom: 3px solid ${c.border};
        padding: 12px 16px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
        box-shadow: 0 4px 24px rgba(0,0,0,0.12);
        backdrop-filter: blur(12px);
        animation: phishnet-slide-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      ">
        <div style="font-size:28px; line-height:1; flex-shrink:0; margin-top:2px;">${c.icon}</div>
        <div style="flex:1; min-width:0;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
            <strong style="font-size:14px; color:${c.accent}; font-weight:700; letter-spacing:-0.01em;">
              ${isPhishing ? "⛔ Phishing Site Detected" : "⚠️ Suspicious Site"} — Risk Score: ${risk_score}/100
            </strong>
            <button id="phishnet-close" style="
              background: none; border: none; cursor: pointer;
              font-size: 18px; color: ${c.text}; opacity: 0.6;
              padding: 0 4px; line-height:1; flex-shrink:0;
            " title="Dismiss">×</button>
          </div>
          <p style="margin:0 0 6px; font-size:13px; color:${c.text}; font-weight:500;">${topReason}</p>
          ${reasons?.length > 1 ? `<ul style="margin:0; padding:0; list-style:none;">${reasonsHtml}</ul>` : ""}
          ${isPhishing ? `<p style="margin:8px 0 0; font-size:12px; font-weight:600; color:${c.accent};">
            Do NOT enter passwords, credit cards, or personal information on this site.
          </p>` : ""}
        </div>
      </div>
      <style>
        @keyframes phishnet-slide-in {
          from { transform: translateY(-100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes phishnet-slide-out {
          from { transform: translateY(0); opacity: 1; }
          to { transform: translateY(-100%); opacity: 0; }
        }
      </style>
    `;

    document.documentElement.insertBefore(banner, document.documentElement.firstChild);
    warningBanner = banner;

    // Close button
    banner.querySelector("#phishnet-close")?.addEventListener("click", () => {
      removeBanner();
    });

    // Auto-dismiss suspicious after 8s, phishing stays
    if (isSuspicious) {
      setTimeout(removeBanner, 8000);
    }
  }

  function showSafePopup() {
    removeBanner();
    const popup = document.createElement("div");
    popup.id = "phishnet-safe-popup";
    popup.innerHTML = `
      <div style="
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 2147483647;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: system-ui, -apple-system, sans-serif;
        animation: phishnet-fade-in-up 0.4s ease-out forwards;
      ">
        <span style="font-size: 18px;">✅</span>
        <span style="font-size: 14px; font-weight: 600; color: #166534;">Website Scanned: Safe</span>
      </div>
      <style>
        @keyframes phishnet-fade-in-up {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes phishnet-fade-out-down {
          from { transform: translateY(0); opacity: 1; }
          to { transform: translateY(20px); opacity: 0; }
        }
      </style>
    `;
    document.documentElement.appendChild(popup);
    warningBanner = popup;
    
    setTimeout(() => {
      if (popup) {
        popup.style.animation = "phishnet-fade-out-down 0.4s ease-in forwards";
        setTimeout(() => popup.remove(), 400);
      }
    }, 4000);
  }

  function removeBanner() {
    const existingSafe = document.getElementById("phishnet-safe-popup");
    if (existingSafe) existingSafe.remove();

    if (warningBanner) {
      const inner = warningBanner.querySelector("#phishnet-inner");
      if (inner) {
        inner.style.animation = "phishnet-slide-out 0.25s ease forwards";
        setTimeout(() => {
          warningBanner?.remove();
          warningBanner = null;
        }, 250);
      } else {
        warningBanner.remove();
        warningBanner = null;
      }
    }
  }

  // ─── Message listener ─────────────────────────────────

  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "PHISHNET_RESULT") {
      const result = message.data;
      if (result && result.status !== currentStatus) {
        currentStatus = result.status;
        createBanner(result);
      }
    }
  });

})();
