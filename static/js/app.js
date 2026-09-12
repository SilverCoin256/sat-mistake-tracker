// Global variables
let subtopicsList = [];
let currentImageBase64 = null;      // display-res (1400px) — normal single-question flow
let currentPageImageBase64 = null;  // higher-res (2200px) — full-page circled-question flow
let cfg = null;                     // cached /config payload, for populating per-card selects
let pageQueue = [];                 // [{ id, cardEl, image }] currently pending review/save

const chkPageMode = document.getElementById("chk-page-mode");
const pageResults = document.getElementById("page-results");
const pageResultsSubtitle = document.getElementById("page-results-subtitle");
const pageCardsEl = document.getElementById("page-cards");
const btnSaveAll = document.getElementById("btn-save-all");
const saveAllSpinner = document.getElementById("save-all-spinner");
const saveAllBtnText = document.getElementById("save-all-btn-text");

// Manual-only Error Type: user had no approach to the question.
const UNSURE_OPTION = "Unsure — Didn't Know How to Solve";

// DOM Elements
const statusBadge = document.getElementById("status-badge");
const btnSettings = document.getElementById("btn-settings");
const settingsModal = document.getElementById("settings-modal");
const modalClose = document.getElementById("modal-close");
const btnSaveKey = document.getElementById("btn-save-key");
const inputApiKey = document.getElementById("input-api-key");

const dropZone = document.getElementById("drop-zone");
const imagePreview = document.getElementById("image-preview");
const btnGrabClipboard = document.getElementById("btn-grab-clipboard");
const btnAnalyze = document.getElementById("btn-analyze");
const btnSubmit = document.getElementById("btn-submit");
const mistakeForm = document.getElementById("mistake-form");

const alertBanner = document.getElementById("alert-banner");
const alertText = document.getElementById("alert-text");
const alertClose = document.getElementById("alert-close");

// Form Fields
const fieldSection = document.getElementById("field-section");
const selectCorrect = document.getElementById("select-correct");
const fieldCorrect = document.getElementById("field-correct");
const selectYours = document.getElementById("select-yours");
const fieldYours = document.getElementById("field-yours");
const fieldTopic = document.getElementById("field-topic");
const fieldSubtopic = document.getElementById("field-subtopic");
const fieldQType = document.getElementById("field-qtype");
const fieldErrorType = document.getElementById("field-error-type");
const fieldRootCause = document.getElementById("field-root-cause");
const fieldFixStrategy = document.getElementById("field-fix-strategy");
const fieldTime = document.getElementById("field-time");
const fieldRetest = document.getElementById("field-retest");
const fieldNotes = document.getElementById("field-notes");

const analyzeSpinner = document.getElementById("analyze-spinner");
const analyzeBtnText = document.getElementById("analyze-btn-text");
const saveSpinner = document.getElementById("save-spinner");
const saveBtnText = document.getElementById("save-btn-text");

// Initialize application
window.addEventListener("DOMContentLoaded", () => {
    loadConfig();
    setupEventListeners();
    setupAnswerSync();
});

// Setup input combination (Dropdown + Text input)
function setupAnswerSync() {
    // Correct Answer syncing
    selectCorrect.addEventListener("change", () => {
        if (selectCorrect.value === "other") {
            fieldCorrect.value = "";
            fieldCorrect.focus();
            fieldCorrect.style.display = "block";
        } else {
            fieldCorrect.value = selectCorrect.value;
            fieldCorrect.style.display = "none";
        }
    });

    fieldCorrect.addEventListener("input", () => {
        const val = fieldCorrect.value.toUpperCase();
        if (["A", "B", "C", "D"].includes(val)) {
            selectCorrect.value = val;
            fieldCorrect.style.display = "none";
            fieldCorrect.value = val;
        } else {
            selectCorrect.value = "other";
            fieldCorrect.style.display = "block";
        }
    });

    // Default: Hide text fields until needed (or keep them beside, but styled nicely)
    fieldCorrect.style.display = "none";

    // Your Answer syncing
    selectYours.addEventListener("change", () => {
        if (selectYours.value === "other") {
            fieldYours.value = "";
            fieldYours.focus();
            fieldYours.style.display = "block";
        } else {
            fieldYours.value = selectYours.value;
            fieldYours.style.display = "none";
        }
    });

    fieldYours.addEventListener("input", () => {
        const val = fieldYours.value.toUpperCase();
        if (["A", "B", "C", "D"].includes(val)) {
            selectYours.value = val;
            fieldYours.style.display = "none";
            fieldYours.value = val;
        } else {
            selectYours.value = "other";
            fieldYours.style.display = "block";
        }
    });

    fieldYours.style.display = "none";
}

// Fetch configuration from Flask backend
function loadConfig() {
    fetch("/config")
        .then(res => res.json())
        .then(data => {
            cfg = data;
            subtopicsList = data.subtopics;
            
            // Populate select menus
            populateSelect(fieldTopic, data.topics);
            populateSelect(fieldQType, data.question_types);
            populateSelect(fieldErrorType, data.error_types);
            populateSelect(fieldRootCause, data.root_causes);
            populateSelect(fieldFixStrategy, data.fix_strategies);

            // Add the manual "Unsure how to solve" option just after the placeholder.
            const unsureOpt = document.createElement("option");
            unsureOpt.value = UNSURE_OPTION;
            unsureOpt.textContent = UNSURE_OPTION;
            fieldErrorType.insertBefore(unsureOpt, fieldErrorType.options[1] || null);
            
            // Update API status
            if (data.has_api_key) {
                statusBadge.className = "status-badge ready";
                statusBadge.querySelector(".status-text").textContent = "API Key Active";
            } else {
                statusBadge.className = "status-badge missing";
                statusBadge.querySelector(".status-text").textContent = "Missing API Key";
                showAlert("Gemini API Key is missing. Please configure it in Settings.", "warning");
                settingsModal.classList.remove("hidden");
            }
        })
        .catch(err => {
            console.error("Error loading config:", err);
            showAlert("Failed to connect to local server backend.", "error");
        });
}

// Slice of the flat subtopics list that belongs to a given Topic.
// Order/boundaries mirror constants.py's SUBTOPICS grouping.
function subtopicsForTopic(topic) {
    const ranges = {
        "Algebra": [0, 13],
        "Advanced Math": [13, 29],
        "Problem Solving & Data Analysis": [29, 46],
        "Geometry & Trigonometry": [46, 63],
        "Information & Ideas": [63, 72],
        "Craft & Structure": [72, 79],
        "Expression of Ideas": [79, 88],
        "Standard English Conventions": [88, undefined],
    };
    const r = ranges[topic];
    return r ? subtopicsList.slice(r[0], r[1]) : [];
}

// Helper: Populate select element options
function populateSelect(element, items) {
    // Keep placeholder option
    const placeholder = element.options[0];
    element.innerHTML = "";
    element.appendChild(placeholder);
    
    items.forEach(item => {
        const opt = document.createElement("option");
        opt.value = item;
        opt.textContent = item;
        element.appendChild(opt);
    });
}

// Setup Event Listeners
function setupEventListeners() {
    // Settings modal toggle
    btnSettings.addEventListener("click", () => {
        settingsModal.classList.remove("hidden");
    });
    
    modalClose.addEventListener("click", () => {
        settingsModal.classList.add("hidden");
    });
    
    // Save API key
    btnSaveKey.addEventListener("click", () => {
        const key = inputApiKey.value.trim();
        if (!key) {
            showAlert("API Key cannot be blank", "error");
            return;
        }
        
        fetch("/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: key })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert("Settings saved successfully!", "success");
                settingsModal.classList.add("hidden");
                loadConfig();
            } else {
                showAlert(data.error || "Failed to save settings", "error");
            }
        })
        .catch(err => {
            showAlert("Error connecting to settings server", "error");
        });
    });

    // Filtering Subtopics based on Topic selection
    fieldTopic.addEventListener("change", () => {
        populateSelect(fieldSubtopic, subtopicsForTopic(fieldTopic.value));
    });

    // Drag & drop images — handles files dragged from Finder AND images
    // dragged straight out of a web page. The whole window is a drop target.
    function loadFromDataTransfer(dt) {
        // 1) Dropped image file(s) from Finder
        if (dt.files && dt.files.length && dt.files[0].type.startsWith("image/")) {
            handleImageFile(dt.files[0]);
            return;
        }
        // 2) Image dragged as an item (file kind)
        if (dt.items) {
            for (const it of dt.items) {
                if (it.kind === "file" && it.type.startsWith("image/")) {
                    const f = it.getAsFile();
                    if (f) { handleImageFile(f); return; }
                }
            }
        }
        // 3) Image dragged from a web page → resolve the URL and fetch it
        let url = dt.getData("text/uri-list") || dt.getData("text/plain") || "";
        if (!url) {
            const html = dt.getData("text/html");
            const m = html && html.match(/<img[^>]+src=["']([^"']+)["']/i);
            if (m) url = m[1];
        }
        if (url) {
            showAlert("Loading dragged image…", "success");
            fetch(url)
                .then(r => r.blob())
                .then(blob => {
                    if (!blob.type.startsWith("image/")) throw new Error("not an image");
                    handleImageFile(blob);
                })
                .catch(() => showAlert("Couldn't load that dragged image (the site blocked it). Save it and drag the file, or copy it and press Cmd+V.", "error"));
            return;
        }
        showAlert("Drop an image file, or an image dragged from a web page.", "error");
    }

    ["dragenter", "dragover"].forEach(ev =>
        dropZone.addEventListener(ev, (e) => { e.preventDefault(); dropZone.classList.add("dragover"); }));
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        loadFromDataTransfer(e.dataTransfer);
    });
    // Accept drops anywhere in the window and stop Chrome from navigating to the image.
    window.addEventListener("dragover", (e) => e.preventDefault());
    window.addEventListener("drop", (e) => {
        // dropZone handles its own; guard contains() against non-Node targets (e.g. window)
        if (e.target instanceof Node && dropZone.contains(e.target)) return;
        e.preventDefault();
        loadFromDataTransfer(e.dataTransfer);
    });

    // Paste handler on drop zone & window
    window.addEventListener("paste", (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf("image") !== -1) {
                const blob = items[i].getAsFile();
                handleImageFile(blob);
                e.preventDefault();
                break;
            }
        }
    });

    dropZone.addEventListener("click", () => {
        // Trigger grab from clipboard manually as click default
        grabClipboardImage();
    });

    btnGrabClipboard.addEventListener("click", grabClipboardImage);

    // "Unsure how to solve" → disable Your Answer + Time Taken (not applicable).
    fieldErrorType.addEventListener("change", () => {
        applyUnsureMode(fieldErrorType.value === UNSURE_OPTION);
    });

    // Toggle button label/behavior for full-page mode
    chkPageMode.addEventListener("change", () => {
        analyzeBtnText.textContent = chkPageMode.checked ? "Detect Circled Questions" : "Analyze with Gemini";
        if (!chkPageMode.checked) {
            pageResults.classList.add("hidden");
        }
    });

    // AI Analysis call — single question, or full-page circled-question mode
    btnAnalyze.addEventListener("click", () => {
        if (chkPageMode.checked) { analyzePage(); return; }
        if (!currentImageBase64) return;

        btnAnalyze.disabled = true;
        analyzeSpinner.classList.remove("hidden");
        analyzeBtnText.textContent = "Analyzing Image...";

        fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: currentImageBase64 })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                populateAnalysisFields(data.analysis);
                showAlert("Gemini analysis complete! Please review the logged fields below.", "success");
                btnSubmit.disabled = false;
            } else {
                showAlert(data.error || "Analysis failed.", "error");
            }
        })
        .catch(err => {
            showAlert("Error calling Gemini API backend: " + err.message, "error");
        })
        .finally(() => {
            btnAnalyze.disabled = false;
            analyzeSpinner.classList.add("hidden");
            analyzeBtnText.textContent = "Analyze with Gemini";
        });
    });

    btnSaveAll.addEventListener("click", saveAllPageCards);

    // Form Submission / Saving row to Excel
    mistakeForm.addEventListener("submit", (e) => {
        e.preventDefault();
        
        btnSubmit.disabled = true;
        saveSpinner.classList.remove("hidden");
        saveBtnText.textContent = "Writing to Excel...";
        
        const payload = {
            image: currentImageBase64,
            section: fieldSection.value,
            correct_answer: fieldCorrect.value.trim(),
            your_answer: fieldYours.value.trim(),
            topic: fieldTopic.value,
            subtopic: fieldSubtopic.value,
            question_type: fieldQType.value,
            error_type: fieldErrorType.value,
            root_cause: fieldRootCause.value,
            fix_strategy: fieldFixStrategy.value,
            time_taken: fieldTime.value.trim(),
            retest_status: fieldRetest.value,
            notes: fieldNotes.value.trim()
        };
        
        fetch("/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, "success");
                
                // Clear image preview and preview variable
                imagePreview.classList.add("hidden");
                imagePreview.src = "";
                currentImageBase64 = null;
                btnAnalyze.disabled = true;
                btnSubmit.disabled = true;
                
                // Clear specific fields but KEEP source and section for easy multi-logging
                selectCorrect.value = "";
                fieldCorrect.value = "";
                fieldCorrect.style.display = "none";
                selectYours.value = "";
                fieldYours.value = "";
                fieldYours.style.display = "none";
                fieldTopic.value = "";
                fieldSubtopic.innerHTML = '<option value="" disabled selected>Select Subtopic</option>';
                fieldQType.value = "";
                fieldErrorType.value = "";
                fieldRootCause.value = "";
                fieldFixStrategy.value = "";
                fieldTime.value = "";
                fieldNotes.value = "";
                applyUnsureMode(false);  // re-enable Your Answer + Time Taken
            } else {
                showAlert(data.error || "Failed to save mistake entry.", "error");
                btnSubmit.disabled = false;
            }
        })
        .catch(err => {
            showAlert("Server connection failed during save: " + err.message, "error");
            btnSubmit.disabled = false;
        })
        .finally(() => {
            saveSpinner.classList.add("hidden");
            saveBtnText.textContent = "Save to Excel Tracker";
        });
    });

    alertClose.addEventListener("click", () => {
        alertBanner.classList.add("hidden");
    });
}

// Downscale large screenshots so the UI, the AI upload, and the Excel embed
// stay fast. SAT text is still crisp at 1400px. Returns the original if small.
function downscaleImage(dataUrl, maxDim = 1400) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const longest = Math.max(img.width, img.height);
            if (longest <= maxDim) { resolve(dataUrl); return; }
            const scale = maxDim / longest;
            const canvas = document.createElement("canvas");
            canvas.width = Math.round(img.width * scale);
            canvas.height = Math.round(img.height * scale);
            canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
            resolve(canvas.toDataURL("image/png"));
        };
        img.onerror = () => resolve(dataUrl);
        img.src = dataUrl;
    });
}

function setLoadedImage(dataUrl, pageDataUrl, msg) {
    currentImageBase64 = dataUrl;
    currentPageImageBase64 = pageDataUrl;
    imagePreview.src = dataUrl;
    imagePreview.classList.remove("hidden");
    btnAnalyze.disabled = false;
    // Allow logging without AI: Analyze is optional, manual fill always works.
    btnSubmit.disabled = false;
    showAlert(msg, "success");
}

// Convert image file to base64, downscale (two sizes — see currentPageImageBase64), preview
function handleImageFile(file) {
    const reader = new FileReader();
    reader.onload = async (e) => {
        // Full-page mode needs more resolution than the single-question flow:
        // each circled question becomes its own crop, which stays legible at
        // 2200px on the long edge even after being cropped down further.
        const [small, page] = await Promise.all([
            downscaleImage(e.target.result, 1400),
            downscaleImage(e.target.result, 2200),
        ]);
        setLoadedImage(small, page, "Screenshot loaded. Click 'Analyze with Gemini' to auto-fill, or fill the fields and Save.");
    };
    reader.readAsDataURL(file);
}

// Calls python backend to grab from OS Clipboard
function grabClipboardImage() {
    fetch("/grab-clipboard", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                Promise.all([
                    downscaleImage(data.image, 1400),
                    downscaleImage(data.image, 2200),
                ]).then(([small, page]) =>
                    setLoadedImage(small, page, "Screenshot grabbed from macOS Clipboard!"));
            } else {
                showAlert(data.error || "Could not grab image.", "warning");
            }
        })
        .catch(err => {
            showAlert("Clipboard capture API failed: " + err.message, "error");
        });
}

// When "Unsure how to solve" is the Error Type, grey out & blank the fields
// that don't apply (you never really attempted the question).
function applyUnsureMode(on) {
    // Your Answer (dropdown + text combo)
    selectYours.disabled = on;
    fieldYours.disabled = on;
    if (on) { selectYours.value = ""; fieldYours.value = ""; fieldYours.style.display = "none"; }
    // Time Taken
    fieldTime.disabled = on;
    if (on) fieldTime.value = "";
    // Visual dimming of the whole field group
    const yoursGroup = selectYours.closest(".form-group");
    const timeGroup = fieldTime.closest(".form-group");
    if (yoursGroup) yoursGroup.style.opacity = on ? "0.45" : "";
    if (timeGroup) timeGroup.style.opacity = on ? "0.45" : "";
}

// Populate UI form inputs with Gemini analysis results
function populateAnalysisFields(res) {
    if (res["Section"]) {
        fieldSection.value = res["Section"];
        // Enable correct inputs configuration based on section
    }
    
    // Correct Answer Combo
    if (res["Correct Answer"]) {
        const val = res["Correct Answer"].toString().toUpperCase().trim();
        fieldCorrect.value = val;
        if (["A", "B", "C", "D"].includes(val)) {
            selectCorrect.value = val;
            fieldCorrect.style.display = "none";
        } else {
            selectCorrect.value = "other";
            fieldCorrect.style.display = "block";
        }
    }
    
    // Your Answer Combo
    if (res["Your Answer"]) {
        const val = res["Your Answer"].toString().toUpperCase().trim();
        fieldYours.value = val;
        if (["A", "B", "C", "D"].includes(val)) {
            selectYours.value = val;
            fieldYours.style.display = "none";
        } else {
            selectYours.value = "other";
            fieldYours.style.display = "block";
        }
    }
    
    // Topic & Subtopics loading
    if (res["Topic"]) {
        fieldTopic.value = res["Topic"];
        // Fire change event to reload subtopics
        fieldTopic.dispatchEvent(new Event("change"));
        
        // Select Subtopic after it loads
        setTimeout(() => {
            if (res["Subtopic"]) {
                fieldSubtopic.value = res["Subtopic"];
            }
        }, 50);
    }
    
    if (res["Question Type"]) fieldQType.value = res["Question Type"];
    if (res["Error Type"]) fieldErrorType.value = res["Error Type"];
    if (res["Root Cause"]) fieldRootCause.value = res["Root Cause"];
    if (res["Fix Strategy"]) fieldFixStrategy.value = res["Fix Strategy"];
    if (res["Notes"]) fieldNotes.value = res["Notes"];
}

// ---- Full-page circled-question mode ----

function analyzePage() {
    if (!currentPageImageBase64) {
        showAlert("Load a page screenshot first.", "warning");
        return;
    }
    btnAnalyze.disabled = true;
    analyzeSpinner.classList.remove("hidden");
    analyzeBtnText.textContent = "Scanning for circled questions...";

    fetch("/analyze-page", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: currentPageImageBase64 })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            showAlert(data.error || "Page analysis failed.", "error");
            return;
        }
        if (!data.questions.length) {
            showAlert("No circled question numbers found on this page.", "warning");
            pageResults.classList.add("hidden");
            return;
        }
        renderPageCards(data.questions);
        showAlert(`Found ${data.questions.length} circled question${data.questions.length === 1 ? "" : "s"}. Review before saving.`, "success");
    })
    .catch(err => showAlert("Error calling Gemini API backend: " + err.message, "error"))
    .finally(() => {
        btnAnalyze.disabled = false;
        analyzeSpinner.classList.add("hidden");
        analyzeBtnText.textContent = "Detect Circled Questions";
    });
}

function renderPageCards(questions) {
    pageCardsEl.innerHTML = "";
    pageQueue = [];

    questions.forEach((q, i) => {
        const id = "pc" + i;
        const image = q.image || currentPageImageBase64;  // fall back to full page if crop failed
        const correct = (q["Correct Answer"] || "").toString();
        const yours = (q["Your Answer"] || "").toString();

        const card = document.createElement("div");
        card.className = "page-card";
        card.dataset.id = id;
        card.innerHTML = `
            <div class="page-card-head">
                <span class="qnum">Q${escapeHtml(q["Question Number"] || "?")}</span>
                <span class="status-pill">pending</span>
                <button type="button" class="page-card-remove" title="Not actually wrong — remove">&times;</button>
            </div>
            ${image ? `<img class="page-card-thumb" src="${image}">` : ""}
            <div class="split-row">
                <div class="form-group">
                    <label>Section</label>
                    <select data-field="section">
                        <option value="Math">Math</option>
                        <option value="Reading & Writing">Reading & Writing</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Topic</label>
                    <select data-field="topic"></select>
                </div>
            </div>
            <div class="form-group">
                <label>Subtopic</label>
                <select data-field="subtopic"></select>
            </div>
            <div class="split-row">
                <div class="form-group">
                    <label>Correct</label>
                    <input type="text" data-field="correct_answer" value="${escapeHtml(correct)}">
                </div>
                <div class="form-group">
                    <label>Your Answer</label>
                    <input type="text" data-field="your_answer" value="${escapeHtml(yours)}">
                </div>
            </div>
            <div class="form-group">
                <label>Question Type</label>
                <select data-field="question_type"></select>
            </div>
            <div class="form-group">
                <label>Error Type</label>
                <select data-field="error_type"></select>
            </div>
            <div class="split-row">
                <div class="form-group">
                    <label>Root Cause</label>
                    <select data-field="root_cause"></select>
                </div>
                <div class="form-group">
                    <label>Fix Strategy</label>
                    <select data-field="fix_strategy"></select>
                </div>
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea data-field="notes" rows="2">${escapeHtml(q["Notes"] || "")}</textarea>
            </div>
        `;

        // Populate selects from the same cached lists the main form uses.
        const topicSel = card.querySelector('[data-field="topic"]');
        const subtopicSel = card.querySelector('[data-field="subtopic"]');
        populateSelectPlain(topicSel, cfg.topics, q["Topic"]);
        populateSelectPlain(card.querySelector('[data-field="question_type"]'), cfg.question_types, q["Question Type"]);
        populateSelectPlain(card.querySelector('[data-field="error_type"]'), cfg.error_types, q["Error Type"]);
        populateSelectPlain(card.querySelector('[data-field="root_cause"]'), cfg.root_causes, q["Root Cause"]);
        populateSelectPlain(card.querySelector('[data-field="fix_strategy"]'), cfg.fix_strategies, q["Fix Strategy"]);
        populateSelectPlain(subtopicSel, subtopicsForTopic(q["Topic"]), q["Subtopic"]);
        topicSel.addEventListener("change", () => populateSelectPlain(subtopicSel, subtopicsForTopic(topicSel.value)));
        if (q["Section"] === "Reading & Writing") card.querySelector('[data-field="section"]').value = "Reading & Writing";

        card.querySelector(".page-card-remove").addEventListener("click", () => {
            card.remove();
            pageQueue = pageQueue.filter(x => x.id !== id);
            updatePageResultsSubtitle();
        });

        pageCardsEl.appendChild(card);
        pageQueue.push({ id, cardEl: card, image });
    });

    pageResults.classList.remove("hidden");
    updatePageResultsSubtitle();
}

// Like populateSelect but takes a plain items array + the value to preselect
// (card selects have no fixed placeholder option to preserve).
function populateSelectPlain(element, items, selected) {
    element.innerHTML = "";
    (items || []).forEach(item => {
        const opt = document.createElement("option");
        opt.value = item;
        opt.textContent = item;
        if (item === selected) opt.selected = true;
        element.appendChild(opt);
    });
}

function escapeHtml(s) {
    return (s ?? "").toString()
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function updatePageResultsSubtitle() {
    pageResultsSubtitle.textContent = pageQueue.length
        ? `${pageQueue.length} question${pageQueue.length === 1 ? "" : "s"} ready to save`
        : "All done";
}

function cardToPayload(cardEl, image) {
    const get = (f) => cardEl.querySelector(`[data-field="${f}"]`).value.trim();
    return {
        image,
        section: get("section"),
        correct_answer: get("correct_answer"),
        your_answer: get("your_answer"),
        topic: get("topic"),
        subtopic: get("subtopic"),
        question_type: get("question_type"),
        error_type: get("error_type"),
        root_cause: get("root_cause"),
        fix_strategy: get("fix_strategy"),
        time_taken: "",
        retest_status: "Not Reviewed",
        notes: get("notes"),
    };
}

// Sequential (not parallel) — keeps Excel row-append order stable and avoids
// hammering the Google Sheets API with a burst of concurrent writes.
async function saveAllPageCards() {
    if (!pageQueue.length) { showAlert("Nothing left to save.", "warning"); return; }

    btnSaveAll.disabled = true;
    saveAllSpinner.classList.remove("hidden");
    let ok = 0, failed = 0;

    for (const item of [...pageQueue]) {
        const payload = cardToPayload(item.cardEl, item.image);
        saveAllBtnText.textContent = `Saving ${ok + failed + 1} / ${pageQueue.length}...`;
        try {
            const res = await fetch("/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                ok++;
                item.cardEl.classList.add("saved");
                item.cardEl.querySelector(".status-pill").textContent = "saved";
                item.cardEl.querySelectorAll("input,select,textarea,button").forEach(el => el.disabled = true);
            } else {
                failed++;
                item.cardEl.classList.add("errored");
                item.cardEl.querySelector(".status-pill").textContent = "failed";
            }
        } catch (err) {
            failed++;
            item.cardEl.classList.add("errored");
            item.cardEl.querySelector(".status-pill").textContent = "failed";
        }
    }

    pageQueue = pageQueue.filter(item => !item.cardEl.classList.contains("saved"));
    updatePageResultsSubtitle();
    saveAllSpinner.classList.add("hidden");
    saveAllBtnText.textContent = "Save All to Tracker";
    btnSaveAll.disabled = false;
    showAlert(`Saved ${ok} question${ok === 1 ? "" : "s"}${failed ? `, ${failed} failed` : ""}.`, failed ? "warning" : "success");
}

// Show Alert Banner
function showAlert(message, type = "success") {
    alertBanner.className = `alert-banner ${type}`;
    alertText.textContent = message;
    alertBanner.classList.remove("hidden");
    
    // Auto-scroll to top to ensure user sees the banner
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
