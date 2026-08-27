/**
 * Akasha Online Compiler — Programiz Style Client Engine
 */

(function () {
  "use strict";

  // Elements
  const codeInput = document.getElementById("code-input");
  const syntaxCode = document.getElementById("syntax-code");
  const syntaxBackdrop = document.getElementById("syntax-backdrop");
  const gutter = document.getElementById("gutter");
  const terminalOutput = document.getElementById("terminal-output");
  const execTimeEl = document.getElementById("exec-time");
  const statusText = document.getElementById("status-text");
  const exampleSelect = document.getElementById("example-select");
  const cursorPosEl = document.getElementById("cursor-pos");
  const codeStatsEl = document.getElementById("code-stats");
  const toast = document.getElementById("toast");

  const btnRun = document.getElementById("btn-run");
  const btnClearCode = document.getElementById("btn-clear-code");
  const btnCopyCode = document.getElementById("btn-copy-code");
  const btnDownload = document.getElementById("btn-download");
  const btnClearOutput = document.getElementById("btn-clear-output");
  const btnFontDec = document.getElementById("btn-font-dec");
  const btnFontInc = document.getElementById("btn-font-inc");

  let currentFontSize = 13;

  const DEFAULT_CODE = `// Akasha Online Compiler
cheppu("Hello, World!")

viluva name = "Akasha"
viluva version = 1

cheppu(f"Welcome to {name} v{version}")

// Function to calculate factorial
karyam factorial(n) {
    okavela n <= 1 { phalitham 1 }
    phalitham n * factorial(n - 1)
}

cheppu(f"5! = {factorial(5)}")
`;

  // ── Syntax Highlighter ──────────────────────────────────────────────────────

  const AKASHA_KEYWORDS = new Set([
    "cheppu", "viluva", "sthiram", "rahasyam", "okavela", "lekapothe", "mariyu",
    "prathi", "lo", "alaa", "loop", "aapu", "konasaginchu", "karyam", "phalitham",
    "muppu", "tirugu", "sthithi", "nijam", "abaddham", "shunyam", "rachana",
    "enum", "lakshanam", "adugu", "nerpu", "asura", "digumathi", "egumathi",
    "vethuku", "default", "pariksha", "pattu", "antham", "visuru", "async", "aagu"
  ]);

  const AKASHA_TYPES = new Set([
    "Sankhya", "Dasamsam", "Padam", "Nijam", "Shunyam", "Vikalpa", "Phalitham",
    "Gumpu", "Naksha", "Janta", "Byte", "Patrika"
  ]);

  const AKASHA_BUILTINS = new Set([
    "parimaanam", "type_of", "range", "adugu", "Undu", "Ledu", "Sari", "Tappu"
  ]);

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function highlight(code) {
    const lines = code.split("\n");
    const highlighted = lines.map((line) => {
      let result = "";
      let i = 0;
      const len = line.length;

      while (i < len) {
        // Comments (// or --)
        if (line.slice(i, i + 2) === "--" || line.slice(i, i + 2) === "//") {
          result += `<span class="hl-comment">${escapeHtml(line.slice(i))}</span>`;
          break;
        }

        // F-strings
        if (line[i] === "f" && (line[i + 1] === '"' || line[i + 1] === "'")) {
          const q = line[i + 1];
          let end = i + 2;
          while (end < len && line[end] !== q) {
            if (line[end] === "\\" && end + 1 < len) end += 2;
            else end++;
          }
          if (end < len) end++;
          result += `<span class="hl-fstr">${escapeHtml(line.slice(i, end))}</span>`;
          i = end;
          continue;
        }

        // Normal strings
        if (line[i] === '"' || line[i] === "'") {
          const q = line[i];
          let end = i + 1;
          while (end < len && line[end] !== q) {
            if (line[end] === "\\" && end + 1 < len) end += 2;
            else end++;
          }
          if (end < len) end++;
          result += `<span class="hl-str">${escapeHtml(line.slice(i, end))}</span>`;
          i = end;
          continue;
        }

        // Numbers
        if (/\d/.test(line[i])) {
          let end = i;
          if (line.slice(i, i + 2).toLowerCase() === "0x") {
            end += 2;
            while (end < len && /[0-9a-fA-F_]/.test(line[end])) end++;
          } else {
            while (end < len && /[0-9._]/.test(line[end])) end++;
          }
          result += `<span class="hl-num">${escapeHtml(line.slice(i, end))}</span>`;
          i = end;
          continue;
        }

        // Identifiers / Keywords
        if (/[a-zA-Z_]/.test(line[i])) {
          let end = i;
          while (end < len && /[a-zA-Z0-9_]/.test(line[end])) end++;
          const word = line.slice(i, end);

          if (AKASHA_KEYWORDS.has(word)) {
            result += `<span class="hl-kw">${escapeHtml(word)}</span>`;
          } else if (AKASHA_TYPES.has(word)) {
            result += `<span class="hl-type">${escapeHtml(word)}</span>`;
          } else if (AKASHA_BUILTINS.has(word)) {
            result += `<span class="hl-builtin">${escapeHtml(word)}</span>`;
          } else if (end < len && line[end] === "(") {
            result += `<span class="hl-fn">${escapeHtml(word)}</span>`;
          } else {
            result += escapeHtml(word);
          }
          i = end;
          continue;
        }

        result += escapeHtml(line[i]);
        i++;
      }

      return result;
    });

    return highlighted.join("\n") + "\n";
  }

  // ── Editor Sync ─────────────────────────────────────────────────────────────

  function updateEditor() {
    const code = codeInput.value;
    syntaxCode.innerHTML = highlight(code);
    updateGutter();
    updateStats();
    localStorage.setItem("akasha_code_clean", code);
  }

  function updateGutter() {
    const count = codeInput.value.split("\n").length;
    let html = "";
    for (let i = 1; i <= count; i++) {
      html += `<div class="gutter-line">${i}</div>`;
    }
    gutter.innerHTML = html;
  }

  function updateStats() {
    const text = codeInput.value;
    const lines = text.split("\n").length;
    codeStatsEl.textContent = `${lines} lines`;

    const pos = codeInput.selectionStart;
    const sub = text.slice(0, pos);
    const lineNum = sub.split("\n").length;
    const colNum = pos - sub.lastIndexOf("\n");
    cursorPosEl.textContent = `Line ${lineNum}, Column ${colNum}`;
  }

  codeInput.addEventListener("scroll", () => {
    syntaxBackdrop.scrollTop = codeInput.scrollTop;
    syntaxBackdrop.scrollLeft = codeInput.scrollLeft;
    gutter.scrollTop = codeInput.scrollTop;
  });

  codeInput.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = codeInput.selectionStart;
      const end = codeInput.selectionEnd;
      codeInput.value = codeInput.value.substring(0, start) + "    " + codeInput.value.substring(end);
      codeInput.selectionStart = codeInput.selectionEnd = start + 4;
      updateEditor();
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      runCode();
    } else if (e.key === "{" || e.key === "(" || e.key === "[" || e.key === '"' || e.key === "'") {
      const pairs = { "{": "}", "(": ")", "[": "]", '"': '"', "'": "'" };
      const close = pairs[e.key];
      const start = codeInput.selectionStart;
      const end = codeInput.selectionEnd;
      if (start !== end) {
        e.preventDefault();
        const selected = codeInput.value.substring(start, end);
        codeInput.value = codeInput.value.substring(0, start) + e.key + selected + close + codeInput.value.substring(end);
        codeInput.selectionStart = start + 1;
        codeInput.selectionEnd = end + 1;
        updateEditor();
      }
    }
  });

  codeInput.addEventListener("input", updateEditor);
  codeInput.addEventListener("click", updateStats);
  codeInput.addEventListener("keyup", updateStats);

  // ── Toast Helper ────────────────────────────────────────────────────────────

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2500);
  }

  // ── Execution Logic ─────────────────────────────────────────────────────────

  async function runCode() {
    const code = codeInput.value.trim();
    if (!code) {
      showToast("Editor is empty");
      return;
    }

    statusText.textContent = "Running...";
    terminalOutput.textContent = "Compiling and running...";

    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();
      execTimeEl.textContent = `${data.execution_time_ms || 0}ms`;

      if (data.success) {
        statusText.textContent = "Success";
        terminalOutput.className = "terminal";
        terminalOutput.textContent = data.output || "[Program finished with no output]";
      } else {
        statusText.textContent = "Error";
        terminalOutput.className = "terminal terminal-error";
        let errMsg = data.error?.message || "Execution error";
        if (data.output) {
          terminalOutput.textContent = `${data.output}\n${errMsg}`;
        } else {
          terminalOutput.textContent = errMsg;
        }
      }
    } catch (e) {
      statusText.textContent = "Connection Error";
      terminalOutput.className = "terminal terminal-error";
      terminalOutput.textContent = `Error connecting to backend: ${e.message}`;
    }
  }

  // ── Examples Loader ─────────────────────────────────────────────────────────

  async function loadExamples() {
    try {
      const response = await fetch("/api/examples");
      const data = await response.json();
      if (data.examples && data.examples.length > 0) {
        exampleSelect.innerHTML = '<option value="">-- Choose Sample --</option>' +
          data.examples.map(ex => `<option value="${ex.id}">${escapeHtml(ex.title)}</option>`).join("");

        exampleSelect.addEventListener("change", (e) => {
          const found = data.examples.find(ex => ex.id === e.target.value);
          if (found) {
            codeInput.value = found.code;
            updateEditor();
            showToast(`Loaded: ${found.title}`);
          }
        });
      }
    } catch (e) {
      console.warn("Error loading samples:", e);
    }
  }

  // ── Action Buttons ──────────────────────────────────────────────────────────

  btnRun.addEventListener("click", runCode);

  btnClearCode.addEventListener("click", () => {
    codeInput.value = "";
    updateEditor();
    showToast("Editor cleared");
  });

  btnCopyCode.addEventListener("click", () => {
    navigator.clipboard.writeText(codeInput.value).then(() => {
      showToast("Code copied to clipboard");
    });
  });

  btnDownload.addEventListener("click", () => {
    const blob = new Blob([codeInput.value], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "main.akasha";
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded main.akasha");
  });

  btnClearOutput.addEventListener("click", () => {
    terminalOutput.textContent = "";
    statusText.textContent = "Ready";
    execTimeEl.textContent = "";
  });

  btnFontInc.addEventListener("click", () => {
    if (currentFontSize < 20) {
      currentFontSize += 1;
      applyFontSize();
    }
  });

  btnFontDec.addEventListener("click", () => {
    if (currentFontSize > 11) {
      currentFontSize -= 1;
      applyFontSize();
    }
  });

  function applyFontSize() {
    codeInput.style.fontSize = `${currentFontSize}px`;
    syntaxBackdrop.style.fontSize = `${currentFontSize}px`;
    gutter.style.fontSize = `${currentFontSize}px`;
  }

  // ── Init ────────────────────────────────────────────────────────────────────

  function init() {
    const saved = localStorage.getItem("akasha_code_clean");
    codeInput.value = saved || DEFAULT_CODE;
    updateEditor();
    loadExamples();
  }

  init();
})();
