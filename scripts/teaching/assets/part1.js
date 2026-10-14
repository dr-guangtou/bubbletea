"use strict";
const packet = JSON.parse(document.getElementById("teaching_packet").textContent);
const by_id = id => document.getElementById(id);
const columns = Object.fromEntries(packet.catalog_columns.map((name, index) => [name, index]));
const rows = packet.catalog_rows;
const features = packet.features;
const feature_lookup = Object.fromEntries(features.map(field => [field.key, field]));
const task1_objects = packet.gallery.filter(object => object.role === "task1");
const examples = packet.gallery.filter(object => object.role === "example");
const totals = {ucd: 0, star: 0, qso: 0, candidate: 0};
for (const row of rows) totals[row[columns.reference_class]]++;
const storage_key = `bubbletea_part1_${packet.packet_sha256}`;
let current_object = task1_objects[0].object_key;
let current_example = examples[0].object_key;
let storage_available = true;
let has_unsaved_changes = false;
let selected_mask = null;
let table_page = 0;
let scan_timer = null;
const plot_definitions = [
  {x: "phot_g_mean_mag", y: "phot_bp_rp_excess_factor", title: "Brightness and flux excess"},
  {x: "phot_g_mean_mag", y: "astrometric_excess_noise", title: "Brightness and excess noise"},
  {x: "bp_rp", y: "phot_bp_rp_excess_factor", title: "Color and flux excess"},
  {x: "absolute_parallax_significance", y: "proper_motion_significance", title: "Parallax and proper motion"}
];
const plots = [];

function blank_rules() {
  return Object.fromEntries(features.map(field => [field.key, {enabled: false, minimum: null, maximum: null}]));
}
function empty_state() {
  return {
    schema_version: "bubbletea_answers_v3", activity_version: packet.activity_version,
    packet_sha256: packet.packet_sha256, student_identifier: "",
    task1_responses: Object.fromEntries(task1_objects.map(object => [object.object_key, {
      source_id: object.source_id, classification: "", confidence: "", evidence_note: "", evidence_basis: "", citation: ""
    }])),
    draft_rules: blank_rules(), draft_missing_policy: "keep", task2_attempts: [],
    task2_final_selection: {attempt_id: "", why_it_works: "", how_to_improve: ""},
    imported_v2_final_rules: null,
    task3_membership_answer: "", llm_disclosure: {used: "", contribution_and_verification: ""}
  };
}
let state = empty_state();

function is_record(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
function exact_keys(value, keys) {
  return is_record(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}
function bounded_text(value, maximum) { return typeof value === "string" && value.length <= maximum; }
function copy(value) { return JSON.parse(JSON.stringify(value)); }
function format(value, digits = 3) {
  return value === null || value === undefined ? "Not supplied" : Number(value).toLocaleString("en-US", {maximumFractionDigits: digits});
}
function percent(value) { return value === null ? "Undefined" : `${(100 * value).toFixed(1)}%`; }
function element(tag, text = "", class_name = "") {
  const item = document.createElement(tag); item.textContent = text; if (class_name) item.className = class_name; return item;
}
function safe_link(label, url) {
  const link = element("a", label); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; return link;
}
function validate_rules(rules) {
  if (!exact_keys(rules, features.map(field => field.key))) throw new Error("Invalid measurement set in selection rules.");
  for (const field of features) {
    const rule = rules[field.key];
    if (!exact_keys(rule, ["enabled", "minimum", "maximum"]) || typeof rule.enabled !== "boolean") throw new Error("Invalid rule structure.");
    for (const bound of [rule.minimum, rule.maximum]) {
      if (bound !== null && (typeof bound !== "number" || !Number.isFinite(bound) || Math.abs(bound) > 1e15)) throw new Error("Boundaries must be finite numbers or unbounded.");
    }
    if (rule.minimum !== null && rule.maximum !== null && rule.minimum > rule.maximum) throw new Error(`${field.label}: minimum is greater than maximum.`);
  }
}
function compute_selection(rules, missing_policy, include_mask = true) {
  const active = features.filter(field => rules[field.key].enabled).map(field => [columns[field.key], rules[field.key]]);
  const counts = {ucd: 0, star: 0, qso: 0, candidate: 0, selected_missing: 0, total_selected: 0};
  const mask = include_mask ? new Uint8Array(rows.length) : null;
  for (let index = 0; index < rows.length; index++) {
    const row = rows[index]; let selected = true, missing = false;
    for (const [column, rule] of active) {
      const value = row[column];
      if (value === null) {missing = true; if (missing_policy === "exclude") selected = false;}
      else if ((rule.minimum !== null && value < rule.minimum) || (rule.maximum !== null && value > rule.maximum)) selected = false;
    }
    if (selected) {
      if (mask) mask[index] = 1;
      counts[row[columns.reference_class]]++; counts.total_selected++;
      if (missing) counts.selected_missing++;
    }
  }
  const scored = counts.ucd + counts.star + counts.qso;
  return {counts, metrics: {purity: scored ? counts.ucd / scored : null, completeness: totals.ucd ? counts.ucd / totals.ucd : null, f1: totals.ucd + scored ? 2 * counts.ucd / (totals.ucd + scored) : null}, mask};
}
function same_numbers(left, right) {
  return exact_keys(left, Object.keys(right)) && Object.keys(right).every(key => {
    if (right[key] === null) return left[key] === null;
    return typeof left[key] === "number" && Number.isFinite(left[key]) && Math.abs(left[key] - right[key]) < 1e-12;
  });
}
function upgrade_v2_answers(value) {
  if (!is_record(value) || value.schema_version !== "bubbletea_answers_v2") return value;
  const old_keys = Object.keys(empty_state()).filter(key => !["task2_final_selection", "imported_v2_final_rules"].includes(key)).concat("task2_final_rules");
  if (!exact_keys(value, old_keys) || !Array.isArray(value.task2_attempts) || value.task2_attempts.length > 500) throw new Error("Invalid older answer structure.");
  const upgraded = copy(value);
  for (const attempt of upgraded.task2_attempts) {
    validate_rules(attempt.rules);
    if (!["keep", "exclude"].includes(attempt.missing_policy)) throw new Error("Invalid older missing-data policy.");
    const result = compute_selection(attempt.rules, attempt.missing_policy, false);
    if (!same_numbers(attempt.counts, result.counts) || !same_numbers(attempt.metrics, {purity:result.metrics.purity, completeness:result.metrics.completeness})) throw new Error("Older counts or scores do not reproduce.");
    attempt.metrics = result.metrics;
  }
  upgraded.schema_version = "bubbletea_answers_v3";
  upgraded.imported_v2_final_rules = upgraded.task2_final_rules;
  delete upgraded.task2_final_rules;
  upgraded.task2_final_selection = {attempt_id:"", why_it_works:"", how_to_improve:""};
  return upgraded;
}
function validate_state(value) {
  value = upgrade_v2_answers(value);
  if (!exact_keys(value, Object.keys(empty_state())) || value.schema_version !== "bubbletea_answers_v3" ||
      value.activity_version !== packet.activity_version || value.packet_sha256 !== packet.packet_sha256)
    throw new Error("This answer file is not for this exact Part I version and catalog. Version 1 worksheets cannot be imported here.");
  if (!bounded_text(value.student_identifier, 80) || !exact_keys(value.task1_responses, task1_objects.map(object => object.object_key))) throw new Error("Invalid student or object identifiers.");
  for (const object of task1_objects) {
    const response = value.task1_responses[object.object_key];
    if (!exact_keys(response, ["source_id", "classification", "confidence", "evidence_note", "evidence_basis", "citation"]) ||
        typeof response.source_id !== "string" || response.source_id !== object.source_id ||
        !["", "ucd", "star", "qso", "uncertain"].includes(response.classification) ||
        !["", "low", "medium", "high"].includes(response.confidence) ||
        !["", "supplied_observations", "external_record", "both"].includes(response.evidence_basis) ||
        !bounded_text(response.evidence_note, 6000) || !bounded_text(response.citation, 2000)) throw new Error("Invalid Task 1 response or exact Gaia identifier.");
  }
  validate_rules(value.draft_rules);
  if (!["keep", "exclude"].includes(value.draft_missing_policy) || !Array.isArray(value.task2_attempts) || value.task2_attempts.length > 500) throw new Error("Invalid selection history or missing-data policy.");
  const attempt_ids = new Set();
  for (const attempt of value.task2_attempts) {
    if (!exact_keys(attempt, ["attempt_id", "rules", "missing_policy", "counts", "metrics"]) ||
        typeof attempt.attempt_id !== "string" || !/^attempt_\d{4}$/.test(attempt.attempt_id) || attempt_ids.has(attempt.attempt_id) ||
        !["keep", "exclude"].includes(attempt.missing_policy)) throw new Error("Invalid or duplicate selection attempt.");
    attempt_ids.add(attempt.attempt_id); validate_rules(attempt.rules);
    const result = compute_selection(attempt.rules, attempt.missing_policy, false);
    if (!same_numbers(attempt.counts, result.counts) || !same_numbers(attempt.metrics, result.metrics)) throw new Error("Saved counts or scores do not reproduce from the supplied rules.");
  }
  const final = value.task2_final_selection;
  if (!exact_keys(final, ["attempt_id", "why_it_works", "how_to_improve"]) ||
      !(final.attempt_id === "" || attempt_ids.has(final.attempt_id)) ||
      !bounded_text(final.why_it_works, 6000) || !bounded_text(final.how_to_improve, 6000) ||
      !bounded_text(value.task3_membership_answer, 12000) ||
      !exact_keys(value.llm_disclosure, ["used", "contribution_and_verification"]) ||
      !["", "yes", "no"].includes(value.llm_disclosure.used) || !bounded_text(value.llm_disclosure.contribution_and_verification, 6000))
    throw new Error("Invalid final rules, membership response, or disclosure.");
  const previous = value.imported_v2_final_rules;
  if (previous !== null && (!exact_keys(previous, ["recovery_attempt_id", "purity_attempt_id", "recovery_explanation", "purity_explanation"]) ||
      ![previous.recovery_attempt_id, previous.purity_attempt_id].every(id => id === "" || attempt_ids.has(id)) ||
      !bounded_text(previous.recovery_explanation, 6000) || !bounded_text(previous.purity_explanation, 6000))) throw new Error("Invalid preserved version 2 choices.");
  return value;
}
function complete_response(response) {
  return Boolean(response.classification);
}
function update_progress() {
  const completed = Object.values(state.task1_responses).filter(complete_response).length;
  by_id("task1_progress").textContent = `${completed} / ${task1_objects.length} classifications recorded. Other fields are optional. This is progress, not accuracy.`;
  for (const button of by_id("task1_navigation").children) button.classList.toggle("answered", Boolean(complete_response(state.task1_responses[button.dataset.object_key])));
  const final = state.task2_final_selection, final_done = final.attempt_id && final.why_it_works.trim() && final.how_to_improve.trim();
  by_id("completion_status").textContent = `Task 1: ${completed}/${task1_objects.length} classified. Task 2: ${final_done ? "final selection and explanations recorded" : "final selection or explanations incomplete"}. Task 3: ${state.task3_membership_answer.trim() ? "answer recorded" : "not answered"}.`;
}
function persist() {
  has_unsaved_changes = true;
  try { localStorage.setItem(storage_key, JSON.stringify(state)); } catch { storage_available = false; }
  by_id("save_status").textContent = storage_available ? "Draft saved in this browser. Download JSON to keep or submit it reliably." : "Browser storage is unavailable. Keep this tab open and download JSON to save your work.";
  update_progress();
}
function source_links(object) {
  const group = element("div", "", "object_links");
  const coordinate = {ra: object.gaia.ra, dec: object.gaia.dec};
  const viewer = "https://www.legacysurvey.org/viewer?" + new URLSearchParams({...coordinate, layer: "ls-dr11", zoom: 17});
  const query = `SELECT source_id,ra,dec,phot_g_mean_mag,bp_rp,parallax,parallax_error,pmra,pmra_error,pmdec,pmdec_error,phot_bp_rp_excess_factor,ruwe FROM gaiadr3.gaia_source WHERE source_id=${object.source_id}`;
  const direct = "https://gea.esac.esa.int/tap-server/tap/sync?" + new URLSearchParams({REQUEST: "doQuery", LANG: "ADQL", FORMAT: "csv", QUERY: query});
  const simbad = "https://simbad.cds.unistra.fr/simbad/sim-coo?" + new URLSearchParams({Coord: `${coordinate.ra} ${coordinate.dec}`, Radius: "5", "Radius.unit": "arcsec"});
  const sdss = "https://skyserver.sdss.org/dr16/en/tools/explore/Summary.aspx?" + new URLSearchParams(coordinate);
  for (const [label, url] of [["Legacy viewer ↗", viewer], ["Gaia Archive ↗", "https://gea.esac.esa.int/archive/"], ["Gaia row (CSV) ↗", direct], ["SIMBAD position search ↗", simbad], ["SDSS position search ↗", sdss]]) group.append(safe_link(label, url));
  return group;
}
function render_object(object, container) {
  const task1 = object.role === "task1";
  if (!task1) container.replaceChildren();
  const layout = element("div", "", "inspection_layout"), image_panel = element("article"), catalog = element("aside", "", "catalog_panel");
  const header = element("div", "", "object_title"); header.append(element("h3", object.display_name));
  const marker_label = element("label", "", "marker_label"), toggle = document.createElement("input"); toggle.type = "checkbox"; toggle.checked = true;
  marker_label.append(toggle, document.createTextNode(" Show position")); header.append(marker_label); image_panel.append(header);
  const coordinates = element("p", `Gaia ${object.source_id} · RA ${format(object.gaia.ra, 8)}° · Dec ${format(object.gaia.dec, 8)}° · ICRS J2016.0`, "object_coordinates");
  if (task1) catalog.append(element("h3", `Measurements / ${object.display_name}`), coordinates);
  else image_panel.append(coordinates);
  if (object.role === "example") {
    const context = object.context || {};
    image_panel.append(element("p", `Reference class: ${context.reference_label || object.reference_class.toUpperCase()}`, "eyebrow"));
    if (context.note) image_panel.append(element("p", context.note, "source_context"));
    if (context.host) image_panel.append(element("p", `${context.host}. ${context.distance_mpc === null || context.distance_mpc === undefined ? "" : `Adopted host distance ${context.distance_mpc} Mpc. `}${context.distance_basis || ""}`, "source_context"));
  }
  const image_grid = element("div", "", "image_grid");
  for (const scale of ["close", "context"]) {
    const photo = object.images[scale], figure = document.createElement("figure"), frame = element("div", "", "image_frame");
    if (photo && photo.data_url) {
      const image = document.createElement("img"); image.src = photo.data_url; image.alt = `${object.display_name}, ${scale} view, Legacy Survey DR11`; image.width = photo.size_pixels; image.height = photo.size_pixels;
      const marker = element("span", "", "position_marker"); marker.setAttribute("aria-hidden", "true");
      const bar_length = scale === "close" ? 5 : 40, bar = element("span", `${bar_length} arcsec`, "scale_bar"); bar.style.width = `${100 * bar_length / photo.field_width_arcsec}%`; bar.setAttribute("aria-hidden", "true");
      frame.append(image, marker, bar);
      figure.append(frame, element("figcaption", `${scale === "close" ? "Close" : "Context"}: ${photo.field_width_arcsec.toFixed(3)} arcsec square; ${photo.pixel_scale_arcsec} arcsec/pixel. North up, east left. Saved ${photo.retrieved_utc.slice(0,10)} UTC.`));
    } else {frame.append(element("p", "Image unavailable. Do not interpret this as an empty field.", "image_unavailable")); figure.append(frame);}
    image_grid.append(figure);
  }
  toggle.addEventListener("change", () => {for (const marker of image_grid.querySelectorAll(".position_marker")) marker.hidden = !toggle.checked;});
  image_panel.append(image_grid);
  if (!task1) image_panel.append(source_links(object));
  if (object.role === "example" && object.context?.paper_url) image_panel.append(safe_link("Reference study ↗", object.context.paper_url));
  const measures = [["Galactic longitude l (deg)", object.galactic_coordinates.longitude_deg], ["Galactic latitude b (deg)", object.galactic_coordinates.latitude_deg],
    ["G magnitude", object.gaia.phot_g_mean_mag], ["BP−RP color (mag)", object.gaia.bp_rp],
    ["BP/RP flux excess", object.gaia.phot_bp_rp_excess_factor], ["Parallax (mas)", object.gaia.parallax, object.gaia.parallax_error],
    ["RA proper motion (mas/yr)", object.gaia.pmra, object.gaia.pmra_error], ["Dec proper motion (mas/yr)", object.gaia.pmdec, object.gaia.pmdec_error],
    ["|parallax| / error", object.gaia.absolute_parallax_significance], ["Combined motion significance", object.gaia.proper_motion_significance],
    ["Excess noise (mas)", object.gaia.astrometric_excess_noise], ["Excess-noise significance", object.gaia.astrometric_excess_noise_sig],
    ["RUWE", object.gaia.ruwe], ["IPD multi-peak (%)", object.gaia.ipd_frac_multi_peak], ["IPD odd-window (%)", object.gaia.ipd_frac_odd_win]];
  const measurement_columns = element("div", "", "measurement_columns");
  const groups = task1 ? [measures.slice(0,8), measures.slice(8)] : [measures];
  for (const group of groups) {
    const table = document.createElement("table"), body = document.createElement("tbody");
    table.setAttribute("aria-label", `${object.display_name} Gaia measurements, ${measurement_columns.children.length+1} of ${groups.length}`);
    for (const [name, value, error] of group) {const row = document.createElement("tr"), heading=element("th", name);heading.scope="row"; row.append(heading, element("td", error !== undefined && value !== null ? `${format(value)} ± ${format(error)}` : format(value))); body.append(row);}
    table.append(body); measurement_columns.append(table);
  }
  catalog.append(measurement_columns, element("p", "Values are Gaia DR3 observations. Missing values are not zero. An image or fit statistic is not a physical classification.", "small"));
  if (task1) {
    catalog.append(source_links(object));
    by_id("task1_properties").replaceChildren(catalog);
    by_id("task1_images").replaceChildren(image_panel);
  } else {layout.append(image_panel, catalog); container.append(layout);}
}
function render_task1() {
  const object = task1_objects.find(object => object.object_key === current_object); render_object(object, by_id("task1_view"));
  for (const button of by_id("task1_navigation").children) button.setAttribute("aria-pressed", String(button.dataset.object_key === current_object));
  const response = state.task1_responses[current_object];
  for (const field of ["classification", "confidence", "evidence_basis"]) for (const input of document.querySelectorAll(`input[name="${field}"]`)) input.checked = input.value === response[field];
  for (const field of ["evidence_note", "citation"]) by_id(field).value = response[field];
  const index = task1_objects.indexOf(object); by_id("previous_object").disabled = index === 0; by_id("next_object").disabled = index === task1_objects.length - 1;
  by_id("response_object").textContent=`Your record / ${object.display_name} of ${task1_objects.length}`;
}
function render_examples() {
  render_object(examples.find(object => object.object_key === current_example), by_id("example_view"));
  for (const button of by_id("example_navigation").children) button.setAttribute("aria-pressed", String(button.dataset.object_key === current_example));
}
function transformed(value, field) {return field.scale === "log1p" ? Math.log1p(value) : value;}
function inverse(value, field) {return field.scale === "log1p" ? Math.expm1(value) : value;}
function slider_position(value, field, lower) {
  if (value === null) return lower ? 0 : 1000;
  const low = transformed(field.minimum, field), high = transformed(field.maximum, field);
  return Math.max(0, Math.min(1000, 1000 * (transformed(Math.max(value, field.minimum), field) - low) / (high - low || 1)));
}
function mark_pending() {
  by_id("pending_status").textContent = "Settings changed. Press Evaluate selection to update the highlights and scores.";
  try {validate_rules(state.draft_rules); by_id("rule_error").textContent = "";} catch (error) {by_id("rule_error").textContent = error.message;}
  persist();
}
function set_rule_bound(field, bound, value) {
  const previous = state.draft_rules[field.key][bound];
  state.draft_rules[field.key][bound] = value;
  try {validate_rules(state.draft_rules);}
  catch (error) {
    state.draft_rules[field.key][bound] = previous;
    sync_rule_controls(); by_id("rule_error").textContent = `${error.message} That change was not saved.`; return;
  }
  sync_rule_controls(); mark_pending();
}
function sync_rule_controls() {
  for (const field of features) {
    const rule = state.draft_rules[field.key]; by_id(`enable_${field.key}`).checked = rule.enabled;
    by_id(`rule_${field.key}`).classList.toggle("rule_disabled", !rule.enabled);
    for (const bound of ["minimum", "maximum"]) {
      by_id(`${field.key}_${bound}`).value = rule[bound] === null ? "" : String(rule[bound]);
      by_id(`${field.key}_${bound}_slider`).value = slider_position(rule[bound], field, bound === "minimum");
    }
  }
  by_id("missing_policy").value = state.draft_missing_policy;
}
function build_rule_controls() {
  for (const field of features) {
    const group = element("div", "", "rule_field rule_disabled"); group.id = `rule_${field.key}`;
    const label = element("label", "", "rule_toggle"), checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.id = `enable_${field.key}`;
    label.append(checkbox, document.createTextNode(` ${field.label}`)); group.append(label, element("p", field.definition, "rule_description"));
    const bounds = element("div", "", "rule_bounds");
    for (const bound of ["minimum", "maximum"]) {
      const bound_label = element("label", bound === "minimum" ? "Minimum" : "Maximum");
      const input = document.createElement("input"); input.type = "number"; input.step = "any"; input.id = `${field.key}_${bound}`; input.placeholder = "Unbounded";
      const slider = document.createElement("input"); slider.type = "range"; slider.min = 0; slider.max = 1000; slider.step = 1; slider.id = `${field.key}_${bound}_slider`; slider.setAttribute("aria-label", `${field.label} ${bound}`);
      input.addEventListener("change", () => {
        if (input.validity.badInput) {sync_rule_controls(); by_id("rule_error").textContent = "Incomplete or invalid number; your previous boundary was kept. Clear the box deliberately for an unbounded limit."; return;}
        const value = input.value === "" ? null : Number(input.value);
        if (value !== null && !Number.isFinite(value)) {by_id("rule_error").textContent = "Use a finite number."; return;}
        set_rule_bound(field, bound, value);
      });
      slider.addEventListener("input", () => {
        const low = transformed(field.minimum, field), high = transformed(field.maximum, field);
        const position = Number(slider.value);
        const value = position === 0 ? field.minimum : position === 1000 ? field.maximum : inverse(low + position / 1000 * (high - low), field);
        set_rule_bound(field, bound, value);
      });
      bound_label.append(input, slider); bounds.append(bound_label);
    }
    checkbox.addEventListener("change", () => {state.draft_rules[field.key].enabled = checkbox.checked; group.classList.toggle("rule_disabled", !checkbox.checked); mark_pending();});
    group.append(bounds, element("p", `Observed ${format(field.minimum)} to ${format(field.maximum)} ${field.unit}. ${field.scale === "log1p" ? "Log-spaced slider; saved values remain in these units." : "Linear slider."}`, "range_note"));
    by_id(field.advanced ? "advanced_rules" : "primary_rules").append(group);
  }
  sync_rule_controls();
}
function coordinate(value, field, start, span, reversed = false) {
  const low = transformed(field.minimum, field), high = transformed(field.maximum, field);
  const fraction = (transformed(value, field) - low) / (high - low || 1);
  return start + span * (reversed ? 1 - fraction : fraction);
}
function build_plots() {
  for (const definition of plot_definitions) {
    const x_field = feature_lookup[definition.x], y_field = feature_lookup[definition.y];
    const card = element("article", "", "plot_card"), canvas = document.createElement("canvas"); canvas.width = 800; canvas.height = 500;
    canvas.setAttribute("role", "img"); canvas.setAttribute("aria-label", `${definition.title}; all available objects, selected objects highlighted. Equivalent records are in the catalog table below.`);
    const context = canvas.getContext("2d"), points = [];
    for (let index = 0; index < rows.length; index++) {
      const x = rows[index][columns[definition.x]], y = rows[index][columns[definition.y]];
      if (x !== null && y !== null) points.push([coordinate(x, x_field, 82, 684), coordinate(y, y_field, 22, 400, true), index]);
    }
    const plot = {definition, canvas, context, points, x_field, y_field, background: document.createElement("canvas")};
    plot.background.width = 800; plot.background.height = 500;
    const base = plot.background.getContext("2d"); base.fillStyle = "#fffdf7"; base.fillRect(0,0,800,500);
    base.font = "16px sans-serif"; base.fillStyle = "#405b50"; base.strokeStyle = "#e0e3d9"; base.lineWidth = 1;
    for (let tick = 0; tick <= 4; tick++) {
      const x = 82 + tick * 684 / 4, y = 422 - tick * 400 / 4;
      base.beginPath(); base.moveTo(x,22); base.lineTo(x,422); base.moveTo(82,y); base.lineTo(766,y); base.stroke();
      const x_value = inverse(transformed(x_field.minimum,x_field) + tick/4*(transformed(x_field.maximum,x_field)-transformed(x_field.minimum,x_field)),x_field);
      const y_value = inverse(transformed(y_field.minimum,y_field) + tick/4*(transformed(y_field.maximum,y_field)-transformed(y_field.minimum,y_field)),y_field);
      base.textAlign = "center"; base.fillText(format(x_value,2),x,446); base.textAlign = "right"; base.fillText(format(y_value,2),75,y+5);
    }
    base.font = "18px sans-serif"; base.textAlign = "center"; base.fillText(x_field.short_label,424,483);
    base.save(); base.translate(20,222); base.rotate(-Math.PI/2); base.fillText(y_field.short_label,0,0); base.restore();
    base.fillStyle = "#476d6248"; for (const [x,y] of points) base.fillRect(x-1.2,y-1.2,2.4,2.4);
    canvas.addEventListener("mousemove", event => {
      const rectangle = canvas.getBoundingClientRect(), pointer_x = (event.clientX-rectangle.left)*800/rectangle.width, pointer_y = (event.clientY-rectangle.top)*500/rectangle.height;
      let nearest = null, distance = 144;
      for (const point of points) {const current_distance=(point[0]-pointer_x)**2+(point[1]-pointer_y)**2; if (current_distance<distance) {nearest=point;distance=current_distance;}}
      if (nearest) {const row=rows[nearest[2]]; by_id("plot_hover").textContent=`Gaia ${row[0]} · ${x_field.label}: ${format(row[columns[definition.x]])} · ${y_field.label}: ${format(row[columns[definition.y]])}${selected_mask ? ` · ${selected_mask[nearest[2]] ? "selected" : "not selected"}` : ""}`;}
      else clear_plot_hover();
    });
    canvas.addEventListener("mouseleave", clear_plot_hover);
    card.append(element("h3",definition.title),canvas,element("p",`${points.length.toLocaleString()} plotted; ${(rows.length-points.length).toLocaleString()} omitted here for unavailable coordinates, but still present in the selection catalog. Spacing: horizontal ${x_field.scale === "log1p" ? "log(1 + value)" : "linear"}; vertical ${y_field.scale === "log1p" ? "log(1 + value)" : "linear"}. Ticks give physical values.`,"small"));
    by_id("plots").append(card); plots.push(plot);
  }
  draw_plots();
}
function draw_plots() {
  for (const plot of plots) {
    plot.context.drawImage(plot.background,0,0); plot.context.fillStyle = "#b3542bcc";
    if (selected_mask) for (const [x,y,index] of plot.points) if (selected_mask[index]) plot.context.fillRect(x-1.5,y-1.5,3,3);
  }
}
function clear_plot_hover() {
  by_id("plot_hover").textContent = "Hover over a point for its measurements. Classes are not shown.";
}
function render_results(attempt) {
  const result = compute_selection(attempt.rules, attempt.missing_policy); selected_mask=result.mask;
  clear_plot_hover();
  const output=by_id("results"); output.replaceChildren();
  const grid=element("div","","metric_grid");
  for (const [label,value] of [["F1 · improve this",result.metrics.f1 === null ? "Undefined" : result.metrics.f1.toFixed(3)],["Reference-subset purity",percent(result.metrics.purity)],["UCD completeness",percent(result.metrics.completeness)]]) {
    const card=element("div","","metric");card.append(element("strong",value),element("span",label));grid.append(card);
  }
  output.append(element("p",`${attempt.attempt_id.replace("attempt_","Attempt ")} · last evaluated result`,"eyebrow"),grid,
    element("p",`${result.counts.total_selected} selected: ${result.counts.ucd} / ${totals.ucd} reference UCDs · ${result.counts.star} stars · ${result.counts.qso} QSOs · ${result.counts.candidate} unconfirmed candidates. ${totals.ucd-result.counts.ucd} reference UCDs missed.`,"count_line"),
    element("p",`${result.counts.selected_missing} selected objects have an unavailable active measurement. Missing-data policy: ${attempt.missing_policy}. Unknown candidates enter none of the scores.`,"small"));
  draw_plots(); render_catalog_table();
}
function render_history() {
  by_id("history_rows").replaceChildren();
  for (const attempt of state.task2_attempts) {
    const row=element("tr");
    for (const value of [attempt.attempt_id.replace("attempt_",""),attempt.counts.ucd,attempt.counts.star,attempt.counts.qso,attempt.counts.candidate,percent(attempt.metrics.purity),percent(attempt.metrics.completeness),attempt.metrics.f1 === null ? "Undefined" : attempt.metrics.f1.toFixed(3)]) row.append(element("td",String(value)));
    const cell=element("td"), button=element("button","Load rules","secondary");button.addEventListener("click",()=>{state.draft_rules=copy(attempt.rules);state.draft_missing_policy=attempt.missing_policy;sync_rule_controls();mark_pending();});cell.append(button);row.append(cell);by_id("history_rows").append(row);
  }
  const select=by_id("final_attempt");select.replaceChildren();const empty=element("option","Choose an evaluated attempt");empty.value="";select.append(empty);
  for (const attempt of state.task2_attempts) {const option=element("option",`${attempt.attempt_id.replace("attempt_","Attempt ")} · F1 ${attempt.metrics.f1 === null ? "undefined" : attempt.metrics.f1.toFixed(3)} · purity ${percent(attempt.metrics.purity)} / completeness ${percent(attempt.metrics.completeness)}`);option.value=attempt.attempt_id;select.append(option);}
  select.value=state.task2_final_selection.attempt_id;
}
function evaluate_selection() {
  try {
    validate_rules(state.draft_rules);
    if (state.task2_attempts.length >= 500) throw new Error("This answer file already holds 500 evaluated attempts. Export it before beginning a separate investigation.");
    const used=state.task2_attempts.map(attempt=>Number(attempt.attempt_id.slice(8))), next=used.length?Math.max(...used)+1:1;
    if(next>9999) throw new Error("Attempt identifier limit reached.");
    const result=compute_selection(state.draft_rules,state.draft_missing_policy);
    const attempt={attempt_id:`attempt_${String(next).padStart(4,"0")}`,rules:copy(state.draft_rules),missing_policy:state.draft_missing_policy,counts:result.counts,metrics:result.metrics};
    state.task2_attempts.push(attempt);render_history();render_results(attempt);by_id("pending_status").textContent="These settings have been evaluated. Change them to try another selection.";by_id("rule_error").textContent="";persist();
  } catch(error) {by_id("rule_error").textContent=error.message;}
}
function render_catalog_table() {
  const indices=[];for(let index=0;index<rows.length;index++) if(by_id("table_mode").value==="all" || selected_mask?.[index]) indices.push(index);
  const pages=Math.max(1,Math.ceil(indices.length/25));table_page=Math.max(0,Math.min(table_page,pages-1));by_id("catalog_table").replaceChildren();
  for(const index of indices.slice(table_page*25,(table_page+1)*25)) {const row=rows[index],tr=element("tr");for(const field of ["source_id","phot_g_mean_mag","bp_rp","phot_bp_rp_excess_factor","astrometric_excess_noise","absolute_parallax_significance","proper_motion_significance"]) tr.append(element("td",field==="source_id"?row[0]:format(row[columns[field]])));by_id("catalog_table").append(tr);}
  by_id("table_page").textContent=`Page ${table_page+1}/${pages} · ${indices.length.toLocaleString()} records`;by_id("table_previous").disabled=table_page===0;by_id("table_next").disabled=table_page===pages-1;
}
function apply_state() {
  clear_plot_hover();
  by_id("student_identifier").value=state.student_identifier;by_id("membership_answer").value=state.task3_membership_answer;
  by_id("llm_used").value=state.llm_disclosure.used;by_id("llm_disclosure").value=state.llm_disclosure.contribution_and_verification;
  for(const name of ["why_it_works","how_to_improve"]) by_id(name).value=state.task2_final_selection[name];
  by_id("previous_final_choices").hidden=state.imported_v2_final_rules===null;
  by_id("previous_final_text").textContent=state.imported_v2_final_rules===null?"":`Your earlier choices are retained below. Please choose one final selection and answer the two revised prompts.\n\n${JSON.stringify(state.imported_v2_final_rules,null,2)}`;
  sync_rule_controls();render_task1();render_history();update_progress();
  if(state.task2_attempts.length) render_results(state.task2_attempts.at(-1));
  else {selected_mask=null;draw_plots();render_catalog_table();by_id("results").replaceChildren(element("p","Set some rules and press Evaluate selection to see counts and scores."));}
  by_id("pending_status").textContent="Restored current settings. The plots show the last evaluated attempt, if any. Evaluate to apply pending changes.";
}
function apply_import(candidate) {
  const previous_state = state;
  state = candidate;
  try {apply_state();}
  catch(error) {
    state = previous_state;
    try {apply_state();}
    catch {throw new Error("Your previous answers are retained in memory, but the display could not be restored. Download JSON before reloading.");}
    throw error;
  }
}
function readable_report() {
  const lines=["A Galaxy in Disguise — Part I",`Student ID: ${state.student_identifier}`,`Activity: ${state.activity_version}`,`Packet SHA-256: ${state.packet_sha256}`,"","TASK 1 — CLASSIFICATIONS (no answer key)"];
  for(const object of task1_objects) {const response=state.task1_responses[object.object_key];lines.push("",`${object.display_name} / Gaia ${object.source_id}`,`Classification: ${response.classification||"unanswered"}; confidence: ${response.confidence||"unanswered"}`,`Evidence basis: ${response.evidence_basis||"unanswered"}`,response.evidence_note,`External source: ${response.citation||"not supplied"}`);}
  lines.push("","TASK 2 — EVALUATED ATTEMPTS");
  for(const attempt of state.task2_attempts) {lines.push("",attempt.attempt_id,`Missing measurements: ${attempt.missing_policy}`);for(const field of features){const rule=attempt.rules[field.key];if(rule.enabled)lines.push(`${field.label}: ${rule.minimum??"unbounded"} to ${rule.maximum??"unbounded"} ${field.unit}`);}if(!Object.values(attempt.rules).some(rule=>rule.enabled))lines.push("No active cuts.");lines.push(`Counts: ${JSON.stringify(attempt.counts)}`,`Reference-subset purity: ${percent(attempt.metrics.purity)}; completeness: ${percent(attempt.metrics.completeness)}; F1: ${format(attempt.metrics.f1,6)}`);}
  lines.push("",`Final selection: ${state.task2_final_selection.attempt_id||"not chosen"}`,"Why do you think this works?",state.task2_final_selection.why_it_works,"How do you think this selection can be improved?",state.task2_final_selection.how_to_improve);
  if(state.imported_v2_final_rules!==null)lines.push("","PRESERVED VERSION 2 FINAL CHOICES",JSON.stringify(state.imported_v2_final_rules,null,2));
  lines.push("","TASK 3 — ESTABLISHING MEMBERSHIP",state.task3_membership_answer,"","LLM DISCLOSURE",`Used: ${state.llm_disclosure.used||"not answered"}`,state.llm_disclosure.contribution_and_verification,"","SUBMISSION: Rename your JSON export to [NAME]_[STUDENT_ID].json and upload it to Tsinghua Online Classroom (网络学堂). This TXT report does not replace the JSON.","","Scores concern the securely classified teaching reference subset, not real-sky purity. Unconfirmed candidates enter none of the scores.");
  return lines.join("\n");
}
function download(content, suffix, mime) {
  const url=URL.createObjectURL(new Blob([content],{type:mime}));const link=element("a");link.href=url;link.download=`bubbletea_part1_${(state.student_identifier||"answers").replace(/[^a-zA-Z0-9_-]/g,"_")}.${suffix}`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  if(suffix==="json"){has_unsaved_changes=false;by_id("save_status").textContent="JSON download started. For submission, rename it to [NAME]_[STUDENT_ID].json and upload it to Tsinghua Online Classroom (网络学堂). Keep a local copy.";}
}
function render_scan() {
  const visit=Number(by_id("scan_visit").value),angle=(visit-1)*31;
  by_id("scan_orientation").setAttribute("transform",`rotate(${angle} 300 130)`);by_id("scan_visit_label").textContent=`Illustrative visit ${visit} / orientation ${angle}°`;
}
function render_size() {
  const distance=Number(by_id("distance_slider").value),radius=(180*3600/Math.PI)*24.2/(distance*1e6);
  by_id("distance_value").textContent=distance.toFixed(1);
  by_id("angular_value").textContent=`Half-light radius ${radius.toFixed(3)} arcsec / diameter ${(2*radius).toFixed(3)} arcsec`;
  const svg=by_id("size_ruler");svg.replaceChildren();
  const items=[[2*radius,"Hypothetical half-light diameter","#126456"],[.0589,"Along-scan pixel","#74847a"],[.1768,"Across-scan pixel","#74847a"],[.23,"Onboard pair separation: along","#95451b"],[.70,"Onboard pair separation: across","#95451b"]];
  function add(tag,attributes,text="") {const item=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const [name,value] of Object.entries(attributes))item.setAttribute(name,value);item.textContent=text;svg.append(item);}
  items.forEach(([size,label,color],index)=>{const y=30+index*43;add("text",{x:15,y:y+4},label);add("line",{x1:300,x2:300+size*105,y1:y,y2:y,stroke:color,"stroke-width":12});add("text",{x:545,y:y+4},`${size.toFixed(3)} arcsec`);});
}
function initialize() {
  for(const [objects,container] of [[examples,"example_navigation"],[task1_objects,"task1_navigation"]]) {
    for(const object of objects) {const button=element("button",object.role==="task1"?object.display_name:object.display_name.split(";")[0]);button.dataset.object_key=object.object_key;button.setAttribute("aria-pressed","false");button.addEventListener("click",()=>{if(object.role==="task1"){current_object=object.object_key;render_task1();}else{current_example=object.object_key;render_examples();}});by_id(container).append(button);}
  }
  build_rule_controls();build_plots();render_examples();
  try {const saved=localStorage.getItem(storage_key);if(saved)state=validate_state(JSON.parse(saved));}catch(error){storage_available=false;by_id("import_error").textContent=`Local draft was not loaded: ${error.message}`;}
  apply_state();
  by_id("sample_description").textContent=`${rows.length.toLocaleString()} real catalog sources. Stars dominate this deliberately constructed sample. Labeled examples and Task 1 objects are excluded. All available points are drawn; dense areas overlap. No class labels appear on individual points or table rows.`;
  by_id("packet_identity").textContent=`${packet.activity_version} · packet SHA-256 ${packet.packet_sha256} · lesson data assembled ${packet.prepared_utc.slice(0,10)} UTC from saved Gaia DR3 source records`;
  by_id("save_status").textContent=storage_available?"Export JSON whenever you want to save, resume elsewhere, or submit.":"Browser storage is unavailable. Export JSON to save your work.";
  for(const field of ["classification","confidence","evidence_basis"]) by_id(field).addEventListener("change",event=>{state.task1_responses[current_object][field]=event.target.value;persist();});
  for(const field of ["evidence_note","citation"]) by_id(field).addEventListener("input",()=>{state.task1_responses[current_object][field]=by_id(field).value;persist();});
  for(const [button,direction] of [["previous_object",-1],["next_object",1]]) by_id(button).addEventListener("click",()=>{const index=task1_objects.findIndex(object=>object.object_key===current_object);current_object=task1_objects[index+direction].object_key;render_task1();by_id("response_object").focus({preventScroll:true});by_id("task1_review").scrollIntoView({block:"start",behavior:"instant"});});
  by_id("missing_policy").addEventListener("change",()=>{state.draft_missing_policy=by_id("missing_policy").value;mark_pending();});by_id("evaluate").addEventListener("click",evaluate_selection);
  by_id("reset_rules").addEventListener("click",()=>{state.draft_rules=blank_rules();sync_rule_controls();mark_pending();});
  by_id("table_mode").addEventListener("change",()=>{table_page=0;render_catalog_table();});by_id("table_previous").addEventListener("click",()=>{table_page--;render_catalog_table();});by_id("table_next").addEventListener("click",()=>{table_page++;render_catalog_table();});
  by_id("final_attempt").addEventListener("change",()=>{state.task2_final_selection.attempt_id=by_id("final_attempt").value;persist();});
  for(const name of ["why_it_works","how_to_improve"]) by_id(name).addEventListener("input",()=>{state.task2_final_selection[name]=by_id(name).value;persist();});
  by_id("student_identifier").addEventListener("input",()=>{state.student_identifier=by_id("student_identifier").value;persist();});by_id("membership_answer").addEventListener("input",()=>{state.task3_membership_answer=by_id("membership_answer").value;persist();});by_id("llm_used").addEventListener("change",()=>{state.llm_disclosure.used=by_id("llm_used").value;persist();});by_id("llm_disclosure").addEventListener("input",()=>{state.llm_disclosure.contribution_and_verification=by_id("llm_disclosure").value;persist();});
  by_id("export_json").addEventListener("click",()=>{try{validate_state(state);download(JSON.stringify(state,null,2),"json","application/json");by_id("import_error").textContent="";}catch(error){by_id("import_error").textContent=`Cannot export until the invalid settings are corrected: ${error.message}`;}});
  by_id("export_text").addEventListener("click",()=>download(readable_report(),"txt","text/plain;charset=utf-8"));
  by_id("import_file").addEventListener("change",async event=>{
    const file=event.target.files[0];if(!file)return;
    try {if(file.size>5000000)throw new Error("Answer file exceeds the 5 MB safety limit.");const candidate=validate_state(JSON.parse(await file.text()));apply_import(candidate);persist();by_id("import_error").textContent="";by_id("save_status").textContent="Answers restored and all evaluated results independently recomputed. "+(state.imported_v2_final_rules!==null?"Your earlier final choices are preserved; choose one final selection and answer the revised prompts. ":"")+"Export again after further changes.";}
    catch(error){by_id("import_error").textContent=`Import rejected; your current answers were kept. ${error.message}`;}finally{event.target.value="";}
  });
  by_id("scan_visit").addEventListener("input",render_scan);by_id("scan_play").addEventListener("click",()=>{
    if(scan_timer){clearInterval(scan_timer);scan_timer=null;by_id("scan_play").textContent="Play visits";}
    else{scan_timer=setInterval(()=>{by_id("scan_visit").value=Number(by_id("scan_visit").value)%6+1;render_scan();},1200);by_id("scan_play").textContent="Pause visits";}
  });render_scan();
  by_id("distance_slider").addEventListener("input",render_size);render_size();
  window.addEventListener("beforeunload",event=>{if(has_unsaved_changes){event.preventDefault();event.returnValue="";}});
}
initialize();
