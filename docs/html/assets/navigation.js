"use strict";

const search_input = document.getElementById("document_search");
if (search_input) {
    const entries = Array.from(document.querySelectorAll("[data_search]"));
    const groups = Array.from(document.querySelectorAll(".document_group"));
    const search_count = document.getElementById("search_count");
    const update_search = () => {
        const terms = search_input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
        let visible_count = 0;
        entries.forEach((entry) => {
            entry.hidden = !terms.every((term) => entry.getAttribute("data_search").includes(term));
            if (!entry.hidden) visible_count += 1;
        });
        groups.forEach((group) => {
            group.hidden = !Array.from(group.querySelectorAll("[data_search]")).some((entry) => !entry.hidden);
        });
        search_count.textContent = `${visible_count} of ${entries.length} documents`;
    };
    search_input.addEventListener("input", update_search);
    update_search();
}
