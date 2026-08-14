"use strict";

const OBSERVATIONS = [
  "resolved",
  "off_center",
  "close_to_host_light",
  "too_faint_to_judge",
  "blend_or_nearby_source",
  "image_artifact",
  "star_forming_or_young_cluster_appearance",
];
const FOUR_STATE = ["not_reviewed", "yes", "no", "uncertain"];
const IMAGE_USABILITY = ["not_reviewed", "usable", "partly_usable", "unusable"];
const CONFIRMED_DECISIONS = ["not_reviewed", "include", "exclude", "hold"];
const CANDIDATE_DECISIONS = ["not_reviewed", "prioritize", "standard", "deprioritize", "hold"];
// Coordinate-proposal responses are derived from the Gaia / Legacy / manual selections.

const OBSERVATION_LABELS = {
  resolved: "Resolved",
  off_center: "Off-center",
  close_to_host_light: "Close to host light",
  too_faint_to_judge: "Too faint to judge",
  blend_or_nearby_source: "Blend or nearby source",
  image_artifact: "Image artifact",
  star_forming_or_young_cluster_appearance: "Star-forming / young-cluster appearance",
};

const PIXEL_SCALE_ARCSEC = 0.262;

let state = {
  page: 1,
  cohort: "",
  reviewStatus: "",
  decision: "",
  query: "",
  items: [],
  currentIndex: -1,
  currentObject: null,
  review: null,
  dirty: false,
  scale: "compact",
  showMarkers: false,
};

const $ = (sel) => document.querySelector(sel);

function emptyReview() {
  return {
    client_revision: 0,
    image_usability: "not_reviewed",
    observations: Object.fromEntries(OBSERVATIONS.map((name) => [name, "not_reviewed"])),
    final_decision: "not_reviewed",
    evidence_note: "",
    general_comment: "",
    decision_reason: "",
    coordinate_proposal: { response: "no_correction_needed" },
  };
}

async function loadSummary() {
  const response = await fetch("/api/summary");
  const data = await response.json();
  $("#summary").textContent =
    `${data.total} total · ${data.confirmed} confirmed · ${data.candidates ?? data.candidate} candidates · ` +
    `${data.reviewed_confirmed} reviewed (${data.included_confirmed} included)`;
}

async function loadList() {
  const params = new URLSearchParams({ page: state.page, page_size: 60 });
  if (state.cohort) params.set("cohort", state.cohort);
  if (state.reviewStatus) params.set("review_status", state.reviewStatus);
  if (state.decision) params.set("decision", state.decision);
  if (state.query) params.set("q", state.query);
  const response = await fetch(`/api/objects?${params}`);
  const data = await response.json();
  state.items = data.items;
  const list = $("#object-list");
  list.innerHTML = "";
  for (const item of data.items) {
    const li = document.createElement("li");
    const cohortBadge =
      item.reference_cohort === "saifollahi_high_probability_candidate"
        ? '<span class="badge candidate">candidate</span>'
        : '<span class="badge confirmed">confirmed</span>';
    const excluded =
      item.design_reference_membership === "excluded_stripped_nucleus_or_luminous_gc"
        ? '<span class="badge excluded">excluded</span>'
        : "";
    const complete = item.complete ? '<span class="badge complete">done</span>' : "";
    li.innerHTML = `
      <div class="obj-name">${escapeHtml(item.original_names || item.canonical_object_id)}${cohortBadge}${excluded}${complete}</div>
      <div class="obj-meta">${escapeHtml(item.host_name || "no host")} · ${fmtDist(item.adopted_distance_mpc)}</div>`;
    li.addEventListener("click", () => selectObject(item.canonical_object_id));
    list.appendChild(li);
  }
  $("#page-info").textContent = `Page ${state.page} (${data.total} objects)`;
}

function selectObject(oid) {
  if (state.dirty && !confirm("Unsaved changes will be lost. Continue?")) return;
  state.currentIndex = state.items.findIndex((item) => item.canonical_object_id === oid);
  loadObject(oid);
}

async function loadObject(oid) {
  const response = await fetch(`/api/objects/${oid}`);
  state.currentObject = await response.json();
  state.review = state.currentObject.review || emptyReview();
  state.dirty = false;
  state.scale = "compact";
  state.showMarkers = false;
  state.proposal = emptyProposal();
  renderDetail();
}

function renderDetail() {
  const obj = state.currentObject;
  const panel = $("#detail-panel");
  const core = obj.object;
  const cohort = core.reference_cohort;
  panel.innerHTML = `
    <div class="object-header">
      <h2>${escapeHtml(core.original_names || core.canonical_object_id)}</h2>
      <div class="meta">
        ${core.canonical_object_id} · RA ${fmtCoord(core.adopted_ra)} Dec ${fmtCoord(core.adopted_dec)} ·
        ${cohort === "saifollahi_high_probability_candidate" ? "Saifollahi candidate" : "Confirmed UCD"}
        ${obj.discovery && obj.discovery.ads_url ? `<br>Discovery: <a href="${obj.discovery.ads_url}" target="_blank">${escapeHtml(obj.discovery.bibcode)}</a>${obj.discovery.title ? ` — ${escapeHtml(obj.discovery.title)}` : ""}` : ""}
      </div>
    </div>
    <div class="nav-row">
      <button id="prev-obj">‹ Previous</button>
      <button id="next-obj">Next ›</button>
      <span id="saved-state" class="saved-state"></span>
    </div>
    <div class="top-panels">
      <div class="panel half"><h3>Host</h3><div class="panel-body">${hostPanel(obj.host)}</div></div>
      <div class="panel half"><h3>Links</h3><div class="panel-body">${linksPanel(obj.links)}</div></div>
    </div>
    <div class="review-layout">
      <div class="left-column">
        <div class="image-panel">
          <div class="image-tabs">
            <button id="tab-compact" class="tab">Compact (16.8″)</button>
            <button id="tab-wide" class="tab">Wide (67.1″)</button>
          </div>
          <div class="image-stage" id="image-stage"></div>
          <div class="image-toolbar">
            <button id="zoom-in">+</button>
            <button id="zoom-out">−</button>
            <button id="zoom-reset">Reset</button>
            <button id="toggle-markers">Show matches</button>
            <span class="legend">
              <span class="legend-item"><i class="dot accepted"></i>accepted Gaia</span>
              <span class="legend-item"><i class="dot neighbor"></i>Gaia neighbor</span>
              <span class="legend-item"><i class="dot legacy"></i>Legacy</span>
            </span>
          </div>
        </div>
        <div class="panel collapsible"><h3>Gaia</h3><div class="panel-body">${gaiaPanel(obj.gaia)}</div></div>
        <div class="panel collapsible"><h3>Legacy Survey</h3><div class="panel-body">${legacyPanel(obj.legacy_survey)}</div></div>
        <div class="panel collapsible"><h3>External catalogs</h3><div class="panel-body">${externalPanel(obj.external_catalogs)}</div></div>
      </div>
      <div class="review-controls">
        ${reviewPanel(cohort)}
      </div>
    </div>
  `;
  $("#prev-obj").addEventListener("click", () => step(-1));
  $("#next-obj").addEventListener("click", () => step(1));
  $("#tab-compact").addEventListener("click", () => setScale("compact"));
  $("#tab-wide").addEventListener("click", () => setScale("wide"));
  $("#zoom-in").addEventListener("click", () => zoom(1.3));
  $("#zoom-out").addEventListener("click", () => zoom(0.77));
  $("#zoom-reset").addEventListener("click", () => resetZoom());
  $("#toggle-markers").addEventListener("click", toggleMarkers);
  document.querySelectorAll(".collapsible > h3").forEach((header) => {
    header.addEventListener("click", () => header.parentElement.classList.toggle("collapsed"));
  });
  renderImage();
  renderReviewControls(cohort);
  $("#saved-state").textContent = state.review.revision_id
    ? `Saved revision #${state.review.revision_id}`
    : "Not yet reviewed";
}

function setScale(scale) {
  state.scale = scale;
  $("#tab-compact").classList.toggle("active", scale === "compact");
  $("#tab-wide").classList.toggle("active", scale === "wide");
  renderImage();
}

function sourcePixel(ra, dec) {
  const obj = state.currentObject;
  const size = state.scale === "compact" ? 64 : 256;
  const centerRa = Number(obj.object.adopted_ra);
  const centerDec = Number(obj.object.adopted_dec);
  const cx = (size - 1) / 2;
  const draArcsec = (ra - centerRa) * Math.cos((centerDec * Math.PI) / 180) * 3600;
  const ddecArcsec = (dec - centerDec) * 3600;
  const px = cx - draArcsec / PIXEL_SCALE_ARCSEC; // east = left
  const py = cx - ddecArcsec / PIXEL_SCALE_ARCSEC; // north = up
  if (px < 0 || px > size || py < 0 || py > size) return null;
  return { x: (px / size) * 100, y: (py / size) * 100 };
}

function computeMarkers() {
  const obj = state.currentObject;
  const markers = [];
  const push = (sources, type, label) => {
    for (const s of sources || []) {
      const ra = Number(s.ra);
      const dec = Number(s.dec);
      if (Number.isNaN(ra) || Number.isNaN(dec)) continue;
      const position = sourcePixel(ra, dec);
      if (!position) continue;
      markers.push({
        ...position,
        type,
        label: label || type,
        sourceId: s.source_id || s.ls_id || "",
        sepArcsec: s.dist_arcsec,
      });
    }
  };
  push(obj.gaia.accepted_sources, "accepted", "accepted");
  push(obj.gaia.positional_neighbors, "neighbor", "neighbor");
  push(obj.legacy_survey, "legacy", "legacy");
  return markers;
}

function renderImage() {
  const obj = state.currentObject;
  const scale = state.scale;
  const image = obj.images[scale] || {};
  const stage = $("#image-stage");
  const size = scale === "compact" ? 64 : 256;
  const markers = state.showMarkers ? computeMarkers() : [];
  const markerHtml = markers
    .map(
      (m) =>
        `<div class="marker ${m.type}" style="left:${m.x}%;top:${m.y}%" title="${escapeHtml(m.label)} ${escapeHtml(m.sourceId)} ${fmtNum(m.sepArcsec)}″"></div>`
    )
    .join("");
  const selectedHtml = [];
  if (state.proposal.gaia) {
    const position = sourcePixel(state.proposal.gaia.ra, state.proposal.gaia.dec);
    if (position) selectedHtml.push(`<div class="marker selected-gaia" style="left:${position.x}%;top:${position.y}%" title="selected Gaia: ${escapeHtml(state.proposal.gaia.source_id)}"><span class="marker-label">Gaia</span></div>`);
  }
  if (state.proposal.legacy) {
    const position = sourcePixel(state.proposal.legacy.ra, state.proposal.legacy.dec);
    if (position) selectedHtml.push(`<div class="marker selected-legacy" style="left:${position.x}%;top:${position.y}%" title="selected Legacy: ${escapeHtml(state.proposal.legacy.source_id)}"><span class="marker-label">Legacy</span></div>`);
  }
  const selectedHtmlStr = selectedHtml.join("");
  stage.innerHTML = `
    <div class="image-content" id="image-content">
      ${image.file_path ? `<img id="current-img" src="/api/images/${obj.canonical_object_id}/${scale}" alt="${scale}">` : `<div class="empty-state">no image</div>`}
      <div class="crosshair"></div>
      <div class="marker-layer">${markerHtml}${selectedHtmlStr}</div>
    </div>`;
  $("#tab-compact").classList.toggle("active", scale === "compact");
  $("#tab-wide").classList.toggle("active", scale === "wide");
  $("#toggle-markers").textContent = state.showMarkers ? "Hide matches" : "Show matches";
}

function zoom(factor) {
  const content = $("#image-content");
  if (!content) return;
  const current = parseFloat(content.dataset.scale || "1");
  const next = Math.min(8, Math.max(0.2, current * factor));
  content.dataset.scale = next;
  content.style.transform = `scale(${next})`;
}

function resetZoom() {
  const content = $("#image-content");
  if (!content) return;
  content.dataset.scale = 1;
  content.style.transform = "scale(1)";
}

function toggleMarkers() {
  state.showMarkers = !state.showMarkers;
  renderImage();
}

function hostPanel(host) {
  if (!host || !host.host_name) return '<div class="value-na">no host</div>';
  return `<span class="inline"><b>${escapeHtml(host.host_name)}</b> ·
    ${escapeHtml(host.host_association_state || "")} ·
    ${fmtDist(host.adopted_distance_mpc)} ·
    ${escapeHtml(host.design_reference_membership || "")}</span>`;
}

function gaiaPanel(gaia) {
  const accepted = gaia.accepted_sources || [];
  const neighbors = gaia.positional_neighbors || [];
  const membership = gaia.accepted_membership;
  const selectButton = (source) =>
    `<button class="select-source" data-source-type="gaia" data-source-id="${escapeHtml(source.source_id)}" data-ra="${source.ra}" data-dec="${source.dec}">use</button>`;
  let rows = "";
  for (const source of accepted) {
    rows += `<tr><td><b>accepted</b></td><td>${source.source_id}</td>
      <td>G=${fmtNum(source.phot_g_mean_mag)} AEN=${fmtNum(source.astrometric_excess_noise)}</td>
      <td>${selectButton(source)}</td></tr>`;
  }
  for (const source of neighbors) {
    rows += `<tr><td>neighbor</td><td>${source.source_id}</td>
      <td>${fmtNum(source.dist_arcsec)}″ · G=${fmtNum(source.phot_g_mean_mag)}</td>
      <td>${selectButton(source)}</td></tr>`;
  }
  const membershipText = membership
    ? `QSO:${membership.in_qso_candidates} galaxy:${membership.in_galaxy_candidates} NSS:${membership.non_single_star}`
    : "";
  return `<div>${escapeHtml(membershipText)}</div>
    <table class="evidence"><tr><th>Basis</th><th>Source</th><th>Measurements</th><th></th></tr>${rows || '<tr><td colspan="4" class="value-na">no Gaia sources</td></tr>'}</table>`;
}

function legacyPanel(legacy) {
  if (!legacy || !legacy.length) return '<div class="value-na">no Legacy Survey association (r &lt; 23)</div>';
  const rows = legacy.map((row) => {
    const ellipticity =
      row.shape_e1 != null && row.shape_e2 != null
        ? Math.sqrt(row.shape_e1 * row.shape_e1 + row.shape_e2 * row.shape_e2)
        : null;
    const shape =
      row.type === "PSF"
        ? `PSF FWHM ${fmtNum(row.psfsize_r)}″`
        : `r_e ${fmtNum(row.shape_r)}″${row.sersic != null ? ` n=${fmtNum(row.sersic)}` : ""} e=${fmtNum(ellipticity)}`;
    const select = `<button class="select-source" data-source-type="legacy" data-source-id="${escapeHtml(row.ls_id)}" data-ra="${row.ra}" data-dec="${row.dec}">use</button>`;
    return `<tr><td>${escapeHtml(row.type || "")}</td><td>${escapeHtml(row.ls_id || "")}</td>
      <td>${fmtNum(row.dist_arcsec)}″ · r=${fmtNum(row.mag_r)} · ${shape}</td>
      <td>${select}</td></tr>`;
  }).join("");
  return `<table class="evidence"><tr><th>Type</th><th>ls_id</th><th>dist · r · shape</th><th></th></tr>${rows}</table>`;
}

function externalPanel(external) {
  if (!external || !external.length) return '<div class="value-na">no external associations</div>';
  const rows = external.map((row) => `
    <tr><td>${escapeHtml(row.catalog_id)}</td><td>${escapeHtml(row.class_label || "")}</td>
    <td>${escapeHtml(row.match_basis)}</td><td>z=${fmtNum(row.redshift)}</td></tr>`).join("");
  return `<table class="evidence"><tr><th>Catalog</th><th>Class</th><th>Basis</th><th>Redshift</th></tr>${rows}</table>`;
}

function linksPanel(links) {
  if (!links) return '<div class="value-na">no links</div>';
  let html = `<a href="${links.legacy_viewer}" target="_blank">Legacy</a> · `;
  html += `<a href="${links.simbad}" target="_blank">SIMBAD</a> · `;
  html += `<a href="${links.ned}" target="_blank">NED</a>`;
  if (links.ads && links.ads.length) html += ` · <a href="${links.ads[0]}" target="_blank">ADS</a>`;
  return html;
}

function reviewPanel(cohort) {
  return `
    <div class="field-label">Image usability</div>
    <div class="segmented" id="seg-usability"></div>
    <div id="observations"></div>
    <div class="field-label">Final decision</div>
    <div class="segmented" id="seg-decision"></div>
    <div id="proposal-section" class="hidden">
      <div class="field-label">Coordinate correction</div>
      <div id="proposal-content"></div>
    </div>
    <div class="field-label">Evidence note</div>
    <input type="text" id="note-evidence" placeholder="factual description of the image">
    <div class="field-label">General comment (optional)</div>
    <input type="text" id="note-general" placeholder="optional">
    <div class="field-label">Decision reason</div>
    <input type="text" id="note-reason" placeholder="required for exclude / hold / deprioritize">
    <div class="review-actions">
      <button class="btn-save" id="btn-save">Save (Ctrl+S)</button>
      <button class="btn-save-next" id="btn-save-next">Save &amp; next</button>
    </div>
    <div class="saved-state" id="review-saved"></div>
    <div class="error-text" id="review-error"></div>`;
}

function renderReviewControls(cohort) {
  const seg = (id, values, selected) => {
    const el = $(`#${id}`);
    el.innerHTML = "";
    for (const value of values) {
      const btn = document.createElement("button");
      btn.textContent = value.replace(/_/g, " ");
      btn.dataset.value = value;
      if (value === selected) btn.classList.add("selected");
      btn.addEventListener("click", () => {
        el.querySelectorAll("button").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        markDirty();
      });
      el.appendChild(btn);
    }
  };

  seg("seg-usability", IMAGE_USABILITY, state.review.image_usability);
  const decisions = cohort === "saifollahi_high_probability_candidate" ? CANDIDATE_DECISIONS : CONFIRMED_DECISIONS;
  seg("seg-decision", decisions, state.review.final_decision);

  const obs = $("#observations");
  obs.innerHTML = "";
  for (const name of OBSERVATIONS) {
    const row = document.createElement("div");
    row.className = "obs-row";
    row.dataset.obsName = name;
    row.innerHTML = `<label>${OBSERVATION_LABELS[name]}</label>`;
    const group = document.createElement("div");
    group.className = "segmented";
    for (const value of FOUR_STATE) {
      const btn = document.createElement("button");
      btn.textContent = value === "not_reviewed" ? "—" : value;
      btn.dataset.value = value;
      if (value === state.review.observations[name]) btn.classList.add("selected");
      btn.addEventListener("click", () => {
        group.querySelectorAll("button").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        markDirty();
        if (name === "off_center") toggleProposal();
      });
      group.appendChild(btn);
    }
    row.appendChild(group);
    obs.appendChild(row);
  }
  toggleProposal();
  $("#note-evidence").value = state.review.evidence_note || "";
  $("#note-general").value = state.review.general_comment || "";
  $("#note-reason").value = state.review.decision_reason || "";

  $("#btn-save").addEventListener("click", () => save(false));
  $("#btn-save-next").addEventListener("click", () => save(true));
}

function emptyProposal() {
  return { response: "no_correction_needed", gaia: null, legacy: null, manual: null };
}

function deriveProposal(proposal) {
  const gaia = proposal.gaia;
  const legacy = proposal.legacy;
  const manual = proposal.manual;
  let coordinate_reference;
  let proposed_ra;
  let proposed_dec;
  if (gaia) {
    coordinate_reference = "gaia";
    proposed_ra = gaia.ra;
    proposed_dec = gaia.dec;
  } else if (legacy) {
    coordinate_reference = "legacy";
    proposed_ra = legacy.ra;
    proposed_dec = legacy.dec;
  } else if (manual && manual.ra != null && manual.dec != null) {
    coordinate_reference = "manual";
    proposed_ra = manual.ra;
    proposed_dec = manual.dec;
  } else {
    coordinate_reference = "none";
    proposed_ra = null;
    proposed_dec = null;
  }
  const reference_quality = gaia && legacy ? "both" : gaia ? "gaia_only" : legacy ? "legacy_only" : "none";
  return { coordinate_reference, proposed_ra, proposed_dec, reference_quality };
}

function updateProposalResponse() {
  const proposal = state.proposal;
  if (proposal.gaia || proposal.legacy) proposal.response = "source_selected";
  else if (proposal.manual && (proposal.manual.ra != null || proposal.manual.dec != null)) proposal.response = "manual_ra_dec";
  else proposal.response = "no_correction_proposed";
}

function toggleProposal() {
  const offCenter = observationValue("off_center");
  const show = offCenter === "yes" || offCenter === "uncertain";
  $("#proposal-section").classList.toggle("hidden", !show);
  if (show) renderProposalSection();
}

function renderProposalSection() {
  const content = $("#proposal-content");
  const proposal = state.proposal;
  const derived = deriveProposal(proposal);
  content.innerHTML = `
    <div class="prop-row">
      <span class="prop-label">Gaia (coordinate)</span>
      <span class="prop-value">${proposal.gaia ? escapeHtml(proposal.gaia.source_id) : 'not selected — click a Gaia "use" button'}</span>
      ${proposal.gaia ? '<button class="prop-clear" data-clear="gaia">clear</button>' : ""}
    </div>
    <div class="prop-row">
      <span class="prop-label">Legacy (photometry)</span>
      <span class="prop-value">${proposal.legacy ? escapeHtml(proposal.legacy.source_id) : 'not selected — click a Legacy "use" button'}</span>
      ${proposal.legacy ? '<button class="prop-clear" data-clear="legacy">clear</button>' : ""}
    </div>
    <div class="prop-row">
      <span class="prop-label">Manual RA/Dec</span>
      <span class="prop-value manual"><input id="prop-manual-ra" placeholder="RA (deg)" value="${proposal.manual?.ra ?? ""}"><input id="prop-manual-dec" placeholder="Dec (deg)" value="${proposal.manual?.dec ?? ""}"></span>
    </div>
    <div class="prop-derived">
      Coordinate: ${derived.coordinate_reference !== "none" ? `${fmtCoord(derived.proposed_ra)}, ${fmtCoord(derived.proposed_dec)} (from ${derived.coordinate_reference})` : "—"} ·
      Quality: <b>${derived.reference_quality.replace(/_/g, " ")}</b>
    </div>
    <button class="prop-clear" data-clear="all">no correction proposed</button>
  `;
  content.querySelectorAll("[data-clear]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const what = btn.dataset.clear;
      if (what === "gaia") state.proposal.gaia = null;
      else if (what === "legacy") state.proposal.legacy = null;
      else {
        state.proposal.gaia = null;
        state.proposal.legacy = null;
        state.proposal.manual = null;
      }
      updateProposalResponse();
      refreshSelectButtons();
      renderProposalSection();
      renderImage();
      markDirty();
    });
  });
  const syncManual = () => {
    const ra = parseFloat($("#prop-manual-ra").value);
    const dec = parseFloat($("#prop-manual-dec").value);
    state.proposal.manual = Number.isNaN(ra) && Number.isNaN(dec) ? null : { ra: Number.isNaN(ra) ? null : ra, dec: Number.isNaN(dec) ? null : dec };
    updateProposalResponse();
    renderImage();
    markDirty();
  };
  $("#prop-manual-ra").addEventListener("input", syncManual);
  $("#prop-manual-dec").addEventListener("input", syncManual);
}

function selectedValue(containerSel) {
  const container = $(containerSel);
  const btn = container.querySelector("button.selected");
  return btn ? btn.dataset.value : "not_reviewed";
}

function observationValue(name) {
  const row = document.querySelector(`.obs-row[data-obs-name="${name}"]`);
  if (!row) return "not_reviewed";
  const btn = row.querySelector("button.selected");
  return btn ? btn.dataset.value : "not_reviewed";
}

function setObservation(name, value) {
  const row = document.querySelector(`.obs-row[data-obs-name="${name}"]`);
  if (!row) return;
  const btn = row.querySelector(`button[data-value="${value}"]`);
  if (btn) btn.click();
}

function refreshSelectButtons() {
  document.querySelectorAll(".select-source").forEach((btn) => {
    const type = btn.dataset.sourceType;
    const id = btn.dataset.sourceId;
    const selected = type === "gaia" ? state.proposal.gaia : state.proposal.legacy;
    btn.textContent = selected && selected.source_id === id ? "✓ selected" : "use";
  });
}

function selectCoordinateSource(sourceType, sourceId, ra, dec, button) {
  setObservation("off_center", "yes");
  const current = sourceType === "gaia" ? state.proposal.gaia : state.proposal.legacy;
  const isSelected = current && current.source_id === sourceId;
  if (isSelected) {
    if (sourceType === "gaia") state.proposal.gaia = null;
    else state.proposal.legacy = null;
  } else {
    if (sourceType === "gaia") {
      state.proposal.gaia = { source_id: sourceId, ra: parseFloat(ra), dec: parseFloat(dec) };
    } else {
      state.proposal.legacy = { source_id: sourceId, ra: parseFloat(ra), dec: parseFloat(dec) };
    }
    state.showMarkers = true;
    const selected = sourceType === "gaia" ? state.proposal.gaia : state.proposal.legacy;
    if (!sourcePixel(selected.ra, selected.dec) && state.scale === "compact") {
      state.scale = "wide";
      $("#tab-compact").classList.remove("active");
      $("#tab-wide").classList.add("active");
    }
  }
  updateProposalResponse();
  refreshSelectButtons();
  renderImage();
  renderProposalSection();
  const saved = $("#review-saved");
  if (saved) saved.textContent = isSelected ? `Cleared ${sourceId}` : `Selected ${sourceId} as ${sourceType} reference (unsaved)`;
  markDirty();
}

function collectReview() {
  const observations = Object.fromEntries(
    OBSERVATIONS.map((name) => [name, observationValue(name)])
  );
  const derived = deriveProposal(state.proposal);
  const proposal = {
    response: state.proposal.response,
    gaia_source_id: state.proposal.gaia?.source_id || null,
    legacy_source_id: state.proposal.legacy?.source_id || null,
    coordinate_reference: derived.coordinate_reference,
    proposed_ra: derived.proposed_ra,
    proposed_dec: derived.proposed_dec,
    reference_quality: derived.reference_quality,
  };
  return {
    client_revision: state.review.client_revision || 0,
    image_usability: selectedValue("#seg-usability"),
    observations,
    final_decision: selectedValue("#seg-decision"),
    evidence_note: $("#note-evidence").value,
    general_comment: $("#note-general").value,
    decision_reason: $("#note-reason").value,
    coordinate_proposal: proposal,
  };
}

async function save(next) {
  const payload = collectReview();
  const response = await fetch(`/api/objects/${state.currentObject.canonical_object_id}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  $("#review-error").textContent = "";
  if (response.status === 400) {
    $("#review-error").textContent = (data.errors || []).join("; ");
    return;
  }
  if (response.status === 409) {
    $("#conflict-dialog").classList.remove("hidden");
    return;
  }
  state.review = { ...payload, revision_id: data.revision_id, client_revision: data.revision_id };
  state.dirty = false;
  $("#review-saved").textContent = `Saved revision #${data.revision_id}`;
  $("#saved-state").textContent = `Saved revision #${data.revision_id}`;
  if (next) step(1);
}

function step(delta) {
  if (state.dirty && !confirm("Unsaved changes will be lost. Continue?")) return;
  const nextIndex = state.currentIndex + delta;
  if (nextIndex < 0 || nextIndex >= state.items.length) return;
  state.currentIndex = nextIndex;
  loadObject(state.items[nextIndex].canonical_object_id);
  const active = document.querySelectorAll(".object-list li");
  active.forEach((li, i) => li.classList.toggle("active", i === nextIndex));
}

function markDirty() {
  state.dirty = true;
  $("#review-saved").textContent = "Unsaved changes";
}

function fmtNum(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return number.toPrecision(4);
}
function fmtDist(mpc) { return mpc ? `${fmtNum(mpc)} Mpc` : "—"; }
function fmtCoord(value) { return Number(value).toFixed(5); }
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(".select-source");
  if (!button) return;
  selectCoordinateSource(
    button.dataset.sourceType,
    button.dataset.sourceId,
    button.dataset.ra,
    button.dataset.dec,
    button
  );
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "s") {
    event.preventDefault();
    if (state.currentObject) save(false);
    return;
  }
  if (event.target.matches("input, textarea, select")) return;
  if (event.key === "ArrowRight" && state.currentObject) step(1);
  if (event.key === "ArrowLeft" && state.currentObject) step(-1);
});

window.addEventListener("beforeunload", (event) => {
  if (state.dirty) event.preventDefault();
});

$("#search").addEventListener("input", (event) => {
  state.query = event.target.value;
  state.page = 1;
  loadList();
});
$("#filter-cohort").addEventListener("change", (e) => { state.cohort = e.target.value; state.page = 1; loadList(); });
$("#filter-review").addEventListener("change", (e) => { state.reviewStatus = e.target.value; state.page = 1; loadList(); });
$("#filter-decision").addEventListener("change", (e) => { state.decision = e.target.value; state.page = 1; loadList(); });
$("#prev-page").addEventListener("click", () => { state.page = Math.max(1, state.page - 1); loadList(); });
$("#next-page").addEventListener("click", () => { state.page += 1; loadList(); });
$("#conflict-close").addEventListener("click", () => $("#conflict-dialog").classList.add("hidden"));

loadSummary();
loadList();
