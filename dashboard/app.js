(function () {
  "use strict";

  const DATA_URLS = {
    customers: "../data_01/baseline_snapshots.json",
    documents: "../data_02/documents.json",
    facts: "../data_03/facts.json",
    alerts: "../data_03/alerts.json",
    aiAnalysis: "../data_03/ai_evidence_analysis.json",
    materialAlerts: "../data_06/material_alerts.json",
    noiseSuppression: "../data_06/noise_suppression.json",
    refreshSummary: "../data_06/refresh_summary.json",
    internalSignals: "../data_07/internal_monitoring_signals.json",
    fusedAlerts: "../data_07/public_internal_fused_alerts.json",
    expandedKycProfiles: "../data_07/expanded_kyc_profiles.json",
    layer2SignalPlaybook: "../data_07/layer2_signal_playbook.json"
  };

  const ACTION_STORAGE_KEY = "signalwatch.reviewActions.v1";
  const RM_OWNERS = {
    "demo-001": "Mara Keller",
    "demo-002": "Alex Meier",
    "demo-003": "Jonas Frei",
    "demo-004": "Nina Schmid",
    "demo-005": "Rafael Costa",
    "demo-006": "Lea Baumann",
    "demo-007": "Sofia Weber",
    "demo-008": "Daniel Roth",
    "demo-009": "Mara Keller"
  };
  const SEVERITY_RANK = { critical: 4, high: 3, medium: 2, low: 1 };
  const CATEGORY_RANK = { risk: 4, mixed: 3, ownership_control: 2, opportunity: 1 };
  const ACTION_TO_STATUS = {
    acknowledged: "in_review",
    escalated: "escalated",
    customer_update_requested: "customer_update_requested",
    added_to_call_brief: "added_to_call_brief",
    dismissed: "dismissed"
  };

  const state = {
    customers: [],
    documents: [],
    facts: [],
    alerts: [],
    materialAlerts: [],
    noiseSuppression: [],
    refreshSummary: {},
    internalSignals: [],
    fusedAlerts: [],
    expandedKycProfiles: [],
    layer2SignalPlaybook: [],
    customersById: new Map(),
    documentsById: new Map(),
    factsById: new Map(),
    aiAnalysesByDocument: new Map(),
    actions: [],
    selectedCustomerId: null,
    selectedAlertId: null,
    viewMode: "notifications",
    filters: {
      query: "",
      category: "all",
      severity: "all",
      status: "all"
    }
  };

  const els = {};

  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    cacheElements();
    bindEvents();

    try {
      const [
        customers,
        documents,
        facts,
        alerts,
        aiAnalysis,
        materialAlerts,
        noiseSuppression,
        refreshSummary,
        internalSignals,
        fusedAlerts,
        expandedKycProfiles,
        layer2SignalPlaybook
      ] = await Promise.all([
        fetchJson(DATA_URLS.customers),
        fetchJson(DATA_URLS.documents),
        fetchJson(DATA_URLS.facts),
        fetchJson(DATA_URLS.alerts),
        fetchJsonOptional(DATA_URLS.aiAnalysis, { analyses: [] }),
        fetchJsonOptional(DATA_URLS.materialAlerts, []),
        fetchJsonOptional(DATA_URLS.noiseSuppression, []),
        fetchJsonOptional(DATA_URLS.refreshSummary, {}),
        fetchJsonOptional(DATA_URLS.internalSignals, []),
        fetchJsonOptional(DATA_URLS.fusedAlerts, []),
        fetchJsonOptional(DATA_URLS.expandedKycProfiles, []),
        fetchJsonOptional(DATA_URLS.layer2SignalPlaybook, [])
      ]);

      state.customers = customers;
      state.documents = documents;
      state.facts = facts;
      const scoredAlertsById = new Map([...materialAlerts, ...noiseSuppression].map((alert) => [alert.alert_id, alert]));
      state.alerts = alerts.map((alert) => ({ ...alert, ...(scoredAlertsById.get(alert.alert_id) || {}) }));
      state.aiAnalysesByDocument = new Map((aiAnalysis.analyses || []).map((analysis) => [analysis.document_id, analysis]));
      state.materialAlerts = materialAlerts;
      state.noiseSuppression = noiseSuppression;
      state.refreshSummary = refreshSummary;
      state.internalSignals = internalSignals;
      state.fusedAlerts = fusedAlerts;
      state.expandedKycProfiles = expandedKycProfiles;
      state.layer2SignalPlaybook = layer2SignalPlaybook;
      state.customersById = new Map(customers.map((customer) => [customer.customer_id, customer]));
      state.documentsById = new Map(documents.map((documentItem) => [documentItem.document_id, documentItem]));
      state.factsById = new Map(facts.map((fact) => [fact.fact_id, fact]));
      state.actions = loadActions();
      seedSelection();
      showApp();
      render();
    } catch (error) {
      showError(error);
    }
  }

  function cacheElements() {
    const ids = [
      "loading",
      "errorState",
      "errorMessage",
      "app",
      "dataHealth",
      "resetDemoState",
      "notificationBadge",
      "notificationsView",
      "workspaceView",
      "notificationWindowLabel",
      "notificationCountLabel",
      "notificationRiskLabel",
      "notificationList",
      "metricCustomers",
      "metricOpen",
      "metricHigh",
      "metricRisk",
      "searchInput",
      "severityFilter",
      "statusFilter",
      "customerCountLabel",
      "customerList",
      "selectedCustomerName",
      "selectedCustomerMeta",
      "selectedCustomerStats",
      "alertQueueTitle",
      "alertQueueCount",
      "alertQueue",
      "alertDetail",
      "briefCustomerLabel",
      "copyBrief",
      "printBrief",
      "briefStatus",
      "briefContent"
    ];
    ids.forEach((id) => {
      els[id] = document.getElementById(id);
    });
  }

  function bindEvents() {
    els.searchInput.addEventListener("input", (event) => {
      state.filters.query = event.target.value.trim().toLowerCase();
      repairSelectionAfterFilter();
      render();
    });

    document.querySelectorAll("[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        state.filters.category = button.dataset.category;
        document.querySelectorAll("[data-category]").forEach((item) => {
          item.classList.toggle("active", item === button);
        });
        repairSelectionAfterFilter();
        render();
      });
    });

    document.querySelectorAll("[data-view-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        state.viewMode = button.dataset.viewMode;
        document.querySelectorAll("[data-view-mode]").forEach((item) => {
          item.classList.toggle("active", item === button);
        });
        render();
      });
    });

    els.severityFilter.addEventListener("change", (event) => {
      state.filters.severity = event.target.value;
      repairSelectionAfterFilter();
      render();
    });

    els.statusFilter.addEventListener("change", (event) => {
      state.filters.status = event.target.value;
      repairSelectionAfterFilter();
      render();
    });

    els.customerList.addEventListener("click", (event) => {
      const row = event.target.closest("[data-customer-id]");
      if (!row) return;
      selectCustomer(row.dataset.customerId);
    });

    els.alertQueue.addEventListener("click", (event) => {
      const row = event.target.closest("[data-alert-id]");
      if (!row) return;
      state.selectedAlertId = row.dataset.alertId;
      render();
    });

    els.notificationList.addEventListener("click", (event) => {
      const actionButton = event.target.closest("[data-notification-action]");
      if (actionButton) {
        event.preventDefault();
        const alert = state.materialAlerts.find((item) => item.alert_id === actionButton.dataset.notificationAlertId);
        if (!alert) return;
        recordActionForAlert(alert, actionButton.dataset.notificationAction, "");
        return;
      }

      const row = event.target.closest("[data-notification-alert-id]");
      if (!row) return;
      const alert = state.materialAlerts.find((item) => item.alert_id === row.dataset.notificationAlertId);
      if (!alert) return;
      state.selectedCustomerId = alert.customer_id;
      state.selectedAlertId = alert.alert_id;
      state.viewMode = "workspace";
      document.querySelectorAll("[data-view-mode]").forEach((item) => {
        item.classList.toggle("active", item.dataset.viewMode === state.viewMode);
      });
      render();
    });

    els.alertDetail.addEventListener("click", (event) => {
      const actionButton = event.target.closest("[data-action]");
      if (!actionButton) return;
      recordAction(actionButton.dataset.action);
    });

    els.copyBrief.addEventListener("click", copyBrief);
    els.printBrief.addEventListener("click", () => window.print());
    els.resetDemoState.addEventListener("click", () => {
      localStorage.removeItem(ACTION_STORAGE_KEY);
      state.actions = [];
      render();
    });
  }

  async function fetchJson(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Could not load ${url}: ${response.status}`);
    }
    return response.json();
  }

  async function fetchJsonOptional(url, fallback) {
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) return fallback;
      return response.json();
    } catch (_error) {
      return fallback;
    }
  }

  function showApp() {
    els.loading.hidden = true;
    els.errorState.hidden = true;
    els.app.hidden = false;
  }

  function showError(error) {
    els.loading.hidden = true;
    els.app.hidden = true;
    els.errorState.hidden = false;
    els.errorMessage.textContent = `${error.message}. Start a local server from the repo root and open /dashboard/.`;
  }

  function seedSelection() {
    const orderedAlerts = sortedAlerts(state.alerts);
    const firstAlert = orderedAlerts[0];
    state.selectedCustomerId = firstAlert ? firstAlert.customer_id : state.customers[0]?.customer_id;
    state.selectedAlertId = firstAlert ? firstAlert.alert_id : null;
  }

  function selectCustomer(customerId) {
    state.selectedCustomerId = customerId;
    const firstAlert = sortedAlerts(getFilteredAlertsForCustomer(customerId))[0];
    state.selectedAlertId = firstAlert ? firstAlert.alert_id : null;
    render();
  }

  function repairSelectionAfterFilter() {
    const visibleCustomers = getVisibleCustomers();
    if (!visibleCustomers.some((customer) => customer.customer_id === state.selectedCustomerId)) {
      state.selectedCustomerId = visibleCustomers[0]?.customer_id || state.customers[0]?.customer_id || null;
    }
    const visibleAlerts = getFilteredAlertsForCustomer(state.selectedCustomerId);
    if (!visibleAlerts.some((alert) => alert.alert_id === state.selectedAlertId)) {
      state.selectedAlertId = sortedAlerts(visibleAlerts)[0]?.alert_id || null;
    }
  }

  function render() {
    renderViewMode();
    renderNotifications();
    renderMetrics();
    renderCustomerList();
    renderWorkspaceHeader();
    renderAlertQueue();
    renderAlertDetail();
    renderBrief();
    renderDataHealth();
  }

  function renderViewMode() {
    els.notificationsView.hidden = state.viewMode !== "notifications";
    els.workspaceView.hidden = state.viewMode !== "workspace";
    document.querySelectorAll("[data-view-mode]").forEach((item) => {
      item.classList.toggle("active", item.dataset.viewMode === state.viewMode);
    });
  }

  function renderMetrics() {
    const visibleCustomers = getVisibleCustomers();
    const openAlerts = getFilteredAlerts().filter((alert) => currentStatus(alert) !== "dismissed");
    els.metricCustomers.textContent = visibleCustomers.length;
    els.metricOpen.textContent = openAlerts.length;
    els.metricHigh.textContent = openAlerts.filter((alert) => alert.severity === "high").length;
    els.metricRisk.textContent = openAlerts.filter((alert) => alert.category === "risk").length;
  }

  function renderDataHealth() {
    const lastScan = maxDate(state.documents.map((documentItem) => documentItem.collected_at));
    const lookback = state.refreshSummary.lookback_hours || 24;
    els.dataHealth.textContent = `${visibleNotifications().length} open notifications | ${getFilteredAlerts().length} focused alerts | ${lookback}h scan ${formatDateTime(lastScan)}`;
  }

  function renderNotifications() {
    const notifications = sortedAlerts(visibleNotifications());
    const hiddenCount = state.materialAlerts.length - notifications.length;
    const lookback = state.refreshSummary.lookback_hours || 24;
    const cutoff = state.refreshSummary.cutoff_at ? formatDateTime(state.refreshSummary.cutoff_at) : "unknown cutoff";
    const generated = state.refreshSummary.generated_at ? formatDateTime(state.refreshSummary.generated_at) : "unknown run";
    const riskCount = notifications.filter((alert) => alert.category === "risk").length;

    els.notificationBadge.textContent = notifications.length;
    els.notificationCountLabel.textContent = notifications.length;
    els.notificationRiskLabel.textContent = riskCount;
    els.notificationWindowLabel.textContent = `Last ${lookback} hours | cutoff ${cutoff} | refreshed ${generated}`;

    els.notificationList.innerHTML = notifications.length
      ? notifications.map((alert) => notificationTemplate(alert)).join("")
      : `
        <div class="notification-empty">
          <h2>${hiddenCount ? "All current notifications acknowledged" : `No material notifications in the last ${escapeHtml(lookback)} hours`}</h2>
          <p>${hiddenCount ? `${escapeHtml(hiddenCount)} notification(s) are hidden from this queue because they were acknowledged or dismissed. They remain available in the Customer workspace audit trail.` : `The refresh still reviewed ${escapeHtml(state.refreshSummary.total_alerts || state.alerts.length)} total alerts. Older or undated evidence was kept in the customer workspace and suppression log instead of being shown as today&apos;s news.`}</p>
        </div>
      `;
  }

  function visibleNotifications() {
    return state.materialAlerts.filter((alert) => {
      const status = currentStatus(alert);
      return !["in_review", "dismissed"].includes(status);
    });
  }

  function notificationTemplate(alert) {
    const customer = state.customersById.get(alert.customer_id);
    const publishedAt = alert.newest_published_at || alert.evidence?.[0]?.published_at;
    const fusion = fusedForAlert(alert.alert_id);
    const profile = kycProfileForCustomer(alert.customer_id);
    return `
      <article class="notification-card" role="listitem">
        <button class="notification-main" type="button" data-notification-alert-id="${escapeAttr(alert.alert_id)}">
          <div class="notification-card-top">
            <span class="customer-name">${escapeHtml(customer?.legal_name || alert.customer_id)}</span>
            <span class="severity-mark ${alert.severity}">${escapeHtml(alert.severity)}</span>
          </div>
          <h2>${escapeHtml(cleanText(alert.title))}</h2>
          <p>${escapeHtml(cleanText(alert.summary))}</p>
          <div class="alert-tags">
            <span class="pill ${alert.category}">${labelize(alert.category)}</span>
            <span class="pill material">Score ${escapeHtml(alert.material_score || "N/A")}</span>
            <span class="pill">${Math.round(alert.confidence * 100)}% confidence</span>
            ${alert.review_lane ? `<span class="pill">${escapeHtml(alert.review_lane)}</span>` : ""}
            ${fusion ? `<span class="pill material">Internal context</span>` : ""}
            ${profile ? `<span class="pill mixed">Layer 2 KYC</span>` : ""}
            <span class="pill">${formatDate(publishedAt) || "Undated"}</span>
          </div>
        </button>
        <div class="alert-source-strip">
          ${sourceLinksTemplate(alert, 2)}
        </div>
        <div class="notification-actions">
          <button class="secondary-button compact-button" type="button" data-notification-action="acknowledged" data-notification-alert-id="${escapeAttr(alert.alert_id)}">Acknowledge</button>
        </div>
      </article>
    `;
  }

  function renderCustomerList() {
    const customers = getVisibleCustomers();
    els.customerCountLabel.textContent = `${customers.length} shown`;
    els.customerList.innerHTML = customers.length
      ? customers.map((customer) => customerRowTemplate(customer)).join("")
      : `<div class="empty-state">No customers match the current filters.</div>`;
  }

  function customerRowTemplate(customer) {
    const aggregate = customerAggregate(customer.customer_id);
    const active = customer.customer_id === state.selectedCustomerId ? "active" : "";
    return `
      <button class="customer-row ${active}" type="button" data-customer-id="${escapeAttr(customer.customer_id)}" role="listitem">
        <div class="customer-topline">
          <span class="customer-name">${escapeHtml(customer.legal_name)}</span>
          <span class="severity-mark ${aggregate.highestSeverity}">${escapeHtml(aggregate.highestSeverity)}</span>
        </div>
        <div class="customer-subline">
          ${escapeHtml(RM_OWNERS[customer.customer_id] || "Demo RM")} | reviewed ${formatDate(customer.last_reviewed_at)}
        </div>
        <div class="customer-counts">
          <span class="pill">${aggregate.alertCount} alerts</span>
          <span class="pill risk">${aggregate.riskCount} risk</span>
          <span class="pill opportunity">${aggregate.opportunityCount} opp</span>
          <span class="pill ownership_control">${aggregate.ownershipCount} own</span>
        </div>
      </button>
    `;
  }

  function renderWorkspaceHeader() {
    const customer = selectedCustomer();
    if (!customer) return;
    const aggregate = customerAggregate(customer.customer_id);
    els.selectedCustomerName.textContent = customer.legal_name;
    els.selectedCustomerMeta.innerHTML = `
      <span class="pill">Risk ${escapeHtml(customer.risk_rating)}</span>
      <span class="pill">Reviewed ${formatDate(customer.last_reviewed_at)}</span>
      <span class="pill">RM ${escapeHtml(RM_OWNERS[customer.customer_id] || "Demo RM")}</span>
    `;
    els.selectedCustomerStats.innerHTML = `
      <span class="pill ${aggregate.highestSeverity}">${aggregate.highestSeverity} top severity</span>
      <span class="pill">${aggregate.alertCount} alerts</span>
      <span class="pill risk">${aggregate.riskCount} risk</span>
      <span class="pill opportunity">${aggregate.opportunityCount} opportunity</span>
    `;
  }

  function renderAlertQueue() {
    const alerts = sortedAlerts(getFilteredAlertsForCustomer(state.selectedCustomerId));
    els.alertQueueTitle.textContent = "Customer alerts";
    els.alertQueueCount.textContent = `${alerts.length} alerts`;
    els.alertQueue.innerHTML = alerts.length
      ? alerts.map((alert) => alertRowTemplate(alert)).join("")
      : `<div class="empty-state">No alerts match the current filters for this customer.</div>`;
  }

  function alertRowTemplate(alert) {
    const active = alert.alert_id === state.selectedAlertId ? "active" : "";
    const reviewedByAi = aiReviewsForAlert(alert).length > 0;
    return `
      <article class="alert-row ${active}" role="listitem">
        <button class="alert-row-main" type="button" data-alert-id="${escapeAttr(alert.alert_id)}">
          <div class="alert-topline">
            <span class="alert-title">${escapeHtml(cleanText(alert.title))}</span>
            <span class="severity-mark ${alert.severity}">${escapeHtml(alert.severity)}</span>
          </div>
          <div class="alert-subline">${escapeHtml(cleanText(alert.summary))}</div>
          <div class="alert-tags">
            <span class="pill ${alert.category}">${labelize(alert.category)}</span>
            <span class="pill">${Math.round(alert.confidence * 100)}% confidence</span>
            ${alert.material_score ? `<span class="pill material">Score ${escapeHtml(alert.material_score)}</span>` : ""}
            ${alert.review_lane ? `<span class="pill">${escapeHtml(alert.review_lane)}</span>` : ""}
            ${reviewedByAi ? `<span class="pill mixed">Document reviewed by Apertus</span>` : ""}
            <span class="pill">Signal extracted by ${escapeHtml(detectionLabel(alert.detection_method))}</span>
            ${kycProfileForCustomer(alert.customer_id) ? `<span class="pill mixed">Layer 2 KYC</span>` : ""}
            <span class="pill">${labelize(currentStatus(alert))}</span>
            <span class="pill">${alert.evidence_document_ids.length} evidence</span>
          </div>
        </button>
        <div class="alert-source-strip">
          ${sourceLinksTemplate(alert, 2)}
        </div>
      </article>
    `;
  }

  function renderAlertDetail() {
    const alert = selectedAlert();
    if (!alert) {
      els.alertDetail.innerHTML = `<div class="detail-empty">Select an alert to review evidence and actions.</div>`;
      return;
    }

    const score = Math.round(alert.confidence * 100);
    els.alertDetail.innerHTML = `
      <div class="detail-header">
        <div>
          <div class="detail-tags">
            <span class="pill ${alert.category}">${labelize(alert.category)}</span>
            <span class="pill ${alert.severity}">${labelize(alert.severity)} severity</span>
            <span class="pill">${labelize(alert.signal_type)}</span>
            ${alert.material_score ? `<span class="pill material">Material score ${escapeHtml(alert.material_score)}</span>` : ""}
            ${alert.review_lane ? `<span class="pill">${escapeHtml(alert.review_lane)}</span>` : ""}
            <span class="pill ${alert.detection_method === "ai_validated" ? "mixed" : ""}">${escapeHtml(detectionLabel(alert.detection_method))}</span>
            ${alert.needs_human_review ? `<span class="pill risk">Human review required</span>` : ""}
            <span class="pill">${labelize(currentStatus(alert))}</span>
          </div>
          <h2>${escapeHtml(cleanText(alert.title))}</h2>
          <p class="summary">${escapeHtml(cleanText(alert.summary))}</p>
          ${materialityTemplate(alert)}
          ${detectionTemplate(alert)}
          ${layer2ProfileTemplate(alert)}
          ${internalContextTemplate(alert)}
          <div class="detail-source-strip">
            ${sourceLinksTemplate(alert)}
          </div>
        </div>
        <div class="confidence-ring" style="--score: ${score}%;" aria-label="${score}% confidence">
          <span>${score}%</span>
        </div>
      </div>

      <div class="detail-grid">
        <div class="detail-block">
          <h3>Recommended action</h3>
          <div class="recommendation">${escapeHtml(cleanText(alert.recommended_action))}</div>

          <h3>Before / after KYC fields</h3>
          ${driftTableTemplate(alert)}

          <h3>Evidence</h3>
          ${evidenceTemplate(alert)}
        </div>

        <div class="detail-block">
          <h3>RM actions</h3>
          <div class="action-stack">
            <textarea id="actionNote" placeholder="Optional note for audit trail"></textarea>
            <div class="action-buttons">
              <button class="secondary-button" type="button" data-action="acknowledged">Acknowledge</button>
              <button class="primary-button" type="button" data-action="escalated">Escalate</button>
              <button class="secondary-button" type="button" data-action="customer_update_requested">Request update</button>
              <button class="secondary-button" type="button" data-action="added_to_call_brief">Add to brief</button>
              <button class="danger-button" type="button" data-action="dismissed">Dismiss</button>
            </div>
          </div>

          <h3>Action history</h3>
          ${actionLogTemplate(alert)}

          <h3>Audit IDs</h3>
          <div class="fact-id-row">
            ${alert.fact_ids.map((factId) => `<span class="pill">${escapeHtml(factId)}</span>`).join("")}
            ${alert.evidence_document_ids.map((documentId) => `<span class="pill">${escapeHtml(documentId)}</span>`).join("")}
          </div>
        </div>
      </div>
    `;
  }

  function materialityTemplate(alert) {
    if (!alert.material_score && !(alert.material_reasons || []).length) return "";
    const reasons = alert.material_reasons || [];
    return `
      <div class="materiality-box">
        <div class="materiality-head">
          <strong>Materiality filter</strong>
          <span class="pill material">Score ${escapeHtml(alert.material_score || "N/A")}</span>
          ${alert.review_lane ? `<span class="pill">${escapeHtml(alert.review_lane)}</span>` : ""}
        </div>
        ${reasons.length ? `<ul>${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>` : ""}
      </div>
    `;
  }

  function detectionTemplate(alert) {
    const method = alert.detection_method || "rule_fallback";
    const quote = alert.evidence_quote || primaryEvidenceQuote(alert);
    const reviews = aiReviewsForAlert(alert);
    const reviewModels = [...new Set(reviews.map((review) => review.model).filter(Boolean))];
    const reviewStatuses = [...new Set(reviews.map((review) => review.status).filter(Boolean))];
    return `
      <div class="materiality-box detection-box">
        <div class="materiality-head">
          <strong>Detection provenance</strong>
          ${reviews.length ? `<span class="pill mixed">Document reviewed by Apertus</span>` : `<span class="pill">Document not AI reviewed</span>`}
          <span class="pill ${method === "ai_validated" ? "mixed" : ""}">Signal extracted by ${escapeHtml(detectionLabel(method))}</span>
          ${reviewModels.length ? `<span class="pill">Review model ${escapeHtml(reviewModels.join(", "))}</span>` : ""}
          ${reviewStatuses.length ? `<span class="pill">AI status ${escapeHtml(reviewStatuses.join(", "))}</span>` : ""}
          ${alert.ai_severity_suggestion ? `<span class="pill ${alert.ai_severity_suggestion}">Apertus severity ${escapeHtml(labelize(alert.ai_severity_suggestion))}</span>` : ""}
          ${alert.needs_human_review ? `<span class="pill risk">Human review required</span>` : ""}
        </div>
        ${quote ? `<p class="evidence-excerpt"><strong>Exact evidence quote:</strong> ${escapeHtml(quote)}</p>` : ""}
      </div>
    `;
  }

  function internalContextTemplate(alert) {
    const fusion = fusedForAlert(alert.alert_id);
    const signals = internalSignalsForAlert(alert.alert_id);
    if (!fusion && !signals.length) return "";

    const visibleSignals = signals.length ? signals : (fusion?.internal_signal_summaries || []).map((summary, index) => ({
      internal_signal_id: fusion.internal_signal_ids?.[index] || `internal-${index + 1}`,
      signal_type: "internal_context",
      severity: "medium",
      confidence: 0,
      summary,
      recommended_action: fusion.recommended_workflow || "Human review required."
    }));

    return `
      <div class="materiality-box internal-box">
        <div class="materiality-head">
          <strong>Internal bank context</strong>
          ${fusion ? `<span class="pill material">Fused score ${escapeHtml(fusion.fused_score)}</span>` : ""}
          <span class="pill">${escapeHtml(visibleSignals.length)} signal(s)</span>
        </div>
        ${fusion ? `<p class="summary">${escapeHtml(fusion.fusion_rationale)}</p>` : ""}
        <ul>
          ${visibleSignals.map((signal) => `
            <li>
              <strong>${escapeHtml(labelize(signal.signal_type))}</strong>:
              ${escapeHtml(cleanText(signal.summary))}
              <span class="muted"> ${escapeHtml(cleanText(signal.recommended_action || ""))}</span>
            </li>
          `).join("")}
        </ul>
      </div>
    `;
  }

  function layer2ProfileTemplate(alert) {
    const profile = kycProfileForCustomer(alert.customer_id);
    if (!profile) return "";

    const baseline = profile.baseline_kyc_profile || {};
    const transactionProfile = baseline.expected_transaction_profile || {};
    const expectedModel = (baseline.expected_business_model || []).slice(0, 3);
    const flags = (profile.layer_2_highlight_flags || []).slice(0, 4);
    const outcome = profile.expected_outcome || {};

    return `
      <div class="materiality-box layer2-box">
        <div class="materiality-head">
          <strong>Layer 2 KYC baseline</strong>
          <span class="pill mixed">Simulated internal bank profile</span>
          <span class="pill">Risk ${escapeHtml(baseline.initial_risk_rating || "unknown")}</span>
        </div>
        <div class="kyc-baseline-grid">
          <div>
            <span class="field-label">Expected model</span>
            <ul class="value-list">
              ${expectedModel.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          </div>
          <div>
            <span class="field-label">Expected activity</span>
            <div class="kyc-stat-row">
              <span><strong>${formatChf(transactionProfile.expected_monthly_volume_chf)}</strong> monthly volume</span>
              <span><strong>${escapeHtml(transactionProfile.expected_transaction_count_monthly || "N/A")}</strong> tx/month</span>
              <span><strong>${formatChf(transactionProfile.typical_single_payment_chf?.review_threshold)}</strong> review threshold</span>
            </div>
            <div class="alert-tags kyc-tags">
              ${(transactionProfile.expected_counterparty_regions || []).map((region) => `<span class="pill">${escapeHtml(region)}</span>`).join("")}
              ${(transactionProfile.expected_products || []).map((product) => `<span class="pill">${escapeHtml(product)}</span>`).join("")}
            </div>
          </div>
        </div>
        ${outcome.rm_tldr ? `<p class="summary"><strong>RM TLDR:</strong> ${escapeHtml(outcome.rm_tldr)}</p>` : ""}
        ${flags.length ? `
          <ul class="layer2-flag-list">
            ${flags.map((flag) => `
              <li>
                <strong>${escapeHtml(flag.expected_flag)}</strong>
                <span class="pill">${escapeHtml(labelize(flag.current_status))}</span>
                <p>${escapeHtml(flag.evidence)}</p>
                <span class="muted">${escapeHtml(flag.recommended_action)}</span>
              </li>
            `).join("")}
          </ul>
        ` : ""}
        ${kycSourceLinksTemplate(profile)}
        <p class="layer2-demo-note">${escapeHtml(profile.important_demo_notice || "")}</p>
      </div>
    `;
  }

  function kycSourceLinksTemplate(profile) {
    const sources = (profile.research_sources || []).filter((source) => source.source_url);
    if (!sources.length) return "";
    return `
      <div class="detail-source-strip layer2-source-strip">
        ${sources.map((source) => `
          <a class="source-link" href="${escapeAttr(source.source_url)}" target="_blank" rel="noreferrer">
            <span>Open source</span>
            <strong>${escapeHtml(source.source_name)}</strong>
            <small>${escapeHtml(source.how_used || "")}</small>
          </a>
        `).join("")}
      </div>
    `;
  }

  function driftTableTemplate(alert) {
    const rows = alert.changed_fields.map((field) => {
      const before = alert.baseline_value ? alert.baseline_value[field] : null;
      const after = alert.new_value ? alert.new_value[field] : null;
      return `
        <tr>
          <td><strong>${escapeHtml(labelize(field))}</strong></td>
          <td>${valueTemplate(before)}</td>
          <td>${valueTemplate(after)}</td>
        </tr>
      `;
    });

    return `
      <table class="drift-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Baseline</th>
            <th>Detected change</th>
          </tr>
        </thead>
        <tbody>${rows.join("")}</tbody>
      </table>
    `;
  }

  function evidenceTemplate(alert) {
    const evidenceItems = (alert.evidence || []).map((evidence) => {
      const sourceUrl = evidence.source_url || "#";
      const review = state.aiAnalysesByDocument.get(evidence.document_id);
      return `
        <li class="evidence-item">
          <div class="evidence-title">
            <a href="${escapeAttr(sourceUrl)}" target="_blank" rel="noreferrer">${escapeHtml(cleanText(evidence.source_name || evidence.title || evidence.document_id))}</a>
            <span class="pill">Quality ${escapeHtml(evidence.source_quality || "N/A")}</span>
          </div>
          <div class="evidence-meta">
            <span class="pill">${escapeHtml(labelize(evidence.source_type || "source"))}</span>
            <span class="pill">${formatDate(evidence.published_at) || "Undated"}</span>
            <span class="pill">${escapeHtml(evidence.document_id)}</span>
            ${review ? `<span class="pill mixed">Document reviewed by Apertus</span>` : ""}
            ${evidence.detection_method ? `<span class="pill">${escapeHtml(detectionLabel(evidence.detection_method))}</span>` : ""}
            ${review?.model ? `<span class="pill">Review model ${escapeHtml(review.model)}</span>` : ""}
            ${review?.status ? `<span class="pill">AI status ${escapeHtml(review.status)}</span>` : ""}
            ${evidence.needs_human_review ? `<span class="pill risk">Human review required</span>` : ""}
          </div>
          <p class="evidence-excerpt">${escapeHtml(cleanText(evidence.excerpt || ""))}</p>
          ${evidence.evidence_quote ? `<p class="evidence-excerpt"><strong>Quote:</strong> ${escapeHtml(evidence.evidence_quote)}</p>` : ""}
        </li>
      `;
    });

    return evidenceItems.length
      ? `<ul class="evidence-list">${evidenceItems.join("")}</ul>`
      : `<div class="empty-state">No evidence attached.</div>`;
  }

  function sourceLinksTemplate(alert, limit = Infinity) {
    const evidence = uniqueEvidence([alert]).filter((item) => item.source_url);
    if (!evidence.length) {
      return `<span class="source-link-muted">No source URL</span>`;
    }

    const visible = evidence.slice(0, limit);
    const extraCount = evidence.length - visible.length;
    const links = visible.map((item) => {
      const label = cleanText(item.source_name || item.title || item.document_id || "Source");
      const meta = item.source_type ? ` ${labelize(item.source_type)}` : "";
      return `
        <a class="source-link" href="${escapeAttr(item.source_url)}" target="_blank" rel="noreferrer">
          <span>Open source</span>
          <strong>${escapeHtml(label)}</strong>
          <small>${escapeHtml(item.document_id || "")}${escapeHtml(meta)}</small>
        </a>
      `;
    });

    if (extraCount > 0) {
      links.push(`<span class="source-link-more">+${extraCount} more in detail</span>`);
    }
    return links.join("");
  }

  function actionLogTemplate(alert) {
    const actions = actionsForAlert(alert);
    if (!actions.length) {
      return `<div class="empty-state">No RM action recorded.</div>`;
    }
    return `
      <ul class="action-log">
        ${actions.map((action) => `
          <li class="action-item">
            <strong>${escapeHtml(labelize(action.action))}</strong>
            <div class="action-meta">
              <span class="pill">${formatDateTime(action.created_at)}</span>
              <span class="pill">${escapeHtml(action.created_by)}</span>
            </div>
            ${action.note ? `<p class="summary">${escapeHtml(action.note)}</p>` : ""}
          </li>
        `).join("")}
      </ul>
    `;
  }

  function renderBrief() {
    const customer = selectedCustomer();
    if (!customer) return;
    const alerts = state.alerts.filter((alert) => alert.customer_id === customer.customer_id);
    const brief = buildBrief(customer, alerts);
    els.briefCustomerLabel.textContent = customer.legal_name;
    els.briefContent.innerHTML = briefHtmlTemplate(brief);
  }

  function buildBrief(customer, alerts) {
    const enrichedAlerts = sortedAlerts(alerts);
    const materialChanges = enrichedAlerts.filter((alert) => {
      return alert.severity === "high" || alert.category === "ownership_control" || alert.signal_type === "risk_rating_review";
    }).slice(0, 5);

    const riskQuestions = enrichedAlerts.filter((alert) => {
      const status = currentStatus(alert);
      return alert.category === "risk" || status === "escalated" || alert.signal_type === "jurisdiction_restriction";
    }).slice(0, 5);

    const opportunities = enrichedAlerts.filter((alert) => {
      const status = currentStatus(alert);
      return alert.category === "opportunity" || status === "added_to_call_brief" || ["commercial_opportunity", "treasury_policy_change"].includes(alert.signal_type);
    }).slice(0, 5);

    const suggestedQuestions = suggestedQuestionsForAlerts(enrichedAlerts).slice(0, 5);
    const evidenceReferences = uniqueEvidence(enrichedAlerts).slice(0, 5);

    return {
      customer,
      materialChanges,
      riskQuestions,
      opportunities,
      suggestedQuestions,
      evidenceReferences
    };
  }

  function briefHtmlTemplate(brief) {
    return `
      ${briefSectionTemplate("Material changes", brief.materialChanges, alertBriefItem)}
      ${briefSectionTemplate("Open risk questions", brief.riskQuestions, alertBriefItem)}
      ${briefSectionTemplate("Commercial opportunities", brief.opportunities, alertBriefItem)}
      ${briefSectionTemplate("Suggested customer questions", brief.suggestedQuestions, questionBriefItem)}
      ${briefSectionTemplate("Evidence references", brief.evidenceReferences, evidenceBriefItem)}
    `;
  }

  function briefSectionTemplate(title, items, renderer) {
    if (!items.length) {
      return `
        <section class="brief-section">
          <h3>${escapeHtml(title)}</h3>
          <div class="empty-state">No current items.</div>
        </section>
      `;
    }
    return `
      <section class="brief-section">
        <h3>${escapeHtml(title)}</h3>
        <ul class="brief-list">
          ${items.map(renderer).join("")}
        </ul>
      </section>
    `;
  }

  function alertBriefItem(alert) {
    return `
      <li class="brief-item">
        <strong>${escapeHtml(cleanText(alert.title))}</strong>
        <p>${escapeHtml(cleanText(alert.recommended_action))}</p>
      </li>
    `;
  }

  function questionBriefItem(question) {
    return `
      <li class="brief-item">
        <p>${escapeHtml(question)}</p>
      </li>
    `;
  }

  function evidenceBriefItem(evidence) {
    return `
      <li class="brief-item">
        <strong>${escapeHtml(cleanText(evidence.source_name || evidence.title || evidence.document_id))}</strong>
        <p>${escapeHtml(cleanText(evidence.excerpt || ""))}</p>
      </li>
    `;
  }

  function suggestedQuestionsForAlerts(alerts) {
    const questions = [];
    alerts.forEach((alert) => {
      if (alert.category === "ownership_control" || alert.signal_type === "ownership_change") {
        questions.push("Can you confirm the current corporate structure, legal entities, and beneficial ownership records?");
      }
      if (alert.signal_type === "new_jurisdiction" || alert.signal_type === "jurisdiction_restriction") {
        questions.push("Which operating jurisdictions and client eligibility restrictions should AMINA update in KYC?");
      }
      if (alert.signal_type === "domain_registration") {
        questions.push("Does the country-code domain reflect defensive registration, pre-launch planning, or active local business activity?");
      }
      if (alert.category === "risk" || alert.signal_type === "regulatory_scrutiny") {
        questions.push("Are there active licensing, regulatory, or market-access issues AMINA should document?");
      }
      if (["digital_asset_activity", "treasury_policy_change", "commercial_opportunity"].includes(alert.signal_type)) {
        questions.push("Would custody, trading, lending, FX, payments, or treasury support be relevant for the next quarter?");
      }
      if (alert.category === "opportunity" || alert.signal_type === "new_product") {
        questions.push("Which new product or expansion plans should the RM map to AMINA services?");
      }
    });
    return Array.from(new Set(questions));
  }

  function uniqueEvidence(alerts) {
    const seen = new Set();
    const evidenceItems = [];
    alerts.forEach((alert) => {
      (alert.evidence || []).forEach((evidence) => {
        if (seen.has(evidence.document_id)) return;
        seen.add(evidence.document_id);
        evidenceItems.push(evidence);
      });
    });
    return evidenceItems;
  }

  function primaryEvidenceQuote(alert) {
    const evidence = (alert.evidence || []).find((item) => item.evidence_quote || item.excerpt);
    return evidence ? cleanText(evidence.evidence_quote || evidence.excerpt || "") : "";
  }

  function detectionLabel(value) {
    if (value === "ai_validated") return "AI validated";
    return "Rule fallback";
  }

  function copyBrief() {
    const customer = selectedCustomer();
    if (!customer) return;
    const briefText = buildBriefText(buildBrief(customer, state.alerts.filter((alert) => alert.customer_id === customer.customer_id)));
    navigator.clipboard.writeText(briefText).then(() => {
      els.briefStatus.textContent = "Brief copied.";
      window.setTimeout(() => {
        els.briefStatus.textContent = "";
      }, 2000);
    }).catch(() => {
      els.briefStatus.textContent = "Copy failed. Select the brief text manually.";
    });
  }

  function buildBriefText(brief) {
    const lines = [
      `SignalWatch RM Brief - ${brief.customer.legal_name}`,
      `Baseline risk: ${brief.customer.risk_rating}`,
      `Last reviewed: ${brief.customer.last_reviewed_at}`,
      ""
    ];

    appendTextSection(lines, "Material changes", brief.materialChanges.map((alert) => `${alert.title} | ${alert.recommended_action}`));
    appendTextSection(lines, "Open risk questions", brief.riskQuestions.map((alert) => `${alert.title} | ${alert.recommended_action}`));
    appendTextSection(lines, "Commercial opportunities", brief.opportunities.map((alert) => `${alert.title} | ${alert.recommended_action}`));
    appendTextSection(lines, "Suggested customer questions", brief.suggestedQuestions);
    appendTextSection(lines, "Evidence references", brief.evidenceReferences.map((evidence) => `${evidence.source_name}: ${evidence.source_url}`));
    return lines.join("\n");
  }

  function appendTextSection(lines, title, items) {
    lines.push(title);
    if (!items.length) {
      lines.push("- No current items.");
    } else {
      items.forEach((item) => lines.push(`- ${cleanText(item)}`));
    }
    lines.push("");
  }

  function recordAction(action) {
    const alert = selectedAlert();
    if (!alert) return;
    recordActionForAlert(alert, action);
  }

  function recordActionForAlert(alert, action, noteOverride) {
    const noteElement = document.getElementById("actionNote");
    const actionRecord = {
      id: `action-${Date.now()}`,
      alert_id: alert.alert_id,
      notification_key: notificationKey(alert),
      customer_id: alert.customer_id,
      action,
      note: noteOverride !== undefined ? noteOverride : (noteElement ? noteElement.value.trim() : ""),
      created_by: "demo-rm",
      created_at: new Date().toISOString()
    };
    state.actions.push(actionRecord);
    saveActions();
    render();
  }

  function loadActions() {
    try {
      return JSON.parse(localStorage.getItem(ACTION_STORAGE_KEY) || "[]");
    } catch (_error) {
      return [];
    }
  }

  function saveActions() {
    localStorage.setItem(ACTION_STORAGE_KEY, JSON.stringify(state.actions));
  }

  function currentStatus(alert) {
    const latestAction = actionsForAlert(alert).slice(-1)[0];
    if (!latestAction) return alert.status || "new";
    return ACTION_TO_STATUS[latestAction.action] || latestAction.action;
  }

  function actionsForAlert(alertOrId) {
    const alert = typeof alertOrId === "object" ? alertOrId : null;
    const alertId = alert ? alert.alert_id : alertOrId;
    const key = alert ? notificationKey(alert) : null;
    return state.actions
      .filter((action) => action.alert_id === alertId || (key && action.notification_key === key))
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  }

  function notificationKey(alert) {
    const sourceUrl = alert.primary_source_url
      || (alert.evidence || []).map((item) => item.source_url).filter(Boolean).sort()[0]
      || "";
    return [
      alert.customer_id,
      alert.signal_type,
      normalizeKey(alert.title),
      normalizeKey(sourceUrl)
    ].join("|");
  }

  function normalizeKey(value) {
    return cleanText(value).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }

  function getVisibleCustomers() {
    const matchingAlertsByCustomer = new Map();
    getFilteredAlerts().forEach((alert) => {
      if (!matchingAlertsByCustomer.has(alert.customer_id)) {
        matchingAlertsByCustomer.set(alert.customer_id, []);
      }
      matchingAlertsByCustomer.get(alert.customer_id).push(alert);
    });

    const query = state.filters.query;
    const watchlist = notificationCustomerScope();
    return state.customers
      .filter((customer) => {
        if (watchlist && !watchlist.has(customer.customer_id)) {
          return false;
        }
        const customerText = [customer.legal_name, customer.customer_id, customer.risk_rating].join(" ").toLowerCase();
        const customerMatches = !query || customerText.includes(query);
        return customerMatches || matchingAlertsByCustomer.has(customer.customer_id);
      })
      .sort((a, b) => {
        const aggregateA = customerAggregate(a.customer_id);
        const aggregateB = customerAggregate(b.customer_id);
        return SEVERITY_RANK[aggregateB.highestSeverity] - SEVERITY_RANK[aggregateA.highestSeverity]
          || aggregateB.alertCount - aggregateA.alertCount
          || a.legal_name.localeCompare(b.legal_name);
      });
  }

  function getFilteredAlertsForCustomer(customerId) {
    return getFilteredAlerts().filter((alert) => alert.customer_id === customerId);
  }

  function getFilteredAlerts() {
    const watchlist = notificationCustomerScope();
    return state.alerts.filter((alert) => {
      if (watchlist && !watchlist.has(alert.customer_id)) {
        return false;
      }
      const query = state.filters.query;
      const customer = state.customersById.get(alert.customer_id);
      const searchable = [
        alert.title,
        alert.summary,
        alert.signal_type,
        alert.category,
        alert.review_lane,
        ...(alert.material_reasons || []),
        customer?.legal_name
      ].join(" ").toLowerCase();

      const categoryMatches = state.filters.category === "all" || alert.category === state.filters.category;
      const severityMatches = state.filters.severity === "all" || alert.severity === state.filters.severity;
      const statusMatches = state.filters.status === "all" || currentStatus(alert) === state.filters.status;
      const queryMatches = !query || searchable.includes(query);
      return categoryMatches && severityMatches && statusMatches && queryMatches;
    });
  }

  function notificationCustomerScope() {
    const scope = state.refreshSummary.notification_customer_ids;
    if (!Array.isArray(scope) || !scope.length) {
      return null;
    }
    return new Set(scope);
  }

  function selectedCustomer() {
    return state.customersById.get(state.selectedCustomerId) || null;
  }

  function selectedAlert() {
    return state.materialAlerts.find((alert) => alert.alert_id === state.selectedAlertId)
      || state.alerts.find((alert) => alert.alert_id === state.selectedAlertId)
      || null;
  }

  function aiReviewsForAlert(alert) {
    return (alert.evidence_document_ids || [])
      .map((documentId) => state.aiAnalysesByDocument.get(documentId))
      .filter(Boolean);
  }

  function fusedForAlert(alertId) {
    return state.fusedAlerts.find((item) => item.alert_id === alertId) || null;
  }

  function internalSignalsForAlert(alertId) {
    const fusion = fusedForAlert(alertId);
    if (!fusion) return [];
    const ids = new Set(fusion.internal_signal_ids || []);
    return state.internalSignals.filter((signal) => ids.has(signal.internal_signal_id));
  }

  function kycProfileForCustomer(customerId) {
    return state.expandedKycProfiles.find((profile) => profile.customer_id === customerId) || null;
  }

  function customerAggregate(customerId) {
    const alerts = state.alerts.filter((alert) => alert.customer_id === customerId && currentStatus(alert) !== "dismissed");
    const severity = alerts.reduce((highest, alert) => {
      return SEVERITY_RANK[alert.severity] > SEVERITY_RANK[highest] ? alert.severity : highest;
    }, "low");

    return {
      alertCount: alerts.length,
      riskCount: alerts.filter((alert) => alert.category === "risk").length,
      opportunityCount: alerts.filter((alert) => alert.category === "opportunity").length,
      ownershipCount: alerts.filter((alert) => alert.category === "ownership_control").length,
      highestSeverity: alerts.length ? severity : "low"
    };
  }

  function sortedAlerts(alerts) {
    return [...alerts].sort((a, b) => {
      return SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity]
        || CATEGORY_RANK[b.category] - CATEGORY_RANK[a.category]
        || (b.material_score || 0) - (a.material_score || 0)
        || b.confidence - a.confidence
        || new Date(b.created_at) - new Date(a.created_at)
        || a.title.localeCompare(b.title);
    });
  }

  function valueTemplate(value) {
    if (value === null || value === undefined || value === "") {
      return `<span class="muted">Not listed</span>`;
    }
    if (Array.isArray(value)) {
      if (!value.length) return `<span class="muted">None</span>`;
      return `<ul class="value-list">${value.map((item) => `<li>${escapeHtml(cleanText(item))}</li>`).join("")}</ul>`;
    }
    if (typeof value === "object") {
      const entries = Object.entries(value);
      if (!entries.length) return `<span class="muted">None</span>`;
      return `<ul class="value-list">${entries.map(([key, item]) => `<li><strong>${escapeHtml(labelize(key))}:</strong> ${escapeHtml(cleanText(item))}</li>`).join("")}</ul>`;
    }
    return escapeHtml(cleanText(value));
  }

  function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric"
    }).format(date);
  }

  function formatDateTime(value) {
    if (!value) return "unknown";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "unknown";
    return new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    }).format(date);
  }

  function formatChf(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return "CHF N/A";
    return new Intl.NumberFormat("en-CH", {
      style: "currency",
      currency: "CHF",
      maximumFractionDigits: 0
    }).format(value);
  }

  function maxDate(values) {
    const dates = values
      .map((value) => new Date(value))
      .filter((date) => !Number.isNaN(date.getTime()))
      .sort((a, b) => b - a);
    return dates[0]?.toISOString() || "";
  }

  function labelize(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) => character.toUpperCase());
  }

  function cleanText(value) {
    return replaceMojibake(String(value ?? ""))
      .replace(/\s+/g, " ")
      .trim();
  }

  function replaceMojibake(value) {
    const replacements = [
      [String.fromCharCode(0x00e2, 0x20ac, 0x0153), "\""],
      [String.fromCharCode(0x00e2, 0x20ac, 0x009d), "\""],
      [String.fromCharCode(0x00e2, 0x20ac, 0x02dc), "'"],
      [String.fromCharCode(0x00e2, 0x20ac, 0x2122), "'"],
      [String.fromCharCode(0x00e2, 0x20ac, 0x201d), "-"],
      [String.fromCharCode(0x00e2, 0x20ac, 0x201c), "-"],
      [String.fromCharCode(0x00c2), ""]
    ];
    return replacements.reduce((text, pair) => text.split(pair[0]).join(pair[1]), value);
  }

  function escapeHtml(value) {
    return cleanText(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeAttr(value) {
    return escapeHtml(value);
  }
})();
