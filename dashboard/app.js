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
    layer2SignalPlaybook: "../data_07/layer2_signal_playbook.json",
    founderInvestor: "../data_08/founder_investor_intelligence.json",
    publicKyc: "../data_09/public_kyc_profiles.json"
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

  const GEO_COUNTRIES = {
    "Australia": {
      id: "AU",
      lat: -25.27,
      lon: 133.78,
      regulator: "Australian Securities & Investments Commission",
      url: "https://asic.gov.au/regulatory-resources/"
    },
    "Bermuda": {
      id: "BM",
      lat: 32.31,
      lon: -64.75,
      regulator: "Bermuda Monetary Authority",
      url: "https://www.bma.bm/regulatory-framework"
    },
    "Canada": {
      id: "CA",
      lat: 56.13,
      lon: -106.35,
      regulator: "FINTRAC",
      url: "https://fintrac-canafe.canada.ca/guidance-directives/overview-apercu/Guide1/1-eng"
    },
    "Estonia": {
      id: "EE",
      lat: 58.6,
      lon: 25.01,
      regulator: "Estonian Financial Intelligence Unit",
      url: "https://fiu.ee/en"
    },
    "European Union": {
      allianceType: "alliance",
      memberIds: [
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE"
      ],
      lat: 50.85,
      lon: 4.35,
      regulator: "European Commission financial services regulation",
      url: "https://finance.ec.europa.eu/regulation-and-supervision_en"
    },
    "Japan": {
      id: "JP",
      lat: 36.2,
      lon: 138.25,
      regulator: "Financial Services Agency Japan",
      url: "https://www.fsa.go.jp/en/"
    },
    "Jersey": {
      id: "JE",
      lat: 49.21,
      lon: -2.13,
      regulator: "Jersey Financial Services Commission",
      url: "https://www.jerseyfsc.org/industry/regulated-entities/"
    },
    "Luxembourg": {
      id: "LU",
      lat: 49.82,
      lon: 6.13,
      regulator: "CSSF Luxembourg",
      url: "https://www.cssf.lu/en/"
    },
    "North Korea": {
      id: "KP",
      lat: 40.34,
      lon: 127.51,
      regulator: "U.S. Treasury OFAC North Korea sanctions",
      url: "https://ofac.treasury.gov/sanctions-programs-and-country-information/north-korea-sanctions"
    },
    "Russia": {
      id: "RU",
      lat: 55.75,
      lon: 37.62,
      regulator: "U.S. Treasury OFAC Russia sanctions",
      url: "https://ofac.treasury.gov/sanctions-programs-and-country-information/russia-related-sanctions"
    },
    "Singapore": {
      id: "SG",
      lat: 1.35,
      lon: 103.82,
      regulator: "Monetary Authority of Singapore",
      url: "https://www.mas.gov.sg/regulation"
    },
    "Spain": {
      id: "ES",
      lat: 40.42,
      lon: -3.7,
      regulator: "CNMV Spain",
      url: "https://www.cnmv.es/portal/Legislacion/Legislacion/NormativaCNMV.aspx?lang=en"
    },
    "Taiwan": {
      id: "TW",
      lat: 23.7,
      lon: 121.0,
      regulator: "Financial Supervisory Commission Taiwan",
      url: "https://www.fsc.gov.tw/en/"
    },
    "United Kingdom": {
      id: "GB",
      lat: 55.38,
      lon: -3.44,
      regulator: "Financial Conduct Authority",
      url: "https://www.fca.org.uk/firms"
    },
    "United States": {
      id: "US",
      lat: 39.83,
      lon: -98.58,
      regulator: "Financial Crimes Enforcement Network",
      url: "https://www.fincen.gov/resources/statutes-regulations"
    }
  };
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
    founderInvestor: { customers: [] },
    publicKyc: { customers: [] },
    customersById: new Map(),
    documentsById: new Map(),
    factsById: new Map(),
    aiAnalysesByDocument: new Map(),
    founderInvestorByCustomer: new Map(),
    publicKycByCustomer: new Map(),
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
  let geoChart = null;

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
        layer2SignalPlaybook,
        founderInvestor,
        publicKyc
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
        fetchJsonOptional(DATA_URLS.layer2SignalPlaybook, []),
        fetchJsonOptional(DATA_URLS.founderInvestor, { customers: [] }),
        fetchJsonOptional(DATA_URLS.publicKyc, { customers: [] })
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
      state.founderInvestor = founderInvestor;
      state.publicKyc = publicKyc;
      state.customersById = new Map(customers.map((customer) => [customer.customer_id, customer]));
      state.documentsById = new Map(documents.map((documentItem) => [documentItem.document_id, documentItem]));
      state.factsById = new Map(facts.map((fact) => [fact.fact_id, fact]));
      state.founderInvestorByCustomer = new Map((founderInvestor.customers || []).map((item) => [item.customer_id, item]));
      state.publicKycByCustomer = new Map((publicKyc.customers || []).map((item) => [item.customer_id, item]));
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
      "geoFootprintTitle",
      "geoMap",
      "geoCountryCard",
      "geoCountryChips",
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



    [els.geoMap, els.geoCountryChips].forEach((container) => {
      container.addEventListener("click", (event) => {
        const row = event.target.closest("[data-geo-country]");
        if (!row) return;
        state.selectedGeoCountry = row.dataset.geoCountry;
        renderGeographicFootprint();
      });
    });

    els.copyBrief.addEventListener("click", copyBrief);
    els.printBrief.addEventListener("click", () => window.print());
    els.resetDemoState.addEventListener("click", () => {
      localStorage.removeItem(ACTION_STORAGE_KEY);
      state.actions = [];
      render();
    });

    // ── Brief panel collapse toggle ───────────────────────────────────────
    const briefToggle = document.getElementById("briefPanelToggle");
    const grid = els.workspaceView;

    function applyBriefCollapse(collapsed) {
      grid.classList.toggle("brief-collapsed", collapsed);
      if (briefToggle) {
        briefToggle.setAttribute(
          "aria-label",
          collapsed ? "Expand RM brief panel" : "Collapse RM brief panel"
        );
        briefToggle.setAttribute("title", collapsed ? "Expand panel" : "Collapse panel");
      }
      sessionStorage.setItem("briefPanelCollapsed", collapsed ? "1" : "0");
    }

    // Restore previous state
    if (sessionStorage.getItem("briefPanelCollapsed") === "1") {
      applyBriefCollapse(true);
    }

    if (briefToggle) {
      briefToggle.addEventListener("click", () => {
        applyBriefCollapse(!grid.classList.contains("brief-collapsed"));
      });
    }
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
    state.selectedGeoCountry = null;
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
    renderGeographicFootprint();
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
    if (els.metricCustomers) els.metricCustomers.textContent = visibleCustomers.length;
    if (els.metricOpen) els.metricOpen.textContent = openAlerts.length;
    if (els.metricHigh) els.metricHigh.textContent = openAlerts.filter((alert) => alert.severity === "high").length;
    if (els.metricRisk) els.metricRisk.textContent = openAlerts.filter((alert) => alert.category === "risk").length;
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
    els.customerCountLabel.textContent = `Showing ${customers.length} filtered result${customers.length !== 1 ? "s" : ""}`;
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
    const rm = escapeHtml(RM_OWNERS[customer.customer_id] || "Demo RM");
    const reviewed = formatDate(customer.last_reviewed_at);
    const riskRating = escapeHtml(customer.risk_rating || "Unknown");
    const riskClass = riskRating.toLowerCase();

    els.selectedCustomerName.textContent = customer.legal_name;
    els.selectedCustomerMeta.innerHTML = `
      <span class="customer-band-rm">RM ${rm}</span>
      <span class="customer-band-dot" aria-hidden="true">·</span>
      <span class="customer-band-reviewed">last reviewed ${reviewed}</span>
      <span class="customer-band-dot" aria-hidden="true">·</span>
      <span class="customer-band-risk ${riskClass}">Current risk rating: <strong>${riskRating}</strong></span>
    `;
    els.selectedCustomerStats.innerHTML = `
      <span class="customer-band-summary">${aggregate.alertCount} alert${aggregate.alertCount !== 1 ? "s" : ""}</span>
      <span class="customer-band-dot" aria-hidden="true">·</span>
      <span class="customer-band-summary risk">${aggregate.riskCount} risk</span>
      <span class="customer-band-dot" aria-hidden="true">·</span>
      <span class="customer-band-summary opportunity">${aggregate.opportunityCount} opportunity</span>
      ${aggregate.ownershipCount > 0 ? `<span class="customer-band-dot" aria-hidden="true">·</span><span class="customer-band-summary ownership_control">${aggregate.ownershipCount} ownership</span>` : ""}
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
    const status = currentStatus(alert);
    const isNew = status === "new";
    const combinedBadge = `${labelize(alert.category)} · ${labelize(alert.severity)}`;
    return `
      <article class="alert-row ${active}" role="listitem">
        <button class="alert-row-main" type="button" data-alert-id="${escapeAttr(alert.alert_id)}">
          <div class="alert-topline">
            <span class="alert-title">${escapeHtml(cleanText(alert.title))}</span>
            <div class="alert-topline-right">
              ${isNew ? `<span class="new-dot" title="New" aria-label="New"></span>` : ""}
              <span class="combined-badge ${alert.category} ${alert.severity}">${escapeHtml(combinedBadge)}</span>
            </div>
          </div>
          <div class="alert-subline">${escapeHtml(cleanText(alert.summary))}</div>
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

    const score        = Math.round(alert.confidence * 100);
    const status       = currentStatus(alert);
    const isNew        = status === "new";
    const combinedBadge = `${labelize(alert.category)} \u00b7 ${labelize(alert.severity)}`;
    const hasDrift     = alert.changed_fields && alert.changed_fields.length > 0;

    // ── Accordion 1: What changed? ───────────────────────────────────────────
    const acc1 = `
      <details class="intel-accordion" open>
        <summary class="intel-accordion-summary">
          <span class="intel-accordion-num">1</span>
          <span class="intel-accordion-title">What changed?</span>
          <div class="intel-accordion-badges">
            <span class="combined-badge ${alert.category} ${alert.severity}">${escapeHtml(combinedBadge)}</span>
            ${isNew ? `<span class="pill new-badge">New</span>` : `<span class="pill">${escapeHtml(labelize(status))}</span>`}
          </div>
          <span class="intel-accordion-chevron" aria-hidden="true"></span>
        </summary>
        <div class="intel-accordion-body">
          <h3 class="intel-event-title">${escapeHtml(cleanText(alert.title))}</h3>
          <div class="intel-fact-row">
            <div class="intel-fact">
              <span class="intel-fact-label">Detected</span>
              <span class="intel-fact-value">${formatDate(alert.detected_at) || "Unknown"}</span>
            </div>
            <div class="intel-fact">
              <span class="intel-fact-label">Confidence</span>
              <span class="intel-fact-value">${score}%</span>
            </div>
            ${alert.material_score ? `
            <div class="intel-fact">
              <span class="intel-fact-label">Materiality score</span>
              <span class="intel-fact-value intel-fact-material">${escapeHtml(alert.material_score)}</span>
            </div>` : ""}
            ${alert.review_lane ? `
            <div class="intel-fact">
              <span class="intel-fact-label">Review lane</span>
              <span class="intel-fact-value">${escapeHtml(alert.review_lane)}</span>
            </div>` : ""}
          </div>
          ${hasDrift ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Before / After comparison</p>
            ${driftTableTemplate(alert)}
          </div>` : ""}
        </div>
      </details>
    `;

    // ── Accordion 2: Why does it matter? ────────────────────────────────────
    const publicKyc    = publicKycForCustomer(alert.customer_id);
    const riskRationale = (publicKyc?.risk_rationale || []).slice(0, 4);
    const sanctions     = [...(publicKyc?.regulatory_and_licensing || []).slice(0, 3),
                            ...(publicKyc?.sanctions_adverse_media || []).slice(0, 3)];
    const matReasons    = (alert.material_reasons || []).slice(0, 4);
    const fusion        = fusedForAlert(alert.alert_id);

    const acc2 = `
      <details class="intel-accordion">
        <summary class="intel-accordion-summary">
          <span class="intel-accordion-num">2</span>
          <span class="intel-accordion-title">Why does it matter?</span>
          <span class="intel-accordion-chevron" aria-hidden="true"></span>
        </summary>
        <div class="intel-accordion-body">
          <p class="intel-narrative">${escapeHtml(cleanText(alert.summary))}</p>
          ${matReasons.length ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Materiality signals</p>
            <ul class="intel-list">${matReasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
          </div>` : ""}
          ${riskRationale.length ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Risk rationale</p>
            <ul class="intel-list">${riskRationale.map(r => `<li>${escapeHtml(cleanText(r))}</li>`).join("")}</ul>
          </div>` : ""}
          ${sanctions.length ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Regulatory &amp; sanctions context</p>
            <ul class="intel-list">${sanctions.map(s => `<li>${escapeHtml(cleanText(s))}</li>`).join("")}</ul>
          </div>` : ""}
          ${fusion ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Internal bank context</p>
            <p class="intel-narrative">${escapeHtml(fusion.fusion_rationale)}</p>
          </div>` : ""}
        </div>
      </details>
    `;

    // ── Accordion 3: What should I do? ──────────────────────────────────────
    const kycQuestions = (publicKyc?.open_kyc_questions || []).slice(0, 4);
    const founderIntel = founderInvestorForCustomer(alert.customer_id);
    const capQuestions = (founderIntel?.summary?.top_rm_questions || []).slice(0, 3);
    const allGaps      = [...kycQuestions, ...capQuestions].filter(Boolean);

    const acc3 = `
      <details class="intel-accordion">
        <summary class="intel-accordion-summary">
          <span class="intel-accordion-num">3</span>
          <span class="intel-accordion-title">What should I do?</span>
          <span class="intel-accordion-chevron" aria-hidden="true"></span>
        </summary>
        <div class="intel-accordion-body">
          <div class="intel-subsection">
            <p class="intel-subsection-label">Recommended action</p>
            <p class="intel-narrative">${escapeHtml(cleanText(alert.recommended_action))}</p>
          </div>
          ${allGaps.length ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Missing information &amp; open questions</p>
            <ul class="intel-list intel-list-gaps">
              ${allGaps.map(q => `<li>${escapeHtml(cleanText(q))}</li>`).join("")}
            </ul>
          </div>` : ""}
          <div class="intel-subsection">
            <p class="intel-subsection-label">RM action</p>
            <div class="action-stack">
              <textarea id="actionNote" placeholder="Optional note for audit trail \u2014 will appear in action history"></textarea>
              <div class="action-buttons">
                <button class="secondary-button" type="button" data-action="acknowledged">Acknowledge</button>
                <button class="primary-button" type="button" data-action="escalated">Escalate</button>
                <button class="secondary-button" type="button" data-action="customer_update_requested">Request update</button>
                <button class="secondary-button" type="button" data-action="added_to_call_brief">Add to brief</button>
                <button class="danger-button" type="button" data-action="dismissed">Dismiss</button>
              </div>
            </div>
          </div>
          <div class="intel-subsection">
            <p class="intel-subsection-label">Action history</p>
            ${actionLogTemplate(alert)}
          </div>
        </div>
      </details>
    `;

    // ── Accordion 4: What supports this finding? ────────────────────────────
    const reviews      = aiReviewsForAlert(alert);
    const reviewModels = [...new Set(reviews.map(r => r.model).filter(Boolean))];
    const quote        = alert.evidence_quote || primaryEvidenceQuote(alert);
    const method       = alert.detection_method || "rule_fallback";

    const acc4 = `
      <details class="intel-accordion">
        <summary class="intel-accordion-summary">
          <span class="intel-accordion-num">4</span>
          <span class="intel-accordion-title">What supports this finding?</span>
          <span class="intel-accordion-chevron" aria-hidden="true"></span>
        </summary>
        <div class="intel-accordion-body">
          <div class="intel-provenance-row">
            <span class="intel-provenance-item">Signal extracted by <strong>${escapeHtml(detectionLabel(method))}</strong></span>
            ${reviews.length
              ? `<span class="intel-provenance-item intel-provenance-ai">Document reviewed by Apertus AI${reviewModels.length ? ` (${escapeHtml(reviewModels.join(", "))})` : ""}</span>`
              : `<span class="intel-provenance-item intel-provenance-muted">Document not AI-reviewed</span>`}
            ${alert.needs_human_review ? `<span class="intel-provenance-item intel-provenance-warn">Human review required</span>` : ""}
            ${alert.ai_severity_suggestion ? `<span class="intel-provenance-item">Apertus severity: <strong>${escapeHtml(labelize(alert.ai_severity_suggestion))}</strong></span>` : ""}
          </div>
          ${quote ? `
          <div class="intel-subsection">
            <p class="intel-subsection-label">Key evidence quote</p>
            <blockquote class="intel-quote">${escapeHtml(quote)}</blockquote>
          </div>` : ""}
          <div class="intel-subsection">
            <p class="intel-subsection-label">Supporting documents (${(alert.evidence || []).length})</p>
            ${evidenceTemplate(alert)}
          </div>
          <div class="intel-subsection">
            <p class="intel-subsection-label">Audit IDs</p>
            <div class="fact-id-row">
              ${alert.fact_ids.map(id => `<span class="pill">${escapeHtml(id)}</span>`).join("")}
              ${alert.evidence_document_ids.map(id => `<span class="pill">${escapeHtml(id)}</span>`).join("")}
            </div>
          </div>
        </div>
      </details>
    `;

    // ── Accordion 5: What else should I know? ───────────────────────────────
    const acc5 = `
      <details class="intel-accordion">
        <summary class="intel-accordion-summary">
          <span class="intel-accordion-num">5</span>
          <span class="intel-accordion-title">What else should I know?</span>
          <span class="intel-accordion-chevron" aria-hidden="true"></span>
        </summary>
        <div class="intel-accordion-body">
          ${publicKycTemplate(alert)}
          ${layer2ProfileTemplate(alert)}
          ${founderInvestorTemplate(alert)}
          ${internalContextTemplate(alert)}
          <div class="intel-subsection">
            <p class="intel-subsection-label">Source links</p>
            <div class="detail-source-strip">${sourceLinksTemplate(alert)}</div>
          </div>
        </div>
      </details>
    `;

    els.alertDetail.innerHTML = `
      <div class="intel-accordion-stack">
        ${acc1}${acc2}${acc3}${acc4}${acc5}
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

  function publicKycTemplate(alert) {
    const profile = publicKycForCustomer(alert.customer_id);
    if (!profile) return "";

    const identity = profile.identity || {};
    const coverage = profile.source_coverage || {};
    const completeness = profile.completeness || {};
    return `
      <div class="materiality-box public-kyc-box">
        <div class="materiality-head">
          <strong>Public-source KYC</strong>
          <span class="pill ${kycRiskPillClass(profile.public_kyc_risk_rating)}">Risk ${escapeHtml(labelize(profile.public_kyc_risk_rating || "unknown"))}</span>
          <span class="pill">${escapeHtml(coverage.source_count || 0)} source(s)</span>
          <span class="pill">Coverage ${escapeHtml(Math.round((completeness.score || 0) * 100))}%</span>
          <span class="pill">${escapeHtml(labelize(profile.kyc_status || "review"))}</span>
        </div>
        <div class="public-kyc-grid">
          <div>
            <span class="field-label">Identity</span>
            <ul class="value-list">
              <li><strong>Legal:</strong> ${escapeHtml(identity.legal_name || profile.legal_name || "unknown")}</li>
              <li><strong>Type:</strong> ${escapeHtml(labelize(identity.entity_type || "unknown"))}</li>
              <li><strong>Listing:</strong> ${escapeHtml(identity.public_listing || "private / not listed")}</li>
              <li><strong>Domicile:</strong> ${escapeHtml(identity.primary_domicile || "unknown")}</li>
              ${identity.headquarters ? `<li><strong>HQ:</strong> ${escapeHtml(identity.headquarters)}</li>` : ""}
            </ul>
          </div>
          <div>
            <span class="field-label">Products and regions</span>
            <div class="alert-tags kyc-tags">
              ${(profile.products_services || []).slice(0, 8).map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join("")}
              ${(identity.operating_regions || []).slice(0, 6).map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join("")}
            </div>
          </div>
        </div>
        ${kycListTemplate("Risk rationale", profile.risk_rationale)}
        ${kycListTemplate("Regulatory / sanctions context", [...(profile.regulatory_and_licensing || []).slice(0, 4), ...(profile.sanctions_adverse_media || []).slice(0, 3)])}
        ${kycListTemplate("RM KYC questions", profile.open_kyc_questions)}
        ${publicKycSourceLinksTemplate(profile)}
        <p class="layer2-demo-note">${escapeHtml(profile.important_notice || "")}</p>
      </div>
    `;
  }

  function kycListTemplate(title, items) {
    const visible = (items || []).filter(Boolean).slice(0, 5);
    if (!visible.length) return "";
    return `
      <div class="public-kyc-list">
        <strong>${escapeHtml(title)}</strong>
        <ul>
          ${visible.map((item) => `<li>${escapeHtml(cleanText(item))}</li>`).join("")}
        </ul>
      </div>
    `;
  }

  function publicKycSourceLinksTemplate(profile) {
    const sources = (profile.source_notes || []).filter((source) => source.source_url).slice(0, 6);
    if (!sources.length) return "";
    return `
      <div class="detail-source-strip layer2-source-strip">
        ${sources.map((source) => `
          <a class="source-link" href="${escapeAttr(source.source_url)}" target="_blank" rel="noreferrer">
            <span>Open source</span>
            <strong>${escapeHtml(source.source_name)}</strong>
            <small>${escapeHtml(source.source_type || "")}${source.source_quality ? ` | Quality ${escapeHtml(source.source_quality)}` : ""}</small>
          </a>
        `).join("")}
      </div>
    `;
  }

  function founderInvestorTemplate(alert) {
    const intel = founderInvestorForCustomer(alert.customer_id);
    const records = sortInvestorRecords(intel?.records || []).slice(0, 5);
    if (!intel || !records.length) return "";

    const summary = intel.summary || {};
    const verifyCount = records.filter((record) => record.needs_verification).length;
    return `
      <div class="materiality-box founder-investor-box">
        <div class="materiality-head">
          <strong>Founder & investor intelligence</strong>
          <span class="pill ownership_control">${escapeHtml(summary.equity_or_control_record_count || 0)} equity/control</span>
          <span class="pill">${escapeHtml(summary.ownership_percent_unknown_count || 0)} stake(s) unknown</span>
          ${verifyCount ? `<span class="pill material">${escapeHtml(verifyCount)} verify</span>` : ""}
        </div>
        <div class="investor-record-list">
          ${records.map((record) => investorRecordTemplate(record)).join("")}
        </div>
        ${investorQuestionsTemplate(summary.top_rm_questions || [])}
      </div>
    `;
  }

  function investorRecordTemplate(record) {
    const stake = record.ownership_percent || "stake not disclosed";
    const amount = record.amount ? `<span class="pill">${escapeHtml(record.amount)}</span>` : "";
    const valuation = record.valuation ? `<span class="pill">${escapeHtml(record.valuation)}</span>` : "";
    const sourceLink = record.source_url
      ? `<a class="source-link" href="${escapeAttr(record.source_url)}" target="_blank" rel="noreferrer">
          <span>Open source</span>
          <strong>${escapeHtml(record.source_name || "Source")}</strong>
          <small>${escapeHtml(record.source_quality ? `Quality ${record.source_quality}` : "")}</small>
        </a>`
      : `<span class="source-link-muted">${escapeHtml(record.source_name || "No public source")}</span>`;

    return `
      <article class="investor-record">
        <div class="investor-record-head">
          <strong>${escapeHtml(record.entity_name || "Unknown party")}</strong>
          <span class="pill ${record.rm_impact === "mixed" ? "mixed" : record.rm_impact === "positive" ? "opportunity" : ""}">
            ${escapeHtml(labelize(record.rm_impact || "unknown"))}
          </span>
        </div>
        <div class="alert-tags">
          <span class="pill">${escapeHtml(labelize(record.role_type || "investor"))}</span>
          <span class="pill ownership_control">${escapeHtml(labelize(record.advisory_vs_equity || "unknown"))}</span>
          <span class="pill">${escapeHtml(stake)}</span>
          ${amount}
          ${valuation}
          ${record.needs_verification ? `<span class="pill material">Verification needed</span>` : ""}
        </div>
        ${record.rm_impact_reason ? `<p class="summary">${escapeHtml(cleanText(record.rm_impact_reason))}</p>` : ""}
        ${record.ownership_basis ? `<p class="summary"><strong>Ownership basis:</strong> ${escapeHtml(cleanText(record.ownership_basis))}</p>` : ""}
        ${record.recommended_action ? `<p class="summary"><strong>RM action:</strong> ${escapeHtml(cleanText(record.recommended_action))}</p>` : ""}
        ${record.evidence_quote ? `<p class="evidence-excerpt"><strong>Evidence:</strong> ${escapeHtml(cleanText(record.evidence_quote))}</p>` : ""}
        <div class="detail-source-strip">${sourceLink}</div>
      </article>
    `;
  }

  function investorQuestionsTemplate(questions) {
    if (!questions.length) return "";
    return `
      <div class="investor-questions">
        <strong>Cap table questions</strong>
        <ul>
          ${questions.slice(0, 4).map((question) => `<li>${escapeHtml(question)}</li>`).join("")}
        </ul>
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
    const founderInvestorRecords = sortInvestorRecords(founderInvestorForCustomer(customer.customer_id)?.records || []).slice(0, 5);
    const publicKyc = publicKycForCustomer(customer.customer_id);

    return {
      customer,
      materialChanges,
      riskQuestions,
      opportunities,
      suggestedQuestions,
      evidenceReferences,
      founderInvestorRecords,
      publicKycQuestions: publicKyc?.open_kyc_questions || [],
      publicKycSources: publicKyc?.source_notes || []
    };
  }

  function getBriefIcon(title) {
    if (title.includes("Material changes")) {
      // Warning triangle
      return `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
    }
    if (title.includes("risk questions")) {
      // Shield
      return `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`;
    }
    if (title.includes("opportunities")) {
      // Lightbulb
      return `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="11" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    }
    if (title.includes("questions")) {
      // Message bubble
      return `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>`;
    }
    if (title.includes("intelligence")) {
      // Users
      return `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`;
    }
    // Default file / evidence
    return `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>`;
  }

  function briefHtmlTemplate(brief) {
    return `
      ${briefSectionTemplate("Material changes", brief.materialChanges, alertBriefItem, true)}
      ${briefSectionTemplate("Open risk questions", brief.riskQuestions, alertBriefItem, false)}
      ${briefSectionTemplate("Commercial opportunities", brief.opportunities, alertBriefItem, false)}
      ${briefSectionTemplate("Suggested customer questions", brief.suggestedQuestions, questionBriefItem, false)}
      ${briefSectionTemplate("Public KYC questions", brief.publicKycQuestions, questionBriefItem, false)}
      ${briefSectionTemplate("Founder/investor intelligence", brief.founderInvestorRecords, investorBriefItem, false)}
      ${briefSectionTemplate("Evidence references", brief.evidenceReferences, evidenceBriefItem, false)}
    `;
  }

  function briefSectionTemplate(title, items, renderer, isOpen) {
    const openAttr = isOpen ? "open" : "";
    const icon = getBriefIcon(title);
    
    if (!items.length) {
      return `
        <details class="brief-accordion" ${openAttr}>
          <summary class="brief-accordion-summary">
            <span class="brief-accordion-icon">${icon}</span>
            <span class="brief-accordion-title">${escapeHtml(title)}</span>
            <span class="brief-accordion-chevron"></span>
          </summary>
          <div class="brief-accordion-body">
            <div class="empty-state">No current items.</div>
          </div>
        </details>
      `;
    }
    return `
      <details class="brief-accordion" ${openAttr}>
        <summary class="brief-accordion-summary">
          <span class="brief-accordion-icon">${icon}</span>
          <span class="brief-accordion-title">${escapeHtml(title)}</span>
          <span class="brief-accordion-chevron"></span>
        </summary>
        <div class="brief-accordion-body">
          <ul class="brief-list">
            ${items.map(renderer).join("")}
          </ul>
        </div>
      </details>
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

  function investorBriefItem(record) {
    const stake = record.ownership_percent || "stake not disclosed";
    return `
      <li class="brief-item">
        <strong>${escapeHtml(cleanText(record.entity_name || "Unknown party"))}</strong>
        <p>${escapeHtml(labelize(record.role_type || "investor"))} | ${escapeHtml(labelize(record.advisory_vs_equity || "unknown"))} | ${escapeHtml(stake)}</p>
        <p>${escapeHtml(cleanText(record.recommended_action || record.rm_impact_reason || ""))}</p>
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
    appendTextSection(lines, "Public KYC questions", brief.publicKycQuestions);
    appendTextSection(
      lines,
      "Founder/investor intelligence",
      brief.founderInvestorRecords.map((record) => {
        const stake = record.ownership_percent || "stake not disclosed";
        return `${record.entity_name} | ${labelize(record.role_type || "investor")} | ${labelize(record.advisory_vs_equity || "unknown")} | ${stake} | ${record.recommended_action}`;
      })
    );
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
    state.selectedCustomerId = alert.customer_id;
    state.selectedAlertId = alert.alert_id;
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


  function renderGeographicFootprint() {
    const customer = selectedCustomer();
    if (!customer) {
      els.geoFootprintTitle.textContent = "Customer geographic footprint";
      els.geoMap.innerHTML = `<div class="empty-state">No customer selected.</div>`;
      els.geoCountryChips.innerHTML = "";
      els.geoCountryCard.hidden = true;
      return;
    }

    const countries = geographicFootprintForCustomer(customer.customer_id);
    const selected = countries.find((item) => item.country === state.selectedGeoCountry);
    if (state.selectedGeoCountry && !selected) {
      state.selectedGeoCountry = null;
    }

    els.geoFootprintTitle.textContent = `${customer.legal_name} geographic footprint`;
    renderAmChartsGeographicMap(countries);
    els.geoCountryChips.innerHTML = countries.length
      ? countries.map(geoChipTemplate).join("")
      : `<span class="source-link-muted">No mapped countries available.</span>`;

    if (selected) {
      els.geoCountryCard.hidden = false;
      els.geoCountryCard.innerHTML = geoCountryCardTemplate(selected);
    } else {
      els.geoCountryCard.hidden = true;
      els.geoCountryCard.innerHTML = "";
    }
  }

  function geographicFootprintForCustomer(customerId) {
    const customer = state.customersById.get(customerId) || {};
    const publicKyc = publicKycForCustomer(customerId) || {};
    const identity = publicKyc.identity || {};
    const domicile = normalizeCountry(identity.primary_domicile || customer.domicile);
    const known = new Set();
    const risk = new Set();

    [
      ...(identity.operating_regions || []),
      ...(customer.known_jurisdictions || [])
    ].forEach((value) => addCountrySet(known, value));

    const profileText = [
      ...(publicKyc.sanctions_adverse_media || []),
      ...(publicKyc.regulatory_and_licensing || []),
      ...(publicKyc.risk_rationale || []),
      ...(publicKyc.open_kyc_questions || [])
    ].join(" ").toLowerCase();
    Object.keys(GEO_COUNTRIES).forEach((country) => {
      const lower = country.toLowerCase();
      if (!profileText.includes(lower)) return;
      if (/(sanction|blocked|restriction|restricted|dprk|north korea|russia|illicit|prohibited|exit|aml|cft|license loss)/i.test(profileText)) {
        risk.add(country);
      } else {
        known.add(country);
      }
    });

    state.alerts
      .filter((alert) => alert.customer_id === customerId)
      .forEach((alert) => {
        const text = [alert.title, alert.summary, alert.recommended_action, ...(alert.material_reasons || [])].join(" ").toLowerCase();
        Object.keys(GEO_COUNTRIES).forEach((country) => {
          if (!text.includes(country.toLowerCase())) return;
          if (/(sanction|blocked|restriction|restricted|illegal|investigation|critical|risk|prohibited|aml|north korea|russia)/i.test(text)) {
            risk.add(country);
          } else {
            known.add(country);
          }
        });
      });

    if (domicile) {
      known.add(domicile);
    }

    const countries = Array.from(new Set([...known, ...risk]))
      .filter((country) => GEO_COUNTRIES[country])
      .map((country) => {
        const type = risk.has(country) ? "risk" : country === domicile ? "domicile" : "known";
        return {
          country,
          type,
          id: GEO_COUNTRIES[country].id || null,
          allianceType: GEO_COUNTRIES[country].allianceType || null,
          memberIds: GEO_COUNTRIES[country].memberIds || [],
          regulator: GEO_COUNTRIES[country].regulator,
          url: GEO_COUNTRIES[country].url,
          lat: GEO_COUNTRIES[country].lat,
          lon: GEO_COUNTRIES[country].lon,
          note: geoCountryNote(country, type, customer, publicKyc)
        };
      })
      .sort((a, b) => geoTypeRank(a.type) - geoTypeRank(b.type) || a.country.localeCompare(b.country));

    return countries;
  }

  function renderAmChartsGeographicMap(countries) {
    if (!countries.length) {
      disposeGeoChart();
      els.geoMap.innerHTML = `<div class="empty-state">No mapped countries available.</div>`;
      return;
    }

    if (!window.am5 || !window.am5map || !window.am5geodata_worldLow) {
      disposeGeoChart();
      els.geoMap.innerHTML = `
        ${worldMapTemplate()}
        ${countries.map(geoMarkerTemplate).join("")}
      `;
      return;
    }

    try {
      const chartParts = ensureGeoChart();
      chartParts.countryNames = new Set(countries.map((item) => item.country));
      chartParts.polygonSeries.data.setAll(geoPolygonData(countries));
      chartParts.pointSeries.data.setAll(countries.map((item) => ({
        ...item,
        geometry: {
          type: "Point",
          coordinates: [item.lon, item.lat]
        }
      })));
    } catch (error) {
      console.error("Could not render amCharts geographic map", error);
      disposeGeoChart();
      els.geoMap.innerHTML = `
        ${worldMapTemplate()}
        ${countries.map(geoMarkerTemplate).join("")}
      `;
    }
  }

  function ensureGeoChart() {
    if (geoChart) return geoChart;

    els.geoMap.innerHTML = "";

    const root = am5.Root.new("geoMap");
    if (window.am5themes_Animated) {
      root.setThemes([am5themes_Animated.new(root)]);
    }

    const chart = root.container.children.push(am5map.MapChart.new(root, {
      panX: "translateX",
      panY: "translateY",
      projection: am5map.geoMercator(),
      wheelY: "zoom",
      pinchZoom: true,
      maxZoomLevel: 8
    }));

    chart.set("zoomControl", am5map.ZoomControl.new(root, {
      x: am5.p100,
      centerX: am5.p100,
      y: am5.p100,
      centerY: am5.p100
    }));

    const polygonSeries = chart.series.push(am5map.MapPolygonSeries.new(root, {
      geoJSON: am5geodata_worldLow,
      exclude: ["AQ"]
    }));

    polygonSeries.mapPolygons.template.setAll({
      fill: am5.color(0xd4dee3),
      stroke: am5.color(0xc1ced4),
      strokeWidth: 0.7,
      tooltipText: "{name}",
      interactive: true,
      templateField: "polygonSettings"
    });

    polygonSeries.mapPolygons.template.states.create("hover", {
      fill: am5.color(0xc6d4da)
    });

    polygonSeries.mapPolygons.template.events.on("click", (event) => {
      const context = event.target.dataItem?.dataContext || {};
      const country = context.geoCountry || normalizeCountry(context.name);
      if (!country || !geoChart?.countryNames?.has(country)) return;
      state.selectedGeoCountry = country;
      renderGeographicFootprint();
    });

    const pointSeries = chart.series.push(am5map.MapPointSeries.new(root, {}));
    pointSeries.bullets.push((bulletRoot, _series, dataItem) => {
      const item = dataItem.dataContext;
      const active = item.country === state.selectedGeoCountry;
      const color = am5.color(geoColorValue(item.type));
      const container = am5.Container.new(bulletRoot, {
        cursorOverStyle: "pointer",
        tooltipText: `${item.country}\n${geoTypeLabel(item.type)}`
      });

      container.children.push(am5.Circle.new(bulletRoot, {
        radius: active ? 15 : 12,
        fill: color,
        fillOpacity: 0.18,
        strokeOpacity: 0
      }));

      container.children.push(am5.Circle.new(bulletRoot, {
        radius: active ? 7 : 5,
        fill: color,
        stroke: am5.color(0xffffff),
        strokeWidth: 2
      }));

      container.events.on("click", () => {
        state.selectedGeoCountry = item.country;
        renderGeographicFootprint();
      });

      return am5.Bullet.new(bulletRoot, {
        sprite: container
      });
    });

    geoChart = {
      root,
      chart,
      polygonSeries,
      pointSeries,
      countryNames: new Set()
    };
    return geoChart;
  }

  function disposeGeoChart() {
    if (geoChart?.root) {
      geoChart.root.dispose();
    }
    geoChart = null;
  }

  function geoPolygonData(countries) {
    const polygonsById = new Map();

    countries.forEach((item) => {
      addGeoPolygon(polygonsById, item, item.id, false);
      (item.memberIds || []).forEach((memberId) => {
        addGeoPolygon(polygonsById, item, memberId, true);
      });
    });

    return Array.from(polygonsById.values()).map((entry) => geoPolygonEntry(entry));
  }

  function addGeoPolygon(polygonsById, item, id, isAllianceMember) {
    if (!id) return;
    const entry = { item, id, isAllianceMember };
    const current = polygonsById.get(id);
    if (!current || geoPolygonPriority(entry) > geoPolygonPriority(current)) {
      polygonsById.set(id, entry);
    }
  }

  function geoPolygonEntry(entry) {
    const { item, id, isAllianceMember } = entry;
    const active = item.country === state.selectedGeoCountry;
    const tooltipLabel = isAllianceMember
      ? `${item.country}\n${geoTypeLabel(item.type)} alliance member`
      : `${item.country}\n${geoTypeLabel(item.type)}`;

    return {
      id,
      name: isAllianceMember ? `${item.country} member country` : item.country,
      geoCountry: item.country,
      geoType: item.type,
      geoLabel: geoTypeLabel(item.type),
      allianceMember: isAllianceMember,
      polygonSettings: {
        fill: am5.color(active ? geoColorValue(item.type) : geoFillValue(item.type)),
        stroke: am5.color(geoColorValue(item.type)),
        strokeWidth: active ? 1.8 : 0.9,
        tooltipText: tooltipLabel
      }
    };
  }

  function geoPolygonPriority(entry) {
    const typeWeight = { risk: 100, domicile: 80, known: 60 }[entry.item.type] || 0;
    const selectedWeight = entry.item.country === state.selectedGeoCountry ? 20 : 0;
    const directCountryWeight = entry.isAllianceMember ? 0 : 10;
    return typeWeight + selectedWeight + directCountryWeight;
  }

  function addCountrySet(target, value) {
    const country = normalizeCountry(value);
    if (country && GEO_COUNTRIES[country]) {
      target.add(country);
    }
  }

  function normalizeCountry(value) {
    const text = cleanText(value || "");
    if (!text) return null;
    const replacements = {
      "Australia review": "Australia",
      "Europe": "European Union",
      "European Union": "European Union",
      "EU": "European Union",
      "United States of America": "United States",
      "USA": "United States",
      "US": "United States",
      "UK": "United Kingdom",
      "DPRK": "North Korea",
      "North Korea": "North Korea",
      "Russia-linked exchange activity": "Russia",
      "global blockchain networks": null,
      "global technology markets": null,
      "global tobacco markets": null,
      "international online users": null
    };
    return Object.prototype.hasOwnProperty.call(replacements, text) ? replacements[text] : text;
  }

  function geoTypeRank(type) {
    return { domicile: 1, known: 2, risk: 3 }[type] || 4;
  }

  function geoColorValue(type) {
    if (type === "risk") return 0xa82218;
    if (type === "known") return 0x4fd37a;
    return 0x0f766e;
  }

  function geoFillValue(type) {
    if (type === "risk") return 0xf7d6d2;
    if (type === "known") return 0xd7f6df;
    return 0xb9dfdd;
  }

  function geoCountryNote(country, type, customer, publicKyc) {
    if (GEO_COUNTRIES[country]?.memberIds?.length) {
      return "Regional or alliance-level footprint. Member countries are highlighted on the map and link to the regional regulatory source.";
    }
    if (type === "domicile") return "Primary domicile from public KYC or baseline profile.";
    if (type === "risk") return "Risk or sanctioned-country context found in KYC, sanctions, or alert evidence.";
    const regions = publicKyc.identity?.operating_regions || customer.known_jurisdictions || [];
    return regions.includes(country) ? "Known operating jurisdiction from public KYC." : "Known jurisdiction from baseline or alert evidence.";
  }

  function lonToX(lon) {
    return ((lon + 180) / 360) * 100;
  }

  function latToY(lat) {
    return ((90 - lat) / 180) * 100;
  }

  function geoMarkerTemplate(item) {
    return `
      <button
        class="geo-marker ${escapeAttr(item.type)} ${item.country === state.selectedGeoCountry ? "active" : ""}"
        type="button"
        data-geo-country="${escapeAttr(item.country)}"
        style="left: ${lonToX(item.lon)}%; top: ${latToY(item.lat)}%;"
        aria-label="${escapeAttr(`${item.country}: ${geoTypeLabel(item.type)}`)}"
      >
        <span></span>
      </button>
    `;
  }

  function geoChipTemplate(item) {
    return `
      <button class="geo-chip ${escapeAttr(item.type)} ${item.memberIds?.length ? "alliance" : ""} ${item.country === state.selectedGeoCountry ? "active" : ""}" type="button" data-geo-country="${escapeAttr(item.country)}">
        <span></span>
        ${escapeHtml(item.country)}
        <em>${escapeHtml(item.memberIds?.length ? `${geoTypeLabel(item.type)} alliance` : geoTypeLabel(item.type))}</em>
      </button>
    `;
  }

  function geoCountryCardTemplate(item) {
    return `
      <div class="geo-card-head">
        <strong>${escapeHtml(item.country)}</strong>
        <span class="pill ${item.type === "risk" ? "risk" : item.type === "known" ? "opportunity" : "mixed"}">${escapeHtml(geoTypeLabel(item.type))}</span>
      </div>
      <p>${escapeHtml(item.note)}</p>
      ${item.memberIds?.length ? `<p class="geo-member-note">${escapeHtml(item.memberIds.length)} member countries highlighted.</p>` : ""}
      <a class="source-link" href="${escapeAttr(item.url)}" target="_blank" rel="noreferrer">
        <span>Open site</span>
        <strong>${escapeHtml(item.regulator)}</strong>
        <small>Official regulation / supervision source</small>
      </a>
    `;
  }

  function geoTypeLabel(type) {
    if (type === "domicile") return "domicile";
    if (type === "risk") return "risk / sanctioned";
    return "known jurisdiction";
  }

  function worldMapTemplate() {
    return `
      <svg class="geo-world" viewBox="0 0 1000 460" role="img" aria-label="World map background">
        <path d="M95 142 C130 95 214 82 281 112 C328 133 338 178 307 208 C267 245 215 228 178 258 C138 290 91 248 77 207 C68 181 72 159 95 142 Z" />
        <path d="M279 248 C323 270 338 323 314 365 C298 394 285 421 255 428 C235 407 230 372 217 339 C202 302 231 263 279 248 Z" />
        <path d="M444 133 C482 111 533 116 559 147 C533 176 486 172 451 166 C423 160 420 145 444 133 Z" />
        <path d="M488 187 C537 170 594 196 611 247 C630 305 590 372 531 382 C488 355 466 291 472 237 C474 217 479 201 488 187 Z" />
        <path d="M584 136 C664 79 802 100 890 169 C918 191 926 238 893 264 C841 306 768 262 710 278 C662 291 612 251 590 204 C579 181 568 153 584 136 Z" />
        <path d="M779 326 C820 305 877 322 899 354 C879 388 817 391 779 373 C755 361 755 339 779 326 Z" />
        <path d="M472 103 C504 87 547 91 574 113 C542 125 502 126 472 103 Z" />
      </svg>
    `;
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

  function founderInvestorForCustomer(customerId) {
    return state.founderInvestorByCustomer.get(customerId) || null;
  }

  function publicKycForCustomer(customerId) {
    return state.publicKycByCustomer.get(customerId) || null;
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

  function sortInvestorRecords(records) {
    const roleRank = {
      equity_control: 6,
      equity: 5,
      voting_control: 5,
      financing: 4,
      management: 3,
      not_equity: 2,
      unknown: 1
    };
    const impactRank = { mixed: 4, positive: 3, unknown: 2, neutral: 1 };
    return [...records].sort((a, b) => {
      return (roleRank[b.advisory_vs_equity] || 0) - (roleRank[a.advisory_vs_equity] || 0)
        || (impactRank[b.rm_impact] || 0) - (impactRank[a.rm_impact] || 0)
        || Number(Boolean(b.ownership_percent)) - Number(Boolean(a.ownership_percent))
        || (b.confidence || 0) - (a.confidence || 0)
        || (a.entity_name || "").localeCompare(b.entity_name || "");
    });
  }

  function kycRiskPillClass(rating) {
    const value = String(rating || "").toLowerCase();
    if (value.includes("critical") || value.includes("high")) return "risk";
    if (value.includes("medium")) return "mixed";
    if (value.includes("low")) return "opportunity";
    return "";
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
