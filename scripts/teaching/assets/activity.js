"use strict";
const packet = JSON.parse(document.getElementById("teaching_packet").textContent);
const by_id = id => document.getElementById(id);
const flag_values = ["not_reviewed", "yes", "no", "uncertain", "not_assessable"];
const recommendation_values = ["not_reviewed", "retain", "possible_contaminant", "insufficient_information"];
const storage_key = `bubbletea_${packet.packet_sha256}`;
let current_key = "m60_ucd1";
let storage_available = true;
let exported = false;

function empty_state() {
  return {schema_version: "ucd_answers_v1", packet_version: packet.packet_version,
    packet_sha256: packet.packet_sha256, student_identifier: "",
    answers: Object.fromEntries(packet.questions.map(question => [question.key, ""])),
    reviews: Object.fromEntries(packet.objects.map(object => [object.object_key, {
      source_id: object.source_id, flags: Object.fromEntries(packet.review_fields.map(field => [field.key, "not_reviewed"])),
      r1: "", r2: "", r3: "", recommendation: "not_reviewed"
    }]))};
}
let state = empty_state();

function is_record(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
function exact_keys(value, keys) {
  return is_record(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}
function bounded_text(value, maximum) { return typeof value === "string" && value.length <= maximum; }
function validate_state(value) {
  if (!exact_keys(value, Object.keys(empty_state())) || value.schema_version !== "ucd_answers_v1" ||
      value.packet_version !== packet.packet_version || value.packet_sha256 !== packet.packet_sha256)
    throw new Error("This is not an answer file for this exact teaching packet.");
  if (!bounded_text(value.student_identifier, 80) || !exact_keys(value.answers, packet.questions.map(question => question.key)))
    throw new Error("Invalid student identifier or question set.");
  if (!Object.values(value.answers).every(answer => bounded_text(answer, 6000))) throw new Error("Invalid answer text.");
  if (!exact_keys(value.reviews, packet.objects.map(object => object.object_key))) throw new Error("Invalid object set.");
  for (const object of packet.objects) {
    const review = value.reviews[object.object_key];
    if (!exact_keys(review, ["source_id", "flags", "r1", "r2", "r3", "recommendation"]) ||
        review.source_id !== object.source_id || typeof review.source_id !== "string" ||
        !exact_keys(review.flags, packet.review_fields.map(field => field.key)) ||
        !Object.values(review.flags).every(flag => flag_values.includes(flag)) ||
        !recommendation_values.includes(review.recommendation) ||
        ![review.r1, review.r2, review.r3].every(answer => bounded_text(answer, 6000)))
      throw new Error("Invalid review, flag, or exact Gaia identifier.");
  }
  return value;
}
function readable(value) { return value.replaceAll("_", " "); }
function text_element(tag, text, class_name = "") {
  const element = document.createElement(tag); element.textContent = text;
  if (class_name) element.className = class_name;
  return element;
}
function persist() {
  exported = false;
  try { localStorage.setItem(storage_key, JSON.stringify(state)); }
  catch { storage_available = false; }
  by_id("save_status").textContent = storage_available ? "Draft updated in this browser. Export a file to keep or submit it." : "Browser storage unavailable. Keep this tab open and export a file to save.";
  update_progress();
}
function update_progress() {
  const questions_done = Object.values(state.answers).filter(answer => answer.trim()).length;
  const candidates = packet.objects.filter(object => object.classification === "candidate");
  const reviews_done = candidates.filter(object => {
    const review = state.reviews[object.object_key];
    return Object.values(review.flags).every(value => value !== "not_reviewed") && review.recommendation !== "not_reviewed" && [review.r1, review.r2, review.r3].every(answer => answer.trim());
  }).length;
  by_id("progress").textContent = `${questions_done} / ${packet.questions.length} guided answers recorded; ${reviews_done} / ${candidates.length} candidate reviews complete. Completion is not a correctness score.`;
}
function formatted(value, digits = 3) { return value === null ? "Not supplied" : Number(value).toFixed(digits); }
function value_with_error(value, error) {
  return value === null ? "Not supplied" : `${formatted(value)} ± ${formatted(error)}`;
}
function select_object(key) {
  current_key = key;
  const object = packet.objects.find(item => item.object_key === key);
  const gaia = object.gaia;
  for (const button of by_id("object_navigation").children) button.setAttribute("aria-pressed", String(button.dataset.object_key === key));
  by_id("object_role").textContent = object.role;
  by_id("object_name").textContent = object.name;
  by_id("object_position").textContent = `RA ${formatted(gaia.ra, 8)}° / Dec ${formatted(gaia.dec, 8)}° / ICRS, J${formatted(gaia.ref_epoch, 1)}`;
  by_id("source_identifier").textContent = `Source ID ${object.source_id}`;
  by_id("object_caveat").textContent = object.caveat;
  by_id("snapshot_date").textContent = `Snapshot: ${packet.gaia_retrieval.snapshot_date_utc.slice(0,10)} UTC. Source identifiers are stored as text.`;
  by_id("external_checks").textContent = object.external_catalog_checks;
  by_id("catalog_rows").replaceChildren();
  const measurements = [["G magnitude", formatted(gaia.phot_g_mean_mag)], ["BP-RP color", formatted(gaia.bp_rp)],
    ["Parallax (mas)", value_with_error(gaia.parallax, gaia.parallax_error)], ["pmra (mas/year)", value_with_error(gaia.pmra, gaia.pmra_error)],
    ["pmdec (mas/year)", value_with_error(gaia.pmdec, gaia.pmdec_error)], ["Raw flux excess C", formatted(gaia.phot_bp_rp_excess_factor)],
    ["RUWE", formatted(gaia.ruwe)], ["Excess noise (mas)", formatted(gaia.astrometric_excess_noise)]];
  for (const [label, value] of measurements) {
    const row = document.createElement("tr"); row.append(text_element("th", label), text_element("td", value));
    by_id("catalog_rows").append(row);
  }
  by_id("images").replaceChildren(); by_id("provenance").replaceChildren();
  by_id("provenance").append(text_element("p", object.provenance), text_element("p", `${object.host}. ${object.distance_mpc === null ? "No host distance assigned." : `Exercise distance ${object.distance_mpc} Mpc.`} ${object.distance_basis}`));
  for (const [scale, image] of Object.entries(object.images)) {
    const figure = document.createElement("figure"); const frame = text_element("div", "", "image_frame");
    if (image.content_status === "nonuniform") {
      const photo = document.createElement("img"); photo.src = image.data_url;
      photo.alt = `${object.name}: ${scale} Legacy Survey DR11 cutout, ${image.field_width_arcsec} arcseconds per side`;
      const marker = text_element("span", "", "position_marker"); marker.setAttribute("aria-hidden", "true");
      const scale_length = scale === "close" ? 5 : 40;
      const bar = text_element("span", "", "scale_bar"); bar.style.width = `${100 * scale_length / image.field_width_arcsec}%`;
      bar.append(text_element("span", `${scale_length} arcsec`)); bar.setAttribute("aria-hidden", "true");
      frame.append(photo, marker, bar);
    } else frame.append(text_element("p", "Unavailable image / placeholder response", "unavailable_image"));
    const caption = text_element("figcaption", `${scale === "close" ? "Close" : "Context"} / ${image.field_width_arcsec.toFixed(3)} arcsec square / ${image.pixel_scale_arcsec} arcsec per pixel`);
    const credit = text_element("a", "Legacy Surveys / D. Lang (Perimeter Institute)");
    credit.href = "https://www.legacysurvey.org/acknowledgment/";
    caption.append(document.createElement("br"), credit);
    figure.append(frame, caption);
    by_id("images").append(figure);
    by_id("provenance").append(text_element("p", `${scale}: ${image.layer}; ${image.size_pixels} pixels square; retrieved ${image.retrieved_utc.slice(0,10)} UTC; content ${image.content_status}; SHA-256 ${image.sha256}.`));
  }
  by_id("object_links").replaceChildren();
  for (const [label, url] of [["Open Legacy Survey viewer ↗", object.viewer_url], ["Original paper / source ↗", object.paper_url], ["Open Gaia Archive ↗", "https://gea.esac.esa.int/archive/"]]) {
    const link = text_element("a", label); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; by_id("object_links").append(link);
  }
  render_review(); render_plot();
}
function render_review() {
  const object = packet.objects.find(item => item.object_key === current_key);
  const review = state.reviews[current_key];
  by_id("review_heading").textContent = `Your review: ${object.name}`;
  by_id("review_flags").replaceChildren();
  for (const field of packet.review_fields) {
    const label = text_element("label", field.label); const select = document.createElement("select");
    select.id = `flag_${field.key}`; label.htmlFor = select.id;
    for (const value of flag_values) { const option = text_element("option", readable(value)); option.value = value; select.append(option); }
    select.value = review.flags[field.key]; select.addEventListener("change", () => { state.reviews[current_key].flags[field.key] = select.value; persist(); });
    label.append(select); by_id("review_flags").append(label);
  }
  by_id("review_responses").replaceChildren();
  for (const [key, prompt] of [["r1", "R1 / Image evidence and uncertainty"], ["r2", "R2 / Astrometry: values, errors, missing data"], ["r3", "R3 / Recommendation reason and next evidence"]]) {
    const label = text_element("label", prompt); const area = document.createElement("textarea"); area.id = key; area.maxLength = 6000; area.value = review[key]; label.htmlFor = key;
    area.addEventListener("input", () => { state.reviews[current_key][key] = area.value; persist(); }); label.append(area); by_id("review_responses").append(label);
  }
  by_id("recommendation").value = review.recommendation;
}
function render_questions() {
  by_id("questions").replaceChildren();
  for (const question of packet.questions) {
    const wrapper = text_element("div", "", "question"); const label = document.createElement("label"); label.htmlFor = question.key;
    label.append(text_element("strong", question.key.toUpperCase()), document.createTextNode(question.prompt));
    const area = document.createElement("textarea"); area.id = question.key; area.maxLength = 6000; area.value = state.answers[question.key];
    area.addEventListener("input", () => { state.answers[question.key] = area.value; persist(); }); wrapper.append(label, area); by_id("questions").append(wrapper);
  }
}
const svg_namespace = "http://www.w3.org/2000/svg";
function svg_element(tag, attributes, text = "") {
  const element = document.createElementNS(svg_namespace, tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  element.textContent = text; return element;
}
function render_size() {
  const distance = Number(by_id("distance_slider").value); const radius = 206265 * 24.2 / (distance * 1000000);
  by_id("distance_value").textContent = distance.toFixed(1);
  by_id("angular_value").textContent = `Half-light radius ${radius.toFixed(3)} arcsec / diameter ${(2*radius).toFixed(3)} arcsec`;
  const svg = by_id("size_ruler"); svg.replaceChildren();
  const items = [[2*radius,"Hypothetical half-light diameter", "#126456"],[0.0589,"Along-scan pixel", "#74847a"],[0.1768,"Across-scan pixel", "#74847a"],[0.23,"Onboard pair separation: along", "#95451b"],[0.70,"Onboard pair separation: across", "#95451b"]];
  for (const [index, [length, label, color]] of items.entries()) {
    const y = 30 + index*39; svg.append(svg_element("text", {x:15,y:y+4,"font-size":12}, label));
    svg.append(svg_element("line", {x1:295,y1:y,x2:295+length*105,y2:y,stroke:color,"stroke-width":7}));
    svg.append(svg_element("text", {x:570,y:y+4,"font-size":12,"text-anchor":"end"}, `${length.toFixed(3)}″`));
  }
}
function render_plot() {
  const svg = by_id("comparison_plot"); svg.replaceChildren();
  const minimum_g = Math.floor(Math.min(...packet.objects.map(object => object.gaia.phot_g_mean_mag))) - .5;
  const maximum_g = Math.ceil(Math.max(...packet.objects.map(object => object.gaia.phot_g_mean_mag))) + .5;
  const maximum_c = Math.ceil(Math.max(...packet.objects.map(object => object.gaia.phot_bp_rp_excess_factor)) / 2)*2;
  const x = magnitude => 75+(magnitude-minimum_g)/(maximum_g-minimum_g)*580;
  const y = excess => 285-excess/maximum_c*245;
  svg.append(svg_element("line", {x1:75,y1:40,x2:75,y2:285,stroke:"#879b90"}),svg_element("line", {x1:75,y1:285,x2:655,y2:285,stroke:"#879b90"}));
  for (let value=Math.ceil(minimum_g);value<maximum_g;value++) svg.append(svg_element("text", {x:x(value),y:308,"text-anchor":"middle","font-size":12},String(value)));
  for (let value=0;value<=maximum_c;value+=2) {
    svg.append(svg_element("line",{x1:75,x2:655,y1:y(value),y2:y(value),stroke:"#e1e6db"}));
    svg.append(svg_element("text", {x:60,y:y(value)+4,"text-anchor":"end","font-size":12},String(value)));
  }
  svg.append(svg_element("text",{x:360,y:342,"text-anchor":"middle","font-size":14},"Gaia G magnitude / brighter to the left"),svg_element("text",{x:20,y:165,transform:"rotate(-90 20 165)","text-anchor":"middle","font-size":13},"Raw flux excess C"));
  const colors = {confirmed:"#126456",candidate:"#95451b",foreground_comparison:"#235d84",boundary_case:"#73756e"};
  for (const object of packet.objects) {
    const point = svg_element("circle", {cx:x(object.gaia.phot_g_mean_mag),cy:y(object.gaia.phot_bp_rp_excess_factor),r:object.object_key===current_key?9:6,fill:colors[object.classification],stroke:object.object_key===current_key?"#233c3a":"white","stroke-width":2,tabindex:0,role:"button","aria-label":`Inspect ${object.name}`,class:"plot_point"});
    point.append(svg_element("title",{},`${object.name}: G ${object.gaia.phot_g_mean_mag.toFixed(3)}, C ${object.gaia.phot_bp_rp_excess_factor.toFixed(3)}`));
    point.addEventListener("click",()=>select_object(object.object_key));
    point.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();select_object(object.object_key);}}); svg.append(point);
  }
}
function report_text() {
  const lines = ["A STAR IN DISGUISE? - STUDENT EVIDENCE", `Student/group: ${state.student_identifier || "Not recorded"}`, `Packet: ${state.packet_version}`, `Snapshot digest: ${state.packet_sha256}`, "Unadjudicated observations, not confirmation.", ""];
  for (const question of packet.questions) lines.push(`${question.key.toUpperCase()}. ${question.prompt}`,state.answers[question.key]||"Not answered"," ");
  for (const object of packet.objects) {
    const review = state.reviews[object.object_key]; lines.push(`${object.name} / ${object.role}`,`Gaia source ID: ${object.source_id}`);
    for (const field of packet.review_fields) lines.push(`${field.label}: ${readable(review.flags[field.key])}`);
    lines.push(`R1: ${review.r1||"Not answered"}`,`R2: ${review.r2||"Not answered"}`,`R3: ${review.r3||"Not answered"}`,`Recommendation: ${readable(review.recommendation)}`, " ");
  }
  return lines.join("\n");
}
function download(content, suffix, mime) {
  const url = URL.createObjectURL(new Blob([content], {type:mime})); const link=document.createElement("a");
  const identifier = state.student_identifier.replace(/[^a-zA-Z0-9_-]/g,"_").slice(0,60) || "student";
  link.href=url; link.download=`ucd_answers_${identifier}.${suffix}`; document.body.append(link); link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000); exported=true;
  by_id("save_status").textContent="Download requested. Check your Downloads folder; nothing has been uploaded. JSON is required to resume.";
}
function render_print() {
  by_id("print_summary").replaceChildren(text_element("h1","A star in disguise?"),text_element("pre",report_text()));
}
by_id("student_identifier").addEventListener("input",()=>{state.student_identifier=by_id("student_identifier").value;persist();});
by_id("recommendation").addEventListener("change",()=>{state.reviews[current_key].recommendation=by_id("recommendation").value;persist();});
by_id("show_marker").addEventListener("change",()=>by_id("images").classList.toggle("hide_marker",!by_id("show_marker").checked));
by_id("distance_slider").addEventListener("input",render_size);
by_id("export_json").addEventListener("click",()=>download(JSON.stringify(state,null,2),"json","application/json"));
by_id("export_text").addEventListener("click",()=>download(report_text(),"txt","text/plain;charset=utf-8"));
by_id("print_answers").addEventListener("click",()=>{render_print();window.print();});
window.addEventListener("beforeprint",render_print);
by_id("import_answers").addEventListener("change",async event=>{
  const file=event.target.files[0];if(!file)return;
  try {if(file.size>1000000)throw new Error("Answer file is too large."); const incoming=validate_state(JSON.parse(await file.text()));state=incoming;by_id("student_identifier").value=state.student_identifier;render_questions();select_object(current_key);persist();by_id("save_status").textContent="Answers imported. Review them, then export again after changes.";}
  catch(error){by_id("save_status").textContent=`Import rejected: ${error.message} Your existing answers were kept.`;}
  event.target.value="";
});
window.addEventListener("beforeunload",event=>{if(!exported&&(state.student_identifier||Object.values(state.answers).some(value=>value))){event.preventDefault();event.returnValue="";}});
try {const stored=localStorage.getItem(storage_key);if(stored)state=validate_state(JSON.parse(stored));}catch{storage_available=false;}
for(const object of packet.objects){const button=text_element("button",object.name);button.dataset.object_key=object.object_key;button.addEventListener("click",()=>select_object(object.object_key));by_id("object_navigation").append(button);}
by_id("student_identifier").value=state.student_identifier;render_questions();select_object(current_key);render_size();update_progress();
if(!storage_available)by_id("save_status").textContent="Browser storage unavailable. Export a file to save before closing.";
by_id("packet_credit").textContent=`Packet ${packet.packet_version}; Gaia snapshot ${packet.gaia_retrieval.snapshot_date_utc.slice(0,10)} UTC; fingerprint ${packet.packet_sha256.slice(0,16)}. ${packet.selection_note}`;
