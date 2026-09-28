  // Quick Days Chips for Custom Date
  document.querySelectorAll(".day-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".day-chip").forEach(b => b.style.borderColor = "");
      btn.style.borderColor = "var(--gold-primary)";
      const days = parseInt(btn.getAttribute("data-days")) || 8;
      const baseDate = new Date(searchDateInput.value || new Date());
      baseDate.setDate(baseDate.getDate() + (days - 1));
      customCheckDate.value = baseDate.toISOString().split("T")[0];
    });
  });
document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentMode = "APP"; // "APP", "MAP", or "SCHEDULE"
  let currentReviews = [];
  let currentTargetInfo = null;
  let autoFetchTimer = null;

  // DOM Elements
  const tabApp = document.getElementById("tabApp");
  const tabMap = document.getElementById("tabMap");
  const tabBulk = document.getElementById("tabBulk");
  const tabSchedule = document.getElementById("tabSchedule");
  const singleTargetGroup = document.getElementById("singleTargetGroup");
  const bulkTargetGroup = document.getElementById("bulkTargetGroup");
  const targetBulkList = document.getElementById("targetBulkList");
  const targetLabel = document.getElementById("targetLabel");
  const targetIdInput = document.getElementById("targetId");
  const targetHint = document.getElementById("targetHint");
  const searchDateInput = document.getElementById("searchDate");
  const ratingSelect = document.getElementById("ratingSelect");
  const keywordText = document.getElementById("keywordText");
  const exactWordCheck = document.getElementById("exactWordCheck");
  const membersText = document.getElementById("membersText");
  const endingHintInput = document.getElementById("endingHintInput");
  const bulkerNameGroup = document.getElementById("bulkerNameGroup");
  const bulkerNameInput = document.getElementById("bulkerName");
  const fetchBtn = document.getElementById("fetchBtn");
  const autoInterval = document.getElementById("autoInterval");
  const autoFetchBtn = document.getElementById("autoFetchBtn");
  const stopAutoBtn = document.getElementById("stopAutoBtn");
  
  // Metrics
  const statScanned = document.getElementById("statScanned");
  const statMatched = document.getElementById("statMatched");
  const statAutoStatus = document.getElementById("statAutoStatus");
  const statAutoSub = document.getElementById("statAutoSub");
  const statSheetStatus = document.getElementById("statSheetStatus");

  // Feed & Banner & Campaigns & Batch
  const targetBanner = document.getElementById("targetBanner");
  const targetIcon = document.getElementById("targetIcon");
  const targetTitle = document.getElementById("targetTitle");
  const targetSub = document.getElementById("targetSub");
  const targetScore = document.getElementById("targetScore");
  const feedToolbar = document.getElementById("feedToolbar");
  const matchedHeaderCount = document.getElementById("matchedHeaderCount");
  const reviewsFeed = document.getElementById("reviewsFeed");
  const emptyState = document.getElementById("emptyState");
  const loadingState = document.getElementById("loadingState");
  const loadingMsg = document.getElementById("loadingMsg");
  const campaignsPanel = document.getElementById("campaignsPanel");
  const campaignsTableBody = document.getElementById("campaignsTableBody");
  const refreshCampaignsBtn = document.getElementById("refreshCampaignsBtn");
  const batchPanel = document.getElementById("batchPanel");
  const batchTableBody = document.getElementById("batchTableBody");
  const batchExportCsvBtn = document.getElementById("batchExportCsvBtn");
  const batchTelegramBtn = document.getElementById("batchTelegramBtn");

  // PWA & Tunnel Elements
  const installPwaBtn = document.getElementById("installPwaBtn");
  const topbarTunnelBadge = document.getElementById("topbarTunnelBadge");
  const startTunnelBtn = document.getElementById("startTunnelBtn");
  const stopTunnelBtn = document.getElementById("stopTunnelBtn");
  const tunnelSpinner = document.getElementById("tunnelSpinner");
  const tunnelUrlBox = document.getElementById("tunnelUrlBox");
  const tunnelLiveLink = document.getElementById("tunnelLiveLink");
  const copyTunnelLinkBtn = document.getElementById("copyTunnelLinkBtn");
  const tunnelStatusBadge = document.getElementById("tunnelStatusBadge");

  let currentBatchResult = null;

  // Export & Action Buttons
  const exportCsvBtn = document.getElementById("exportCsvBtn");
  const syncSheetBtn = document.getElementById("syncSheetBtn");
  const copyAllBtn = document.getElementById("copyAllBtn");

  // Settings Modal
  const openSettingsBtn = document.getElementById("openSettingsBtn");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const cancelSettingsBtn = document.getElementById("cancelSettingsBtn");
  const settingsModal = document.getElementById("settingsModal");
  const settingsForm = document.getElementById("settingsForm");
  const sheetWebhookInput = document.getElementById("sheetWebhookInput");
  const tgTokenInput = document.getElementById("tgTokenInput");
  const tgChatInput = document.getElementById("tgChatInput");
  const placesKeyInput = document.getElementById("placesKeyInput");
  const testTgBtn = document.getElementById("testTgBtn");
  const testTgResult = document.getElementById("testTgResult");

  // Set default date to today
  const today = new Date().toISOString().split("T")[0];
  searchDateInput.value = today;

  // Date Labels and Custom Date Groups
  const searchDateLabel = document.getElementById("searchDateLabel");
  const ratingGroup = document.getElementById("ratingGroup");
  const customCheckDateGroup = document.getElementById("customCheckDateGroup");
  const customCheckDate = document.getElementById("customCheckDate");

  // Floating Toast Notifications System
  function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "✨";
    if (type === "success") icon = "✅";
    else if (type === "error") icon = "❌";
    else if (type === "info") icon = "📋";

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-message">${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "toastFadeOut 0.3s ease-out forwards";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // 1. Mode Switching
  tabApp.addEventListener("click", () => setMode("APP"));
  tabMap.addEventListener("click", () => setMode("MAP"));
  if (tabBulk) tabBulk.addEventListener("click", () => setMode("BULK"));
  tabSchedule.addEventListener("click", () => setMode("SCHEDULE"));

  function setMode(mode) {
    currentMode = mode;
    tabApp.classList.toggle("active", mode === "APP");
    tabMap.classList.toggle("active", mode === "MAP");
    if (tabBulk) tabBulk.classList.toggle("active", mode === "BULK");
    tabSchedule.classList.toggle("active", mode === "SCHEDULE");

    if (mode === "APP") {
      if (singleTargetGroup) singleTargetGroup.classList.remove("hidden");
      if (bulkTargetGroup) bulkTargetGroup.classList.add("hidden");
      if (bulkerNameGroup) bulkerNameGroup.classList.add("hidden");
      const mapTimeGroup = document.getElementById("mapTimeGroup");
      const mapTimeChips = document.getElementById("mapTimeChips");
      const appDateGroup = document.getElementById("appDateGroup");
      if (mapTimeGroup) mapTimeGroup.classList.add("hidden");
      if (mapTimeChips) mapTimeChips.classList.add("hidden");
      if (appDateGroup) appDateGroup.classList.remove("hidden");
      targetLabel.textContent = "Target Package ID";
      targetIdInput.placeholder = "e.g. com.whatsapp or Play Store URL";
      targetHint.textContent = "Enter Google Play Store package ID or Play Store link.";
      searchDateLabel.textContent = "Target Date";
      ratingGroup.classList.remove("hidden");
      customCheckDateGroup.classList.add("hidden");
      fetchBtn.textContent = "⚡ Fetch Reviews Now";
      if (exactWordCheck) exactWordCheck.checked = true;
      const exactLabel = document.querySelector("label[for='exactWordCheck'] .checkbox-label-text");
      if (exactLabel) exactLabel.textContent = "Exact 100% comment match (Strict word-for-word for App campaigns)";
      campaignsPanel.classList.add("hidden");
      if (batchPanel) batchPanel.classList.add("hidden");
      reviewsFeed.classList.remove("hidden");
    } else if (mode === "MAP") {
      if (singleTargetGroup) singleTargetGroup.classList.remove("hidden");
      if (bulkTargetGroup) bulkTargetGroup.classList.add("hidden");
      if (bulkerNameGroup) bulkerNameGroup.classList.add("hidden");
      const mapTimeGroup = document.getElementById("mapTimeGroup");
      const mapTimeChips = document.getElementById("mapTimeChips");
      const appDateGroup = document.getElementById("appDateGroup");
      const mapTimeSelect = document.getElementById("mapTimeSelect");
      if (mapTimeGroup) mapTimeGroup.classList.remove("hidden");
      if (mapTimeChips) mapTimeChips.classList.remove("hidden");
      if (appDateGroup) {
        if (mapTimeSelect && mapTimeSelect.value === "CUSTOM") {
          appDateGroup.classList.remove("hidden");
        } else {
          appDateGroup.classList.add("hidden");
        }
      }
      targetLabel.textContent = "Google Maps Place URL / Place ID";
      targetIdInput.placeholder = "e.g. https://maps.app.goo.gl/... or Place Name";
      targetHint.textContent = "Paste Google Maps location link, Place ID, or Search Query.";
      searchDateLabel.textContent = "Target Date";
      ratingGroup.classList.remove("hidden");
      customCheckDateGroup.classList.add("hidden");
      fetchBtn.textContent = "⚡ Fetch Reviews Now";
      const exactLabel = document.querySelector("label[for='exactWordCheck'] .checkbox-label-text");
      if (exactLabel) exactLabel.textContent = "Exact comment match (uncheck for keywords/phrase search)";
      campaignsPanel.classList.add("hidden");
      if (batchPanel) batchPanel.classList.add("hidden");
      reviewsFeed.classList.remove("hidden");
    } else if (mode === "BULK") {
      if (singleTargetGroup) singleTargetGroup.classList.add("hidden");
      if (bulkTargetGroup) bulkTargetGroup.classList.remove("hidden");
      if (bulkerNameGroup) bulkerNameGroup.classList.add("hidden");
      const mapTimeGroup = document.getElementById("mapTimeGroup");
      const mapTimeChips = document.getElementById("mapTimeChips");
      const appDateGroup = document.getElementById("appDateGroup");
      if (mapTimeGroup) mapTimeGroup.classList.add("hidden");
      if (mapTimeChips) mapTimeChips.classList.add("hidden");
      if (appDateGroup) appDateGroup.classList.remove("hidden");
      searchDateLabel.textContent = "Target Date";
      ratingGroup.classList.remove("hidden");
      customCheckDateGroup.classList.add("hidden");
      fetchBtn.textContent = "🚀 Start Bulk Batch Scan";
      campaignsPanel.classList.add("hidden");
      targetBanner.classList.add("hidden");
      reviewsFeed.classList.remove("hidden");
    } else if (mode === "SCHEDULE") {
      if (singleTargetGroup) singleTargetGroup.classList.remove("hidden");
      if (bulkTargetGroup) bulkTargetGroup.classList.add("hidden");
      if (bulkerNameGroup) bulkerNameGroup.classList.remove("hidden");
      const mapTimeGroup = document.getElementById("mapTimeGroup");
      const mapTimeChips = document.getElementById("mapTimeChips");
      const appDateGroup = document.getElementById("appDateGroup");
      if (mapTimeGroup) mapTimeGroup.classList.add("hidden");
      if (mapTimeChips) mapTimeChips.classList.add("hidden");
      if (appDateGroup) appDateGroup.classList.remove("hidden");
      targetLabel.textContent = "Campaign App Package ID";
      targetIdInput.placeholder = "e.g. com.example.app (App given on Day 1)";
      targetHint.textContent = "Enter app package ID. System will check on the custom date and send to Telegram.";
      searchDateLabel.textContent = "List Date (Day 1)";
      ratingGroup.classList.add("hidden");
      customCheckDateGroup.classList.remove("hidden");
      fetchBtn.textContent = "📅 Save & Schedule Auto-Check Task";
      
      // Default custom date to 8th day from searchDate
      const baseDate = new Date(searchDateInput.value || new Date());
      baseDate.setDate(baseDate.getDate() + 7);
      customCheckDate.value = baseDate.toISOString().split("T")[0];

      campaignsPanel.classList.remove("hidden");
      if (batchPanel) batchPanel.classList.add("hidden");
      reviewsFeed.classList.add("hidden");
      targetBanner.classList.add("hidden");
      feedToolbar.classList.add("hidden");
      loadCampaigns();
    }
  }

  // Quick Time Chips for Google Maps
  document.querySelectorAll(".map-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".map-chip").forEach(c => c.classList.remove("active-chip"));
      chip.classList.add("active-chip");
      const tVal = chip.getAttribute("data-time") || "ALL";
      const mapTimeSelect = document.getElementById("mapTimeSelect");
      const appDateGroup = document.getElementById("appDateGroup");
      if (mapTimeSelect) {
        mapTimeSelect.value = tVal;
      }
      if (appDateGroup) {
        if (tVal === "CUSTOM") {
          appDateGroup.classList.remove("hidden");
        } else {
          appDateGroup.classList.add("hidden");
        }
      }
      showToast(`Selected Maps Timeframe: ${tVal}`, "info");
    });
  });

  const mapTimeSelect = document.getElementById("mapTimeSelect");
  if (mapTimeSelect) {
    mapTimeSelect.addEventListener("change", () => {
      const val = mapTimeSelect.value;
      document.querySelectorAll(".map-chip").forEach(c => {
        c.classList.toggle("active-chip", c.getAttribute("data-time") === val);
      });
      const appDateGroup = document.getElementById("appDateGroup");
      if (appDateGroup) {
        if (val === "CUSTOM") {
          appDateGroup.classList.remove("hidden");
        } else {
          appDateGroup.classList.add("hidden");
        }
      }
    });
  }


  // When searchDate changes, update customCheckDate if in schedule mode
  searchDateInput.addEventListener("change", () => {
    if (currentMode === "SCHEDULE") {
      const baseDate = new Date(searchDateInput.value || new Date());
      baseDate.setDate(baseDate.getDate() + 7);
      customCheckDate.value = baseDate.toISOString().split("T")[0];
    }
  });

  // 2. Quick Symbol Chips, Hint Chips & Day Chips
  document.querySelectorAll(".chip[data-val]").forEach(chip => {
    chip.addEventListener("click", () => {
      const val = chip.getAttribute("data-val");
      if (val) {
        if (keywordText.value.trim()) {
          keywordText.value += "\n" + val;
        } else {
          keywordText.value = val;
        }
        keywordText.focus();
        showToast(`Added quick keyword: ${val}`, "info");
      }
    });
  });

  document.querySelectorAll(".hint-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      if (endingHintInput) {
        endingHintInput.value = chip.getAttribute("data-hint");
        endingHintInput.focus();
        showToast(`Selected Ending Hint: ${endingHintInput.value}`, "info");
      }
    });
  });

  document.querySelectorAll(".day-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".day-chip").forEach(c => c.classList.remove("active-chip"));
      chip.classList.add("active-chip");
      const days = parseInt(chip.getAttribute("data-days") || "7");
      const baseDate = new Date(searchDateInput.value || new Date());
      baseDate.setDate(baseDate.getDate() + days);
      customCheckDate.value = baseDate.toISOString().split("T")[0];
      showToast(`Retention Check set to ${days} Days (${customCheckDate.value})`, "info");
    });
  });

  // 3. Form Submit (Manual Fetch OR Bulk Scan OR Save Schedule)
  document.getElementById("fetchForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (currentMode === "SCHEDULE") {
      await saveScheduledCampaign();
    } else if (currentMode === "BULK") {
      await performBatchFetch();
    } else {
      await performManualFetch();
    }
  });

  async function saveScheduledCampaign() {
    const targetId = targetIdInput.value.trim();
    if (!targetId) return;

    // Calculate days difference
    const sDate = new Date(searchDateInput.value);
    const cDate = new Date(customCheckDate.value);
    const diffDays = Math.max(1, Math.round((cDate - sDate) / (1000 * 60 * 60 * 24))) || 7;

    try {
      const resp = await fetch("/api/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_type: "APP",
          target_id: targetId,
          bulker_name: bulkerNameInput ? bulkerNameInput.value.trim() : "",
          start_date: searchDateInput.value,
          check_date: customCheckDate.value, // Selected custom date
          retention_days: diffDays,
          keywords: keywordText.value,
          members: membersText.value,
          ending_hint: endingHintInput ? endingHintInput.value.trim() : ""
        })
      });

      const data = await resp.json();
      if (data.success) {
        alert(`✅ ${data.message}`);
        loadCampaigns();
      } else {
        alert(data.error || "Failed to schedule task.");
      }
    } catch (err) {
      alert("Error scheduling task: " + err.message);
    }
  }

  async function performManualFetch() {
    const targetId = targetIdInput.value.trim();
    if (!targetId) return;

    // Show loading
    showLoading(true, `Fetching reviews for ${targetId}...`);

    // Calculate search date depending on mode
    let searchDateVal = searchDateInput.value;
    const mapTimeSelect = document.getElementById("mapTimeSelect");
    if (currentMode === "MAP" && mapTimeSelect) {
      if (mapTimeSelect.value !== "CUSTOM") {
        searchDateVal = mapTimeSelect.value;
      }
    }

    try {
      const resp = await fetch("/api/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_type: currentMode,
          target_id: targetId,
          search_date: searchDateVal,
          rating: ratingSelect.value ? parseInt(ratingSelect.value) : null,
          keywords: keywordText.value,
          exact_word: exactWordCheck.checked,
          members: membersText.value,
          ending_hint: endingHintInput ? endingHintInput.value.trim() : "",
          auto_save: true
        })
      });

      const data = await resp.json();
      showLoading(false);

      if (!resp.ok || !data.success) {
        alert(data.error || "Failed to fetch reviews.");
        return;
      }

      currentReviews = data.reviews || [];
      currentTargetInfo = data.app_info || data.place_info || null;

      // Update metrics
      statScanned.textContent = (data.total_scanned || 0).toLocaleString();
      statMatched.textContent = (data.total_matched || 0).toLocaleString();
      matchedHeaderCount.textContent = (data.total_matched || 0).toLocaleString();

      // Render banner
      renderTargetBanner(currentTargetInfo);

      // Render reviews
      renderReviews(currentReviews);
      if (currentReviews.length > 0) {
        showToast(`Found ${currentReviews.length} matched live units! 🎉`, "success");
      } else {
        showToast("No matching reviews found for these criteria.", "info");
      }

    } catch (err) {
      showLoading(false);
      alert("Network or server error occurred: " + err.message);
    }
  }

  async function performBatchFetch() {
    const rawTargets = targetBulkList ? targetBulkList.value.trim() : "";
    if (!rawTargets) {
      showToast("Please enter at least one target link or ID in the box.", "error");
      return;
    }

    const lines = rawTargets.split("\n").map(l => l.trim()).filter(Boolean);
    showLoading(true, `Starting bulk batch scan for ${lines.length} targets...`);
    if (batchPanel) batchPanel.classList.add("hidden");

    try {
      const resp = await fetch("/api/batch_fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          targets: rawTargets,
          search_date: searchDateInput.value,
          rating: ratingSelect.value ? parseInt(ratingSelect.value) : null,
          keywords: keywordText.value,
          exact_word: exactWordCheck.checked,
          members: membersText.value,
          ending_hint: endingHintInput ? endingHintInput.value.trim() : "",
          auto_save: true
        })
      });

      const data = await resp.json();
      showLoading(false);

      if (!resp.ok || !data.success) {
        showToast(data.error || "Batch scan failed.", "error");
        return;
      }

      currentBatchResult = data;
      currentReviews = data.all_matched_reviews || [];

      // Update metrics
      statScanned.textContent = (data.total_scanned || 0).toLocaleString();
      statMatched.textContent = (data.total_matched || 0).toLocaleString();
      matchedHeaderCount.textContent = (data.total_matched || 0).toLocaleString();

      // Render Batch summary table
      renderBatchSummary(data);

      // Render all aggregated reviews
      renderReviews(currentReviews);

      showToast(`Batch Complete: ${data.total_matched} live units across ${data.total_targets} targets! 🎉`, "success");

    } catch (err) {
      showLoading(false);
      showToast("Batch scan error: " + err.message, "error");
    }
  }

  function renderBatchSummary(batchData) {
    if (!batchPanel || !batchTableBody) return;
    batchTableBody.innerHTML = "";
    batchPanel.classList.remove("hidden");

    const targets = batchData.targets_summary || [];
    targets.forEach(t => {
      const tr = document.createElement("tr");
      const icon = t.service_type === "APP" ? "📱 App" : "📍 Map";
      const statusBadge = t.status === "SUCCESS"
        ? '<span class="status-badge badge-green">VERIFIED</span>'
        : `<span class="status-badge badge-danger" title="${escapeHtml(t.error || '')}">ERROR</span>`;

      tr.innerHTML = `
        <td><strong>${t.index}</strong></td>
        <td>
          <div style="font-weight: 700; color: var(--gold-bright);">${escapeHtml(t.target_name || t.target_id)}</div>
          <small style="color: var(--text-muted); font-size: 11px;">${escapeHtml(t.target_id)}</small>
        </td>
        <td><span class="status-badge">${icon}</span></td>
        <td><strong>${t.scanned}</strong></td>
        <td><span style="color: var(--emerald-bright); font-weight: 800; font-size: 14px;">${t.matched}</span></td>
        <td>${statusBadge}</td>
      `;
      batchTableBody.appendChild(tr);
    });
  }

  if (batchExportCsvBtn) {
    batchExportCsvBtn.addEventListener("click", async () => {
      if (!currentReviews || currentReviews.length === 0) {
        showToast("No batch reviews to export.", "info");
        return;
      }
      try {
        const resp = await fetch("/api/batch_export_csv", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(currentReviews)
        });
        if (resp.ok) {
          const blob = await resp.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `Arceus_Batch_Matched_${new Date().toISOString().split("T")[0]}.csv`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          showToast("Consolidated Batch CSV exported! 📁", "success");
        }
      } catch (err) {
        showToast("CSV export failed: " + err.message, "error");
      }
    });
  }

  if (batchTelegramBtn) {
    batchTelegramBtn.addEventListener("click", async () => {
      if (!currentBatchResult) {
        showToast("No batch result to send.", "info");
        return;
      }
      showToast("Sending Batch Report & CSV to Telegram...", "info");
      try {
        const resp = await fetch("/api/batch_telegram_alert", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            batch_result: currentBatchResult,
            search_date: searchDateInput.value
          })
        });
        const data = await resp.json();
        if (data.success) {
          showToast("Batch Report & CSV sent to Telegram! ✈️", "success");
        } else {
          showToast(data.message || data.error || "Failed to send to Telegram.", "error");
        }
      } catch (err) {
        showToast("Telegram send error: " + err.message, "error");
      }
    });
  }

  function renderTargetBanner(info) {
    if (!info) {
      targetBanner.classList.add("hidden");
      return;
    }
    targetBanner.classList.remove("hidden");
    targetIcon.src = info.icon || "/static/img/default-app.png";
    targetTitle.textContent = info.title || targetIdInput.value;
    
    let sub = [];
    if (info.developer) sub.push(info.developer);
    if (info.installs) sub.push(info.installs + " installs");
    if (info.total_ratings) sub.push(info.total_ratings + " ratings");
    targetSub.textContent = sub.join(" • ") || (currentMode === "APP" ? "Android App" : "Location on Google Maps");
    
    targetScore.textContent = `★ ${info.score || '0.0'}`;
  }

  function renderReviews(reviews, isLiveFiltering = false) {
    reviewsFeed.innerHTML = "";

    if (!reviews || reviews.length === 0) {
      if (!isLiveFiltering) {
        feedToolbar.classList.add("hidden");
      }
      emptyState.classList.remove("hidden");
      const titleEl = emptyState.querySelector(".empty-title") || emptyState.querySelector("h2") || emptyState.querySelector("h3");
      if (titleEl) titleEl.textContent = "No Matching Reviews Found";
      const descEl = emptyState.querySelector("p");
      if (descEl) descEl.textContent = isLiveFiltering ? "No reviews match your search query. Backspace or clear search box." : "No reviews found matching the specified date, rating, and comments/keywords. Try selecting 'All Stars' or modifying keywords.";
      reviewsFeed.appendChild(emptyState);
      return;
    }

    emptyState.classList.add("hidden");
    feedToolbar.classList.remove("hidden");

    reviews.forEach((r, idx) => {
      const card = document.createElement("div");
      card.className = "review-card";
      card.style.animationDelay = `${Math.min(idx * 0.05, 0.8)}s`;

      const stars = "★".repeat(r.rating || 5) + "☆".repeat(5 - (r.rating || 5));
      const avatarSrc = r.user_image || "https://www.gstatic.com/images/branding/product/1x/avatar_circle_blue_512dp.png";

      card.innerHTML = `
        <div class="review-header">
          <div class="reviewer-profile">
            <img class="reviewer-avatar" src="${avatarSrc}" alt="Avatar" onerror="this.src='https://www.gstatic.com/images/branding/product/1x/avatar_circle_blue_512dp.png'">
            <div>
              <div class="reviewer-name">${escapeHtml(r.user_name)}</div>
              <div class="review-meta">
                <span class="review-stars">${stars}</span>
                <span class="review-date">${r.review_date} ${r.review_time || ''}</span>
              </div>
            </div>
          </div>
          <span class="matched-badge">✨ 100% MATCH</span>
        </div>

        <div class="review-body">
          ${r.highlighted_text || escapeHtml(r.review_text)}
        </div>

        <div class="review-footer">
          <span class="matched-rule-tag">Rule: <strong>${escapeHtml(r.matched_keywords || 'Comment Match')}</strong></span>
          <button class="btn-copy-card copy-btn" data-text="${escapeHtml(r.review_text)}">📋 Copy</button>
        </div>
      `;

      reviewsFeed.appendChild(card);
    });

    // Wire up individual copy buttons
    document.querySelectorAll(".copy-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const text = btn.getAttribute("data-text");
        navigator.clipboard.writeText(text).then(() => {
          btn.textContent = "Copied! ✓";
          showToast("Review text copied to clipboard! ✓", "info");
          setTimeout(() => btn.textContent = "📋 Copy", 1500);
        });
      });
    });
  }

  // 3b. Show All Recent Reviews (No Filter) Button
  const fetchAllRecentBtn = document.getElementById("fetchAllRecentBtn");
  if (fetchAllRecentBtn) {
    fetchAllRecentBtn.addEventListener("click", async () => {
      const targetId = targetIdInput.value.trim();
      if (!targetId) {
        showToast("Please enter a Target ID or Maps link first!", "error");
        targetIdInput.focus();
        return;
      }

      // Save user inputs temporarily
      const prevKw = keywordText.value;
      const prevHint = endingHintInput ? endingHintInput.value : "";
      const prevMembers = membersText ? membersText.value : "";
      const prevExact = exactWordCheck.checked;

      // Temporarily clear to fetch all recent reviews
      keywordText.value = "";
      if (endingHintInput) endingHintInput.value = "";
      if (membersText) membersText.value = "";
      exactWordCheck.checked = false;

      showToast("Fetching all recent live reviews (no filters)...", "info");
      try {
        await performManualFetch();
      } finally {
        // Restore user inputs
        keywordText.value = prevKw;
        if (endingHintInput) endingHintInput.value = prevHint;
        if (membersText) membersText.value = prevMembers;
        exactWordCheck.checked = prevExact;
      }
    });
  }

  // 3c. Live In-Feed Real-time Instant Search
  const liveFeedSearch = document.getElementById("liveFeedSearch");
  if (liveFeedSearch) {
    liveFeedSearch.addEventListener("input", () => {
      const q = liveFeedSearch.value.trim().toLowerCase();
      if (!currentReviews || currentReviews.length === 0) return;
      if (!q) {
        renderReviews(currentReviews);
        matchedHeaderCount.textContent = currentReviews.length.toLocaleString();
        return;
      }
      const filtered = currentReviews.filter(r => {
        const author = (r.user_name || "").toLowerCase();
        const text = (r.review_text || "").toLowerCase();
        const rule = (r.matched_keywords || "").toLowerCase();
        return author.includes(q) || text.includes(q) || rule.includes(q);
      });
      renderReviews(filtered, true);
      matchedHeaderCount.textContent = filtered.length.toLocaleString();
    });
  }

  // 4. Auto-Fetch Background Monitor
  autoFetchBtn.addEventListener("click", async () => {
    const targetId = targetIdInput.value.trim();
    if (!targetId) {
      alert("Please enter a target Package ID or Maps URL first.");
      return;
    }

    const intervalMin = parseInt(autoInterval.value);

    let searchDateVal = searchDateInput.value;
    const mapTimeSelect = document.getElementById("mapTimeSelect");
    if (currentMode === "MAP" && mapTimeSelect) {
      if (mapTimeSelect.value !== "CUSTOM") {
        searchDateVal = mapTimeSelect.value;
      }
    }

    try {
      const resp = await fetch("/api/autofetch/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_type: currentMode,
          target_id: targetId,
          search_date: searchDateVal,
          rating: ratingSelect.value ? parseInt(ratingSelect.value) : null,
          keywords: keywordText.value,
          exact_word: exactWordCheck.checked,
          members: membersText.value,
          ending_hint: endingHintInput ? endingHintInput.value.trim() : "",
          interval_minutes: intervalMin
        })
      });

      const data = await resp.json();
      if (data.success) {
        startPollingAutoFetch();
      }
    } catch (err) {
      alert("Failed to start auto-fetch: " + err.message);
    }
  });

  stopAutoBtn.addEventListener("click", async () => {
    try {
      await fetch("/api/autofetch/stop", { method: "POST" });
      stopPollingAutoFetch();
    } catch (err) {
      console.error(err);
    }
  });

  function startPollingAutoFetch() {
    autoFetchBtn.classList.add("hidden");
    stopAutoBtn.classList.remove("hidden");
    statAutoStatus.textContent = "MONITORING";
    statAutoStatus.className = "metric-value status-badge badge-gold";
    statAutoSub.textContent = `Active: Every ${autoInterval.value} min`;

    if (autoFetchTimer) clearInterval(autoFetchTimer);
    autoFetchTimer = setInterval(pollAutoFetchStatus, 4000);
    pollAutoFetchStatus();
  }

  function stopPollingAutoFetch() {
    autoFetchBtn.classList.remove("hidden");
    stopAutoBtn.classList.add("hidden");
    statAutoStatus.textContent = "STANDBY";
    statAutoStatus.className = "metric-value status-badge";
    statAutoSub.textContent = "Click Start Auto-Fetch";
    if (autoFetchTimer) {
      clearInterval(autoFetchTimer);
      autoFetchTimer = null;
    }
  }

  async function pollAutoFetchStatus() {
    try {
      const resp = await fetch("/api/autofetch/status");
      const st = await resp.json();

      if (!st.is_running) {
        stopPollingAutoFetch();
        return;
      }

      statScanned.textContent = (st.total_scanned || 0).toLocaleString();
      statMatched.textContent = (st.matched_count || 0).toLocaleString();
      statAutoSub.textContent = `Last run: ${st.last_run ? st.last_run.split(' ')[1] : 'just now'}`;

    } catch (e) {
      console.error("Auto fetch polling error:", e);
    }
  }

  // 5. CSV Export
  exportCsvBtn.addEventListener("click", async () => {
    if (!currentReviews || currentReviews.length === 0) {
      alert("No matched reviews available to export.");
      return;
    }

    try {
      const resp = await fetch("/api/export/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentReviews)
      });

      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Arceus_Reviews_${searchDateInput.value || 'Matched'}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert("Export failed: " + err.message);
    }
  });

  // 6. Google Sheet Upload
  syncSheetBtn.addEventListener("click", async () => {
    if (!currentReviews || currentReviews.length === 0) {
      alert("No matched reviews to sync.");
      return;
    }

    syncSheetBtn.textContent = "Uploading...";
    syncSheetBtn.disabled = true;

    try {
      const resp = await fetch("/api/sync/sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_name: targetTitle.textContent || targetIdInput.value,
          search_date: searchDateInput.value,
          reviews: currentReviews
        })
      });

      const data = await resp.json();
      if (data.success) {
        alert(`Successfully synced ${data.uploaded} reviews to Google Sheet!`);
        statSheetStatus.textContent = "SYNCED";
        statSheetSub.textContent = `${data.uploaded} units uploaded`;
      } else {
        alert("Google Sheet Upload: " + (data.message || "Failed. Configure Webhook URL in Settings."));
      }
    } catch (err) {
      alert("Error syncing to sheet: " + err.message);
    } finally {
      syncSheetBtn.textContent = "📤 Upload to Google Sheet";
      syncSheetBtn.disabled = false;
    }
  });

  // Send Alert to Telegram Bot
  const sendTgAlertBtn = document.getElementById("sendTgAlertBtn");
  if (sendTgAlertBtn) {
    sendTgAlertBtn.addEventListener("click", async () => {
      if (!currentReviews || currentReviews.length === 0) {
        alert("No matched reviews to send.");
        return;
      }

      sendTgAlertBtn.textContent = "Sending to TG...";
      sendTgAlertBtn.disabled = true;

      try {
        const resp = await fetch("/api/telegram/send_alert", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            app_name: targetTitle.textContent || targetIdInput.value,
            search_date: searchDateInput.value,
            service_type: currentMode,
            reviews: currentReviews
          })
        });

        const data = await resp.json();
        if (data.success) {
          alert(`✅ Success! Sent App Name, Date, ${currentReviews.length} Members, and CSV directly to your Telegram Bot!`);
        } else {
          alert("Telegram Send Failed: " + (data.message || "Check bot settings"));
        }
      } catch (err) {
        alert("Error sending to Telegram: " + err.message);
      } finally {
        sendTgAlertBtn.textContent = "🤖 Send Alert to Bot";
        sendTgAlertBtn.disabled = false;
      }
    });
  }

  // 7. Copy All Matched Units
  copyAllBtn.addEventListener("click", () => {
    if (!currentReviews || currentReviews.length === 0) return;
    const formatted = currentReviews.map((r, i) => `${i+1}. [${r.user_name}] (${r.rating}★) ${r.review_date}: "${r.review_text}"`).join("\n\n");
    navigator.clipboard.writeText(formatted).then(() => {
      copyAllBtn.textContent = "Copied All! ✓";
      showToast(`Copied all ${currentReviews.length} matched reviews to clipboard! ✓`, "info");
      setTimeout(() => copyAllBtn.textContent = "📋 Copy All", 2000);
    });
  });

  // ==========================================================================
  // 8. MASTER ADMIN ID & PASSWORD SECURITY CONTROLLER
  // ==========================================================================
  let isSessionUnlocked = false;
  let pendingAuthCallback = null;
  let securityState = {
    admin_username: "admin",
    has_security_pin: false,
    lock_settings_enabled: true,
    lock_campaigns_enabled: false,
    lock_tunnel_enabled: false
  };

  const adminAuthModal = document.getElementById("adminAuthModal");
  const adminAuthForm = document.getElementById("adminAuthForm");
  const authUsernameInput = document.getElementById("authUsernameInput");
  const authPasswordInput = document.getElementById("authPasswordInput");
  const adminAuthError = document.getElementById("adminAuthError");
  const adminAuthPromptMsg = document.getElementById("adminAuthPromptMsg");
  const closeAdminAuthBtn = document.getElementById("closeAdminAuthBtn");
  const cancelAdminAuthBtn = document.getElementById("cancelAdminAuthBtn");
  const submitAdminAuthBtn = document.getElementById("submitAdminAuthBtn");

  const lockStatusPill = document.getElementById("lockStatusPill");
  const adminUsernameInput = document.getElementById("adminUsernameInput");
  const adminPasswordInput = document.getElementById("adminPasswordInput");
  const confirmAdminPasswordInput = document.getElementById("confirmAdminPasswordInput");
  const toggleMaskKeysBtn = document.getElementById("toggleMaskKeysBtn");
  const lockSessionNowBtn = document.getElementById("lockSessionNowBtn");
  const lockSettingsCheck = document.getElementById("lockSettingsCheck");
  const lockCampaignsCheck = document.getElementById("lockCampaignsCheck");
  const lockTunnelCheck = document.getElementById("lockTunnelCheck");

  let areKeysMasked = true;
  function applyKeyMasking() {
    const type = areKeysMasked ? "password" : "text";
    if (tgTokenInput) tgTokenInput.type = type;
    if (tgChatInput) tgChatInput.type = type;
    if (sheetWebhookInput) sheetWebhookInput.type = type;
    if (placesKeyInput) placesKeyInput.type = type;
    if (adminPasswordInput) adminPasswordInput.type = type;
    if (confirmAdminPasswordInput) confirmAdminPasswordInput.type = type;
    if (toggleMaskKeysBtn) {
      toggleMaskKeysBtn.textContent = areKeysMasked ? "👁️ Show Passwords & API Keys" : "🔒 Mask Passwords & API Keys";
    }
  }

  if (toggleMaskKeysBtn) {
    toggleMaskKeysBtn.addEventListener("click", () => {
      areKeysMasked = !areKeysMasked;
      applyKeyMasking();
    });
  }

  if (lockSessionNowBtn) {
    lockSessionNowBtn.addEventListener("click", () => {
      isSessionUnlocked = false;
      closeModal();
      showToast("Settings session locked! 🔒", "info");
    });
  }

  async function loadSecurityStatus() {
    try {
      const resp = await fetch("/api/settings");
      const data = await resp.json();
      securityState.admin_username = data.admin_username || "admin";
      securityState.has_security_pin = !!data.has_security_pin;
      securityState.lock_settings_enabled = (data.lock_settings_enabled !== false);
      securityState.lock_campaigns_enabled = !!data.lock_campaigns_enabled;
      securityState.lock_tunnel_enabled = !!data.lock_tunnel_enabled;
      updateSecurityUI();
    } catch (e) {}
  }

  function updateSecurityUI() {
    if (lockStatusPill) {
      if (securityState.lock_settings_enabled) {
        lockStatusPill.textContent = "🔒 PROTECTED (ID & PASS)";
        lockStatusPill.className = "status-badge badge-green";
      } else {
        lockStatusPill.textContent = "⚪ UNLOCKED (OPEN)";
        lockStatusPill.className = "status-badge";
      }
    }
    if (adminUsernameInput && !adminUsernameInput.value) {
      adminUsernameInput.value = securityState.admin_username || "admin";
    }
    if (lockSettingsCheck) lockSettingsCheck.checked = securityState.lock_settings_enabled;
    if (lockCampaignsCheck) lockCampaignsCheck.checked = securityState.lock_campaigns_enabled;
    if (lockTunnelCheck) lockTunnelCheck.checked = securityState.lock_tunnel_enabled;
  }

  function promptAdminAuth(message, onSuccess) {
    pendingAuthCallback = onSuccess;
    if (adminAuthPromptMsg) adminAuthPromptMsg.textContent = message || "Enter Admin ID & Password to access Settings & Credentials.";
    if (authUsernameInput) authUsernameInput.value = securityState.admin_username || "admin";
    if (authPasswordInput) authPasswordInput.value = "";
    if (adminAuthError) adminAuthError.classList.add("hidden");
    if (adminAuthModal) adminAuthModal.classList.remove("hidden");
    setTimeout(() => {
      if (authPasswordInput) authPasswordInput.focus();
    }, 150);
  }

  function closeAdminAuthModal() {
    if (adminAuthModal) adminAuthModal.classList.add("hidden");
    pendingAuthCallback = null;
  }

  if (closeAdminAuthBtn) closeAdminAuthBtn.addEventListener("click", closeAdminAuthModal);
  if (cancelAdminAuthBtn) cancelAdminAuthBtn.addEventListener("click", closeAdminAuthModal);

  async function submitAdminAuth(e) {
    if (e) e.preventDefault();
    const user = authUsernameInput ? authUsernameInput.value.trim() : "";
    const pass = authPasswordInput ? authPasswordInput.value.trim() : "";
    
    if (!user || !pass) {
      if (adminAuthError) {
        adminAuthError.textContent = "⚠️ Please enter both Admin ID and Password.";
        adminAuthError.classList.remove("hidden");
      }
      return;
    }

    try {
      if (submitAdminAuthBtn) {
        submitAdminAuthBtn.disabled = true;
        submitAdminAuthBtn.textContent = "Verifying...";
      }
      const resp = await fetch("/api/settings/verify_auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, password: pass })
      });
      const data = await resp.json();
      if (data.valid) {
        isSessionUnlocked = true;
        closeAdminAuthModal();
        showToast("Admin authenticated! 🔓", "success");
        if (typeof pendingAuthCallback === "function") {
          const cb = pendingAuthCallback;
          pendingAuthCallback = null;
          cb();
        }
      } else {
        if (adminAuthError) {
          adminAuthError.textContent = "❌ Incorrect Admin ID or Password. Please try again.";
          adminAuthError.classList.remove("hidden");
        }
        if (authPasswordInput) {
          authPasswordInput.value = "";
          authPasswordInput.focus();
        }
      }
    } catch (err) {
      if (adminAuthError) {
        adminAuthError.textContent = "Auth error: " + err.message;
        adminAuthError.classList.remove("hidden");
      }
    } finally {
      if (submitAdminAuthBtn) {
        submitAdminAuthBtn.disabled = false;
        submitAdminAuthBtn.textContent = "🔓 Login & Open";
      }
    }
  }

  if (adminAuthForm) {
    adminAuthForm.addEventListener("submit", submitAdminAuth);
  }

  function openSettingsModal() {
    // Load current settings
    fetch("/api/settings")
      .then(r => r.json())
      .then(s => {
        if (sheetWebhookInput) sheetWebhookInput.value = s.google_sheet_webhook_url || "";
        if (tgTokenInput) tgTokenInput.value = s.telegram_bot_token || "";
        if (tgChatInput) tgChatInput.value = s.telegram_chat_id || "";
        if (placesKeyInput) placesKeyInput.value = s.google_places_api_key || "";
        if (adminUsernameInput) adminUsernameInput.value = s.admin_username || "admin";
        securityState.admin_username = s.admin_username || "admin";
        securityState.has_security_pin = !!s.has_security_pin;
        securityState.lock_settings_enabled = (s.lock_settings_enabled !== false);
        securityState.lock_campaigns_enabled = !!s.lock_campaigns_enabled;
        securityState.lock_tunnel_enabled = !!s.lock_tunnel_enabled;
        updateSecurityUI();
        applyKeyMasking();
      })
      .catch(() => {});
    checkTunnelStatus();
    settingsModal.classList.remove("hidden");
  }

  openSettingsBtn.addEventListener("click", () => {
    if (securityState.lock_settings_enabled && !isSessionUnlocked) {
      promptAdminAuth("Enter Admin ID & Password to access Settings:", () => {
        openSettingsModal();
      });
      return;
    }
    openSettingsModal();
  });

  const closeModal = () => settingsModal.classList.add("hidden");
  closeSettingsBtn.addEventListener("click", closeModal);
  cancelSettingsBtn.addEventListener("click", closeModal);

  settingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const newPass = adminPasswordInput ? adminPasswordInput.value.trim() : "";
    const confirmPass = confirmAdminPasswordInput ? confirmAdminPasswordInput.value.trim() : "";
    const newUsername = adminUsernameInput ? adminUsernameInput.value.trim() : "admin";

    if (newPass || confirmPass) {
      if (newPass !== confirmPass) {
        alert("⚠️ New Password and Confirm Password do not match!");
        if (confirmAdminPasswordInput) confirmAdminPasswordInput.focus();
        return;
      }
      if (newPass.length < 3) {
        alert("⚠️ Password must be at least 3 characters.");
        if (adminPasswordInput) adminPasswordInput.focus();
        return;
      }
    }

    try {
      const payload = {
        google_sheet_webhook_url: sheetWebhookInput.value,
        telegram_bot_token: tgTokenInput.value,
        telegram_chat_id: tgChatInput.value,
        google_places_api_key: placesKeyInput.value,
        admin_username: newUsername,
        lock_settings_enabled: lockSettingsCheck ? lockSettingsCheck.checked : true,
        lock_campaigns_enabled: lockCampaignsCheck ? lockCampaignsCheck.checked : false,
        lock_tunnel_enabled: lockTunnelCheck ? lockTunnelCheck.checked : false
      };
      if (newPass) {
        payload.admin_password = newPass;
      }

      const resp = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const res = await resp.json();
      if (res.success) {
        showToast("Settings & Admin Credentials saved! ⚙️", "success");
        if (adminPasswordInput) adminPasswordInput.value = "";
        if (confirmAdminPasswordInput) confirmAdminPasswordInput.value = "";
        closeModal();
        await loadSecurityStatus();
      } else {
        alert(res.message || "Failed to save settings.");
      }
    } catch (err) {
      alert("Failed to save settings: " + err.message);
    }
  });

  // 9. Telegram Test Connection
  testTgBtn.addEventListener("click", async () => {
    const token = tgTokenInput.value.trim();
    const chat = tgChatInput.value.trim();
    if (!token || !chat) {
      testTgResult.textContent = "⚠️ Please enter both Bot Token and Chat ID.";
      testTgResult.style.color = "#f87171";
      return;
    }

    testTgResult.textContent = "Testing...";
    testTgResult.style.color = "#94a3b8";

    try {
      const resp = await fetch("/api/telegram/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bot_token: token, chat_id: chat })
      });
      const data = await resp.json();
      if (data.success) {
        testTgResult.textContent = "✅ Message sent to Telegram!";
        testTgResult.style.color = "#10b981";
      } else {
        testTgResult.textContent = "❌ " + (data.message || "Failed");
        testTgResult.style.color = "#f87171";
      }
    } catch (e) {
      testTgResult.textContent = "❌ Error: " + e.message;
      testTgResult.style.color = "#f87171";
    }
  });

  // 10. Campaigns Management
  if (refreshCampaignsBtn) {
    refreshCampaignsBtn.addEventListener("click", loadCampaigns);
  }

  async function loadCampaigns() {
    if (!campaignsTableBody) return;
    campaignsTableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Loading campaigns...</td></tr>`;

    try {
      const resp = await fetch("/api/campaigns");
      const data = await resp.json();
      const campaigns = data.campaigns || [];

      if (campaigns.length === 0) {
        campaignsTableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No scheduled retention tasks yet. Create one on the left!</td></tr>`;
        return;
      }

      campaignsTableBody.innerHTML = "";
      campaigns.forEach(c => {
        const tr = document.createElement("tr");

        let countdownHtml = "";
        if (c.status === "COMPLETED") {
          countdownHtml = `<span class="countdown-badge badge-completed">✅ Checked & Sent</span>`;
        } else if (c.days_remaining <= 0) {
          countdownHtml = `<span class="countdown-badge badge-due">🔔 Due Today!</span>`;
        } else {
          countdownHtml = `<span class="countdown-badge badge-pending">⏳ ${c.days_remaining} days left</span>`;
        }

        const statusBadge = c.status === "COMPLETED" 
          ? `<span class="status-badge badge-green">${c.matched_units} Live Units</span>` 
          : `<span class="status-badge">${c.status}</span>`;

        const bulkerDisplay = c.bulker_name 
          ? `<span class="badge-bulker">🏷️ ${escapeHtml(c.bulker_name)}</span>` 
          : `<span class="text-muted" style="font-size: 11px;">—</span>`;

        tr.innerHTML = `
          <td><strong>${escapeHtml(c.target_name || c.target_id)}</strong><br><small class="text-muted">${escapeHtml(c.target_id)}</small></td>
          <td>${bulkerDisplay}</td>
          <td>${c.start_date}</td>
          <td><strong>${c.check_date}</strong> (Day ${c.retention_days})</td>
          <td>${countdownHtml}</td>
          <td>${statusBadge}</td>
          <td>
            <button type="button" class="btn-sm btn-action-run check-task-btn" data-id="${c.id}" title="Run Check & Send Telegram Report Now">⚡ Check & Send TG</button>
            <button type="button" class="btn-sm btn-action-del del-task-btn" data-id="${c.id}" title="Delete Task">🗑️</button>
          </td>
        `;

        campaignsTableBody.appendChild(tr);
      });

      // Wire up action buttons
      document.querySelectorAll(".check-task-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-id");
          btn.textContent = "Checking & Sending...";
          btn.disabled = true;
          try {
            const r = await fetch(`/api/campaigns/${id}/check_now`, { method: "POST" });
            const res = await r.json();
            if (res.success) {
              alert(`🎉 Checked successfully! Found ${res.matched_units} Live Units. Telegram dispatched: ${res.telegram_sent ? 'YES' : 'NO (Check bot settings)'}`);
              loadCampaigns();
            } else {
              alert("Check failed: " + (res.error || "Unknown error"));
            }
          } catch (e) {
            alert("Error: " + e.message);
          } finally {
            btn.textContent = "⚡ Check & Send TG";
            btn.disabled = false;
          }
        });
      });

      document.querySelectorAll(".del-task-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-id");
          const doDelete = async () => {
            if (!confirm("Are you sure you want to delete this scheduled campaign?")) return;
            try {
              await fetch(`/api/campaigns/${id}`, { method: "DELETE" });
              loadCampaigns();
            } catch (e) {
              alert("Delete failed: " + e.message);
            }
          };

          if (securityState.lock_campaigns_enabled && !isSessionUnlocked) {
            promptAdminAuth("Admin ID & Password required to delete this scheduled campaign:", () => {
              doDelete();
            });
            return;
          }
          doDelete();
        });
      });

    } catch (err) {
      console.error("Error loading campaigns:", err);
    }
  }

  function showLoading(show, msg = "") {
    if (show) {
      loadingState.classList.remove("hidden");
      loadingMsg.textContent = msg;
      emptyState.classList.add("hidden");
      feedToolbar.classList.add("hidden");
      fetchBtn.disabled = true;
      fetchBtn.textContent = "⏳ Fetching...";
    } else {
      loadingState.classList.add("hidden");
      fetchBtn.disabled = false;
      fetchBtn.textContent = "⚡ Fetch Reviews Now";
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // --- CLOUDFLARE REMOTE TUNNEL LOGIC ---
  async function checkTunnelStatus() {
    try {
      const resp = await fetch("/api/tunnel/status");
      const data = await resp.json();
      updateTunnelUI(data);
    } catch (e) {
      console.log("Tunnel status check error:", e);
    }
  }

  function updateTunnelUI(data) {
    if (!tunnelStatusBadge) return;
    if (data && data.running && data.url) {
      if (topbarTunnelBadge) topbarTunnelBadge.classList.remove("hidden");
      tunnelStatusBadge.textContent = "ONLINE (ACTIVE)";
      tunnelStatusBadge.className = "status-badge badge-green";
      if (tunnelUrlBox) tunnelUrlBox.classList.remove("hidden");
      if (tunnelLiveLink) {
        tunnelLiveLink.href = data.url;
        tunnelLiveLink.textContent = data.url;
      }
      if (startTunnelBtn) startTunnelBtn.classList.add("hidden");
      if (stopTunnelBtn) stopTunnelBtn.classList.remove("hidden");
      if (tunnelSpinner) tunnelSpinner.classList.add("hidden");
    } else {
      if (topbarTunnelBadge) topbarTunnelBadge.classList.add("hidden");
      tunnelStatusBadge.textContent = "STANDBY";
      tunnelStatusBadge.className = "status-badge";
      if (tunnelUrlBox) tunnelUrlBox.classList.add("hidden");
      if (startTunnelBtn) startTunnelBtn.classList.remove("hidden");
      if (stopTunnelBtn) stopTunnelBtn.classList.add("hidden");
      if (tunnelSpinner) tunnelSpinner.classList.add("hidden");
    }
  }

  if (startTunnelBtn) {
    const proceedStartTunnel = async () => {
      if (tunnelSpinner) tunnelSpinner.classList.remove("hidden");
      startTunnelBtn.classList.add("hidden");
      showToast("Launching Cloudflare Secure Tunnel...", "info");
      try {
        const resp = await fetch("/api/tunnel/start", { method: "POST" });
        const data = await resp.json();
        if (tunnelSpinner) tunnelSpinner.classList.add("hidden");
        if (data.success && data.url) {
          updateTunnelUI(data);
          showToast("Cloud Access Live! Link ready for phone. 🌐", "success");
        } else {
          showToast(data.message || "Failed to start tunnel.", "error");
          updateTunnelUI({ running: false });
        }
      } catch (err) {
        if (tunnelSpinner) tunnelSpinner.classList.add("hidden");
        showToast("Tunnel error: " + err.message, "error");
        updateTunnelUI({ running: false });
      }
    };

    startTunnelBtn.addEventListener("click", () => {
      if (securityState.lock_tunnel_enabled && !isSessionUnlocked) {
        promptAdminAuth("Admin ID & Password required to start Cloud Remote Access:", () => {
          proceedStartTunnel();
        });
        return;
      }
      proceedStartTunnel();
    });
  }

  if (stopTunnelBtn) {
    const proceedStopTunnel = async () => {
      try {
        const resp = await fetch("/api/tunnel/stop", { method: "POST" });
        const data = await resp.json();
        updateTunnelUI({ running: false });
        showToast("Cloud Access Stopped.", "info");
      } catch (err) {
        showToast("Error stopping tunnel: " + err.message, "error");
      }
    };

    stopTunnelBtn.addEventListener("click", () => {
      if (securityState.lock_tunnel_enabled && !isSessionUnlocked) {
        promptAdminAuth("Admin ID & Password required to stop Cloud Remote Access:", () => {
          proceedStopTunnel();
        });
        return;
      }
      proceedStopTunnel();
    });
  }

  if (copyTunnelLinkBtn) {
    copyTunnelLinkBtn.addEventListener("click", () => {
      if (tunnelLiveLink && tunnelLiveLink.textContent) {
        navigator.clipboard.writeText(tunnelLiveLink.textContent).then(() => {
          showToast("Cloud URL copied to clipboard! 📋", "success");
        });
      }
    });
  }

  if (topbarTunnelBadge) {
    topbarTunnelBadge.addEventListener("click", () => {
      if (securityState.lock_settings_enabled && !isSessionUnlocked) {
        promptAdminAuth("Enter Admin ID & Password to view Cloud Remote Access:", () => {
          openSettingsModal();
        });
        return;
      }
      openSettingsModal();
    });
  }

  // Check tunnel on initial load
  checkTunnelStatus();

  // Load Security Lock Status on initial load
  loadSecurityStatus();

  // --- PWA (PROGRESSIVE WEB APP) INSTALLATION ---
  let deferredInstallPrompt = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    if (installPwaBtn) installPwaBtn.classList.remove("hidden");
  });

  if (installPwaBtn) {
    installPwaBtn.addEventListener("click", async () => {
      if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        const { outcome } = await deferredInstallPrompt.userChoice;
        if (outcome === "accepted") {
          showToast("Arceus App Installed Successfully! 👑", "success");
        }
        deferredInstallPrompt = null;
        installPwaBtn.classList.add("hidden");
      } else {
        showToast("To install, tap your browser's menu (⋮) -> 'Install App' or 'Add to Home Screen'", "info");
      }
    });
  }

  window.addEventListener("appinstalled", () => {
    if (installPwaBtn) installPwaBtn.classList.add("hidden");
    showToast("Welcome to Arceus PRO App! 🚀", "success");
  });

  // Register Service Worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/sw.js").then((reg) => {
      console.log("[PWA] Service Worker registered with scope:", reg.scope);
    }).catch((err) => {
      console.log("[PWA] Service Worker registration failed:", err);
    });
  }
});

