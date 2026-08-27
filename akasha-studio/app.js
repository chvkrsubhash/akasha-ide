/**
 * Akasha Studio — Desktop Application Engine
 * ==========================================
 * Manages editor tabs, live syntax highlighting, compiler API calls,
 * bytecode disassembly, terminal streaming, and command palette.
 */

// ── Built-in Sample Programs ──────────────────────────────────────────────────

const SAMPLES = [
  {
    id: "hello.akasha",
    name: "01. Hello World",
    code: `-- Hello World in Akasha
cheppu("Namaste, World!")
cheppu("Welcome to the Telugu-inspired programming language.")
`
  },
  {
    id: "variables.akasha",
    name: "02. Variables & Math",
    code: `-- Variables (viluva) and Constants (sthiram)
viluva peru = "Subhash"
viluva vayasu = 22
sthiram PI = 3.14159

cheppu(f"Peru: {peru}, Vayasu: {vayasu}")

viluva a = 20
viluva b = 6
cheppu(f"a + b = {a + b}")
cheppu(f"a * b = {a * b}")
cheppu(f"a / b = {a / b}")
`
  },
  {
    id: "conditions.akasha",
    name: "03. Conditionals (okavela)",
    code: `-- Conditional Logic
viluva score = 88

okavela score >= 90 {
    cheppu("Grade: A+ (Uttamam)")
} mariyu score >= 80 {
    cheppu("Grade: A (Baga undi)")
} lekapothe {
    cheppu("Grade: Needs practice")
}
`
  },
  {
    id: "loops.akasha",
    name: "04. Loops & Iterations",
    code: `-- For-each (prathi ... lo) and While (alaa) loops
cheppu("Counting 1 to 5:")
prathi i lo 1..6 {
    cheppu(f"  Step: {i}")
}

viluva count = 3
alaa count > 0 {
    cheppu(f"  Countdown: {count}")
    count = count - 1
}
cheppu("Blast off!")
`
  },
  {
    id: "fibonacci.akasha",
    name: "05. Recursive Fibonacci",
    code: `-- Recursive Fibonacci in Akasha
karyam fib(n: Sankhya): Sankhya {
    okavela n <= 1 { phalitham n }
    phalitham fib(n - 1) + fib(n - 2)
}

cheppu("Fibonacci sequence (0..8):")
prathi i lo 0..9 {
    cheppu(f"  fib({i}) = {fib(i)}")
}
`
  },
  {
    id: "bubble_sort.akasha",
    name: "06. Bubble Sort Algorithm",
    code: `-- Bubble Sort Algorithm
karyam bubble_sort(arr) {
    viluva n = parimaanam(arr)
    prathi i lo 0..n {
        prathi j lo 0..(n - i - 1) {
            okavela arr[j] > arr[j + 1] {
                viluva temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
            }
        }
    }
    phalitham arr
}

viluva dataset = [64, 34, 25, 12, 22, 11, 90]
cheppu(f"Before sorting: {dataset}")
viluva sorted_data = bubble_sort(dataset)
cheppu(f"After sorting:  {sorted_data}")
`
  },
  {
    id: "closures.akasha",
    name: "07. Higher-Order Closures",
    code: `-- Higher-order functions & lambdas (muppu)
viluva numbers = [1, 2, 3, 4, 5, 6, 7, 8]

viluva evens = numbers.filter(muppu(x) => x % 2 == 0)
cheppu(f"Even numbers: {evens}")

viluva squares = numbers.map(muppu(x) => x * x)
cheppu(f"Squares:      {squares}")

viluva total = numbers.reduce(0, muppu(acc, x) => acc + x)
cheppu(f"Sum total:    {total}")
`
  }
];

// ── Application State ─────────────────────────────────────────────────────────

let tabs = [];
let activeTabId = null;
let tabCounter = 1;

const textarea = document.getElementById('editor-textarea');
const highlightLayer = document.getElementById('editor-highlight');
const gutter = document.getElementById('editor-gutter');
const statusCursor = document.getElementById('status-cursor');
const statusMsg = document.getElementById('status-msg');
const statusErrors = document.getElementById('status-errors');
const crumbFilename = document.getElementById('crumb-filename');

// ── Initialization ───────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  initSamplesSidebar();
  loadWorkspaceFiles();
  setupEditorEvents();
  setupResizers();
  setupKeyboardShortcuts();

  // Open default starter file
  openTab({
    id: 'tab-main',
    name: 'main.akasha',
    path: 'main.akasha',
    content: SAMPLES[5].code // Bubble Sort
  });
});

// ── Tab Management ───────────────────────────────────────────────────────────

function openTab({ id, name, path = null, content = "" }) {
  // Check if tab is already open
  const existing = tabs.find(t => t.id === id || (path && t.path === path));
  if (existing) {
    switchTab(existing.id);
    return;
  }

  const newTab = {
    id: id || `tab-${tabCounter++}`,
    name: name || 'Untitled.akasha',
    path: path,
    content: content,
    isDirty: false
  };

  tabs.push(newTab);
  renderTabs();
  renderOpenEditors();
  switchTab(newTab.id);
}

function switchTab(tabId) {
  const currentTab = tabs.find(t => t.id === activeTabId);
  if (currentTab) {
    currentTab.content = textarea.value;
  }

  activeTabId = tabId;
  const targetTab = tabs.find(t => t.id === tabId);
  if (!targetTab) return;

  textarea.value = targetTab.content;
  updateEditorView();
  renderTabs();
  renderOpenEditors();
  crumbFilename.textContent = targetTab.name;
  statusMsg.textContent = `Opened: ${targetTab.name}`;
}

function closeTab(tabId, event) {
  if (event) event.stopPropagation();
  const idx = tabs.findIndex(t => t.id === tabId);
  if (idx === -1) return;

  tabs.splice(idx, 1);

  if (tabs.length === 0) {
    openTab({ id: 'tab-1', name: 'Untitled.akasha', content: '' });
  } else if (activeTabId === tabId) {
    const nextIdx = Math.max(0, idx - 1);
    switchTab(tabs[nextIdx].id);
  } else {
    renderTabs();
    renderOpenEditors();
  }
}

function closeActiveTab() {
  if (activeTabId) closeTab(activeTabId);
}

function newFile() {
  openTab({
    name: `Untitled-${tabCounter++}.akasha`,
    content: `-- New Akasha script\ncheppu("Hello from Akasha!")\n`
  });
}

function renderTabs() {
  const container = document.getElementById('tabs-container');
  container.innerHTML = '';

  tabs.forEach(tab => {
    const tabEl = document.createElement('div');
    tabEl.className = `editor-tab ${tab.id === activeTabId ? 'active' : ''} ${tab.isDirty ? 'dirty' : ''}`;
    tabEl.onclick = () => switchTab(tab.id);

    tabEl.innerHTML = `
      <span class="tab-title-text">📄 ${tab.name}</span>
      <span class="tab-dirty-dot"></span>
      <span class="tab-close-btn" onclick="closeTab('${tab.id}', event)">✕</span>
    `;
    container.appendChild(tabEl);
  });
}

function renderOpenEditors() {
  const list = document.getElementById('open-editors-list');
  list.innerHTML = '';

  tabs.forEach(tab => {
    const li = document.createElement('li');
    li.className = `file-list-item ${tab.id === activeTabId ? 'active' : ''}`;
    li.innerHTML = `📄 ${tab.name}`;
    li.onclick = () => switchTab(tab.id);
    list.appendChild(li);
  });
}

// ── Live Syntax Highlighting Engine ──────────────────────────────────────────

const KEYWORDS = new Set([
  "cheppu", "viluva", "sthiram", "rahasyam", "okavela", "lekapothe", "mariyu",
  "prathi", "lo", "alaa", "loop", "aapu", "konasaginchu", "karyam", "phalitham",
  "muppu", "tirugu", "sthithi", "nijam", "abaddham", "shunyam", "rachana",
  "enum", "lakshanam", "adugu", "nerpu", "asura", "digumathi", "egumathi",
  "vethuku", "default", "pariksha", "pattu", "antham", "visuru", "async", "aagu"
]);

const TYPES = new Set([
  "Sankhya", "Dasamsam", "Padam", "Nijam", "Shunyam", "Vikalpa", "Phalitham",
  "Gumpu", "Naksha", "Janta", "Byte", "Patrika"
]);

const BUILTINS = new Set([
  "parimaanam", "type_of", "range", "adugu", "Undu", "Ledu", "Sari", "Tappu"
]);

function highlightAkashaCode(code) {
  const lines = code.split('\n');
  const highlightedLines = lines.map(line => highlightLine(line));
  return highlightedLines.join('\n');
}

function highlightLine(line) {
  let i = 0;
  let out = "";
  const n = line.length;

  while (i < n) {
    // Comments: -- or //
    if (line.slice(i, i + 2) === "--" || line.slice(i, i + 2) === "//") {
      out += `<span class="tok-comment">${escapeHtml(line.slice(i))}</span>`;
      break;
    }

    // F-strings: f"..." or f'...'
    if (line[i] === 'f' && (line[i + 1] === '"' || line[i + 1] === "'")) {
      const q = line[i + 1];
      let end = i + 2;
      while (end < n && line[end] !== q) {
        if (line[end] === '\\') end += 2;
        else end += 1;
      }
      if (end < n) end += 1;
      out += `<span class="tok-fstring">${escapeHtml(line.slice(i, end))}</span>`;
      i = end;
      continue;
    }

    // Standard strings: "..." or '...'
    if (line[i] === '"' || line[i] === "'") {
      const q = line[i];
      let end = i + 1;
      while (end < n && line[end] !== q) {
        if (line[end] === '\\') end += 2;
        else end += 1;
      }
      if (end < n) end += 1;
      out += `<span class="tok-string">${escapeHtml(line.slice(i, end))}</span>`;
      i = end;
      continue;
    }

    // Numbers
    if (/\d/.test(line[i])) {
      let end = i;
      while (end < n && /[\w.]/.test(line[end])) end++;
      out += `<span class="tok-number">${escapeHtml(line.slice(i, end))}</span>`;
      i = end;
      continue;
    }

    // Identifiers, Keywords, Functions
    if (/[a-zA-Z_]/.test(line[i])) {
      let end = i;
      while (end < n && /[\w_]/.test(line[end])) end++;
      const word = line.slice(i, end);

      if (KEYWORDS.has(word)) {
        out += `<span class="tok-keyword">${word}</span>`;
      } else if (TYPES.has(word)) {
        out += `<span class="tok-type">${word}</span>`;
      } else if (BUILTINS.has(word)) {
        out += `<span class="tok-builtin">${word}</span>`;
      } else if (line[end] === '(') {
        out += `<span class="tok-func">${word}</span>`;
      } else {
        out += `<span class="tok-variable">${word}</span>`;
      }
      i = end;
      continue;
    }

    out += escapeHtml(line[i]);
    i++;
  }

  return out;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function updateEditorView() {
  const code = textarea.value;
  highlightLayer.innerHTML = highlightAkashaCode(code) + "\n";

  // Update line numbers gutter
  const lineCount = code.split('\n').length;
  gutter.innerHTML = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');

  // Sync active tab state
  const curTab = tabs.find(t => t.id === activeTabId);
  if (curTab) {
    curTab.content = code;
    curTab.isDirty = true;
    renderTabs();
  }

  updateCursorPos();
}

function updateCursorPos() {
  const pos = textarea.selectionStart;
  const val = textarea.value.slice(0, pos);
  const lines = val.split('\n');
  const line = lines.length;
  const col = lines[lines.length - 1].length + 1;
  statusCursor.textContent = `Ln ${line}, Col ${col}`;
}

// ── Editor Event Listeners ────────────────────────────────────────────────────

function setupEditorEvents() {
  textarea.addEventListener('input', updateEditorView);
  textarea.addEventListener('keyup', updateCursorPos);
  textarea.addEventListener('click', updateCursorPos);

  // Synchronized scroll
  textarea.addEventListener('scroll', () => {
    highlightLayer.scrollTop = textarea.scrollTop;
    highlightLayer.scrollLeft = textarea.scrollLeft;
    gutter.scrollTop = textarea.scrollTop;
  });

  // Tab & Auto-Indentation Handling
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      insertTextAtCursor('    ');
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const pos = textarea.selectionStart;
      const lineStart = textarea.value.lastIndexOf('\n', pos - 1) + 1;
      const currentLine = textarea.value.slice(lineStart, pos);
      const indent = currentLine.match(/^\s*/)[0];
      const extra = currentLine.trim().endsWith('{') ? '    ' : '';
      insertTextAtCursor('\n' + indent + extra);
    } else if (e.key === '{') {
      e.preventDefault();
      insertEnclosed('{}');
    } else if (e.key === '(') {
      e.preventDefault();
      insertEnclosed('()');
    } else if (e.key === '[') {
      e.preventDefault();
      insertEnclosed('[]');
    } else if (e.key === '"') {
      e.preventDefault();
      insertEnclosed('""');
    }
  });
}

function insertTextAtCursor(text) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  textarea.value = textarea.value.slice(0, start) + text + textarea.value.slice(end);
  textarea.selectionStart = textarea.selectionEnd = start + text.length;
  updateEditorView();
}

function insertEnclosed(pair) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const sel = textarea.value.slice(start, end);
  textarea.value = textarea.value.slice(0, start) + pair[0] + sel + pair[1] + textarea.value.slice(end);
  textarea.selectionStart = textarea.selectionEnd = start + 1 + sel.length;
  updateEditorView();
}

// ── Backend Compiler & VM API Calls ──────────────────────────────────────────

async function runScript() {
  const code = textarea.value;
  if (!code.trim()) return;

  switchPanelTab('terminal');
  appendTerminalLine(`> akasha run ${crumbFilename.textContent}`, 'term-cmd');
  statusMsg.textContent = 'Running script on Stack VM...';
  document.getElementById('exec-time-badge').textContent = 'Running...';

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    const data = await res.json();

    if (data.success) {
      if (data.output) {
        appendTerminalLine(data.output.trimEnd());
      } else {
        appendTerminalLine('[Process finished with exit code 0]', 'term-system');
      }
      document.getElementById('exec-time-badge').textContent = `Done in ${data.execution_time_ms}ms`;
      statusMsg.textContent = `Execution Finished (${data.execution_time_ms}ms)`;
      statusErrors.innerHTML = '<span>⨂ 0  ⚠ 0</span>';
    } else {
      const err = data.error ? `${data.error.phase} Error: ${data.error.message}` : 'Runtime Error';
      appendTerminalLine(err, 'term-error');
      document.getElementById('exec-time-badge').textContent = `Failed in ${data.execution_time_ms}ms`;
      statusMsg.textContent = 'Execution Error';
      statusErrors.innerHTML = '<span style="color: #f87171;">⨂ 1  ⚠ 0</span>';
    }
  } catch (err) {
    appendTerminalLine(`Communication Error: ${err.message}`, 'term-error');
  }
}

async function disassembleScript() {
  const code = textarea.value;
  if (!code.trim()) return;

  switchPanelTab('bytecode');
  statusMsg.textContent = 'Compiling to Bytecode (.akb)...';

  try {
    const res = await fetch('/api/disassemble', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    const data = await res.json();

    const container = document.getElementById('bytecode-output');
    if (data.success) {
      let html = `
        <table class="bytecode-table">
          <thead><tr><th>Offset</th><th>OpCode</th><th>Arg</th><th>Value / Target</th><th>Line</th></tr></thead>
          <tbody>
      `;
      data.instructions.forEach(inst => {
        let badgeClass = 'opcode-badge';
        if (inst.opcode.includes('CONST')) badgeClass += ' const';
        else if (inst.opcode.includes('JUMP')) badgeClass += ' jump';
        else if (inst.opcode.includes('CALL')) badgeClass += ' call';

        html += `
          <tr>
            <td>${inst.offset}</td>
            <td><span class="${badgeClass}">${inst.opcode}</span></td>
            <td>${inst.arg !== null ? inst.arg : ''}</td>
            <td>${escapeHtml(inst.arg_repr || '')}</td>
            <td>${inst.line}</td>
          </tr>
        `;
      });
      html += `</tbody></table>`;
      container.innerHTML = html;
      statusMsg.textContent = `Bytecode Compiled (${data.instructions.length} opcodes)`;
    } else {
      container.innerHTML = `<div class="term-error" style="padding: 10px;">Compilation Error: ${data.error}</div>`;
    }
  } catch (err) {
    document.getElementById('bytecode-output').innerHTML = `<div class="term-error">Error: ${err.message}</div>`;
  }
}

async function checkSyntax() {
  const code = textarea.value;
  try {
    const res = await fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    const data = await res.json();
    if (data.success) {
      statusMsg.textContent = 'Syntax Valid!';
      statusErrors.innerHTML = '<span>⨂ 0  ⚠ 0</span>';
      document.getElementById('problems-output').innerHTML = '<div class="problems-empty">✓ No problems detected in active file.</div>';
    } else {
      statusMsg.textContent = 'Syntax Error';
      statusErrors.innerHTML = '<span style="color: #f87171;">⨂ 1  ⚠ 0</span>';
      document.getElementById('problems-output').innerHTML = `<div style="padding: 12px; color: #f87171;">⨂ ${data.error}</div>`;
      switchPanelTab('problems');
    }
  } catch (e) {
    console.error(e);
  }
}

// ── Workspace Files & Samples ─────────────────────────────────────────────────

async function loadWorkspaceFiles() {
  const list = document.getElementById('workspace-files-list');
  try {
    const res = await fetch('/api/workspace/files');
    const data = await res.json();
    list.innerHTML = '';

    if (data.files && data.files.length > 0) {
      data.files.forEach(f => {
        const li = document.createElement('li');
        li.className = 'file-list-item';
        li.innerHTML = `📄 ${f.name}`;
        li.onclick = () => loadFileFromPath(f.path, f.name);
        list.appendChild(li);
      });
    } else {
      list.innerHTML = '<li class="file-list-empty">No .akasha files found.</li>';
    }
  } catch (err) {
    list.innerHTML = '<li class="file-list-empty">Workspace offline</li>';
  }
}

async function loadFileFromPath(path, name) {
  try {
    const res = await fetch(`/api/file/read?path=${encodeURIComponent(path)}`);
    const data = await res.json();
    if (data.success) {
      openTab({ name, path, content: data.content });
    }
  } catch (err) {
    console.error(err);
  }
}

function initSamplesSidebar() {
  const list = document.getElementById('samples-library-list');
  list.innerHTML = '';

  SAMPLES.forEach(s => {
    const li = document.createElement('li');
    li.className = 'file-list-item';
    li.innerHTML = `✦ ${s.name}`;
    li.onclick = () => {
      openTab({ id: `sample-${s.id}`, name: s.id, content: s.code });
    };
    list.appendChild(li);
  });
}

// ── File Save ─────────────────────────────────────────────────────────────────

async function saveActiveFile() {
  const currentTab = tabs.find(t => t.id === activeTabId);
  if (!currentTab) return;

  try {
    const res = await fetch('/api/file/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: currentTab.path,
        name: currentTab.name,
        content: textarea.value
      })
    });
    const data = await res.json();
    if (data.success) {
      currentTab.path = data.path;
      currentTab.isDirty = false;
      renderTabs();
      statusMsg.textContent = `Saved: ${currentTab.name}`;
    }
  } catch (err) {
    console.error(err);
  }
}

// ── Panel & Terminal Control ──────────────────────────────────────────────────

function switchPanelTab(tabName) {
  document.querySelectorAll('.panel-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.panel-pane-content').forEach(p => p.classList.remove('active'));

  const btn = document.getElementById(`tab-btn-${tabName}`);
  const pane = document.getElementById(`pane-${tabName}`);
  if (btn) btn.classList.add('active');
  if (pane) pane.classList.add('active');
}

function appendTerminalLine(text, className = '') {
  const consoleEl = document.getElementById('terminal-output');
  const line = document.createElement('div');
  line.className = `term-line ${className}`;
  line.textContent = text;
  consoleEl.appendChild(line);
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearTerminal() {
  document.getElementById('terminal-output').innerHTML = '';
  document.getElementById('exec-time-badge').textContent = '';
  statusMsg.textContent = 'Terminal cleared';
}

function togglePanel() {
  const panel = document.getElementById('bottom-panel');
  const resizer = document.getElementById('resizer-panel');
  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? 'flex' : 'none';
  resizer.style.display = isHidden ? 'block' : 'none';
}

function togglePanelMaximize() {
  const panel = document.getElementById('bottom-panel');
  if (panel.style.height === '70vh') {
    panel.style.height = '220px';
  } else {
    panel.style.height = '70vh';
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar-panel');
  const resizer = document.getElementById('resizer-sidebar');
  const isHidden = sidebar.style.display === 'none';
  sidebar.style.display = isHidden ? 'flex' : 'none';
  resizer.style.display = isHidden ? 'block' : 'none';
}

function toggleSection(sectionId) {
  const sec = document.getElementById(sectionId);
  if (sec) sec.classList.toggle('collapsed');
}

// ── Resizer Drag Logic ────────────────────────────────────────────────────────

function setupResizers() {
  // Sidebar Resizer
  const resizerH = document.getElementById('resizer-sidebar');
  const sidebar = document.getElementById('sidebar-panel');
  let isResizingH = false;

  resizerH.addEventListener('mousedown', () => {
    isResizingH = true;
    resizerH.classList.add('resizing');
  });

  // Panel Resizer
  const resizerV = document.getElementById('resizer-panel');
  const panel = document.getElementById('bottom-panel');
  let isResizingV = false;

  resizerV.addEventListener('mousedown', () => {
    isResizingV = true;
    resizerV.classList.add('resizing');
  });

  document.addEventListener('mousemove', (e) => {
    if (isResizingH) {
      const newWidth = Math.max(160, Math.min(e.clientX - 48, 500));
      sidebar.style.width = `${newWidth}px`;
    }
    if (isResizingV) {
      const newHeight = Math.max(100, Math.min(window.innerHeight - e.clientY - 22, window.innerHeight * 0.8));
      panel.style.height = `${newHeight}px`;
    }
  });

  document.addEventListener('mouseup', () => {
    isResizingH = false;
    isResizingV = false;
    resizerH.classList.remove('resizing');
    resizerV.classList.remove('resizing');
  });
}

// ── Command Palette (Ctrl+P / F1) ─────────────────────────────────────────────

const COMMANDS = [
  { label: "Run Active File", shortcut: "F5", action: runScript },
  { label: "Compile to Bytecode (.akb)", shortcut: "Ctrl+B", action: disassembleScript },
  { label: "Check Syntax", shortcut: "F7", action: checkSyntax },
  { label: "New Akasha File", shortcut: "Ctrl+N", action: newFile },
  { label: "Save File", shortcut: "Ctrl+S", action: saveActiveFile },
  { label: "Clear Terminal", shortcut: "Ctrl+L", action: clearTerminal },
  { label: "Toggle Sidebar", shortcut: "Ctrl+B", action: toggleSidebar },
  { label: "Toggle Terminal Panel", shortcut: "Ctrl+J", action: togglePanel },
  { label: "Theme: VS Code Dark+", action: () => setTheme('theme-vscode-dark') },
  { label: "Theme: Tokyo Night", action: () => setTheme('theme-tokyo-night') },
  { label: "Theme: GitHub Light", action: () => setTheme('theme-github-light') },
  { label: "Open Language Reference Docs", action: openDocsModal }
];

function openCommandPalette() {
  const modal = document.getElementById('cmd-palette-modal');
  const input = document.getElementById('cmd-palette-input');
  modal.classList.remove('hidden');
  input.value = '';
  input.focus();
  renderCommandList('');
}

function closeCommandPalette(event) {
  if (!event || event.target.id === 'cmd-palette-modal') {
    document.getElementById('cmd-palette-modal').classList.add('hidden');
  }
}

function renderCommandList(query) {
  const list = document.getElementById('cmd-palette-list');
  list.innerHTML = '';
  const filtered = COMMANDS.filter(c => c.label.toLowerCase().includes(query.toLowerCase()));

  filtered.forEach((cmd, idx) => {
    const li = document.createElement('li');
    li.className = `cmd-palette-item ${idx === 0 ? 'active' : ''}`;
    li.innerHTML = `<span>${cmd.label}</span>${cmd.shortcut ? `<span class="opt-shortcut">${cmd.shortcut}</span>` : ''}`;
    li.onclick = () => {
      closeCommandPalette();
      cmd.action();
    };
    list.appendChild(li);
  });
}

document.getElementById('cmd-palette-input')?.addEventListener('input', (e) => {
  renderCommandList(e.target.value);
});

// ── Keyboard Shortcuts ────────────────────────────────────────────────────────

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F5') {
      e.preventDefault();
      runScript();
    } else if (e.key === 'F7') {
      e.preventDefault();
      checkSyntax();
    } else if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      saveActiveFile();
    } else if (e.ctrlKey && e.key === 'n') {
      e.preventDefault();
      newFile();
    } else if (e.ctrlKey && e.key === 'w') {
      e.preventDefault();
      closeActiveTab();
    } else if (e.ctrlKey && e.key === 'p') {
      e.preventDefault();
      openCommandPalette();
    } else if (e.ctrlKey && e.key === 'b') {
      e.preventDefault();
      disassembleScript();
    } else if (e.ctrlKey && e.key === 'l') {
      e.preventDefault();
      clearTerminal();
    } else if (e.key === 'Escape') {
      closeCommandPalette();
      closeDocsModal();
    }
  });
}

// ── Themes & Dialogs ──────────────────────────────────────────────────────────

function setTheme(themeClass) {
  document.body.className = `desktop-app-body ${themeClass}`;
}

function openDocsModal() {
  document.getElementById('docs-modal').classList.remove('hidden');
}

function closeDocsModal(e) {
  if (!e || e.target.id === 'docs-modal') {
    document.getElementById('docs-modal').classList.add('hidden');
  }
}

function openAboutModal() {
  alert("Akasha Studio (VS Code Edition) v0.1.0\n\nThe official desktop IDE for the Telugu-inspired Akasha programming language.");
}

function toggleMenu(menuId) {
  document.querySelectorAll('.menu-dropdown').forEach(m => {
    if (m.id !== menuId) m.classList.add('hidden');
  });
  const menu = document.getElementById(menuId);
  if (menu) menu.classList.toggle('hidden');
}

document.addEventListener('click', (e) => {
  if (!e.target.closest('.menu-item')) {
    document.querySelectorAll('.menu-dropdown').forEach(m => m.classList.add('hidden'));
  }
});

// ── Native Window Controls Simulation ─────────────────────────────────────────

function windowMinimize() {
  statusMsg.textContent = "Window minimized (Simulation)";
}

function windowMaximize() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}

function windowClose() {
  window.close();
}
