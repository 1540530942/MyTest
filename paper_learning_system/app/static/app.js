const tokenInput = document.querySelector('#tokenInput');
const seedInput = document.querySelector('#seedInput');
const mineButton = document.querySelector('#mineButton');
const clearMineButton = document.querySelector('#clearMineButton');
const refreshLibraryButton = document.querySelector('#refreshLibraryButton');
const importReferenceButton = document.querySelector('#importReferenceButton');
const mineResults = document.querySelector('#mineResults');
const referenceList = document.querySelector('#referenceList');
const paperList = document.querySelector('#paperList');
const paperTitle = document.querySelector('#paperTitle');
const paperMeta = document.querySelector('#paperMeta');
const paperAbstract = document.querySelector('#paperAbstract');
const paperLink = document.querySelector('#paperLink');
const paperChips = document.querySelector('#paperChips');
const analyzeButton = document.querySelector('#analyzeButton');
const practiceButton = document.querySelector('#practiceButton');
const analysisOutput = document.querySelector('#analysisOutput');
const questionInput = document.querySelector('#questionInput');
const askButton = document.querySelector('#askButton');
const answerOutput = document.querySelector('#answerOutput');
const practiceOutput = document.querySelector('#practiceOutput');
const noteInput = document.querySelector('#noteInput');
const saveNoteButton = document.querySelector('#saveNoteButton');
const notesOutput = document.querySelector('#notesOutput');
const statusText = document.querySelector('#statusText');
const hermesProvider = document.querySelector('#hermesProvider');
const hermesMessages = document.querySelector('#hermesMessages');
const hermesInput = document.querySelector('#hermesInput');
const hermesSendButton = document.querySelector('#hermesSendButton');
const hermesClearButton = document.querySelector('#hermesClearButton');
const hermesProviderSelect = document.querySelector('#hermesProviderSelect');
const hermesModelSelect = document.querySelector('#hermesModelSelect');

const basePath = window.PAPER_BASE_PATH || '';

const analysisFields = [
  ['background', 'Background'],
  ['core_problem', 'Core Problem'],
  ['method', 'Method'],
  ['contributions', 'Contributions'],
  ['limitations', 'Limitations'],
  ['reading_plan', 'Reading Plan']
];

let selectedPaper = null;
let library = [];
let referencePapers = [];
let hermesProviders = [];

function setStatus(message) {
  statusText.textContent = message;
}

function headers() {
  const value = tokenInput.value.trim().replace(/^API_TOKEN\s*=\s*/, '');
  const base = { 'Content-Type': 'application/json' };
  if (value) {
    base.Authorization = `Bearer ${value}`;
  }
  return base;
}

async function api(path, options = {}) {
  const response = await fetch(`${basePath}${path}`, {
    ...options,
    headers: {
      ...headers(),
      ...(options.headers || {})
    }
  });
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      const snippet = text.replace(/\s+/g, ' ').slice(0, 160);
      throw new Error(`Expected JSON but received ${response.status} ${response.statusText}: ${snippet}`);
    }
  }
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

function enabledHermesProviders() {
  return hermesProviders.filter((provider) => provider.enabled);
}

function selectedHermesProvider() {
  return enabledHermesProviders().find((provider) => provider.name === hermesProviderSelect.value) || enabledHermesProviders()[0] || null;
}

function renderHermesModels() {
  const provider = selectedHermesProvider();
  hermesModelSelect.replaceChildren();
  if (!provider) {
    hermesModelSelect.append(new Option('No model configured', ''));
    hermesProvider.textContent = 'provider: unavailable';
    return;
  }

  const model = provider.model || '';
  hermesModelSelect.append(new Option(model || 'default model', model));
  hermesProvider.textContent = `provider: ${provider.name}`;
}

async function loadHermesProviders() {
  try {
    const data = await api('/api/hermes/providers');
    hermesProviders = Array.isArray(data.providers) ? data.providers : [];
    const enabled = enabledHermesProviders();
    hermesProviderSelect.replaceChildren();
    if (!enabled.length) {
      hermesProviderSelect.append(new Option('No provider configured', ''));
      renderHermesModels();
      appendHermesMessage('assistant', 'No Hermes model provider is enabled on the server yet. Configure GLM, DeepSeek, Qwen, OpenAI, or another provider in the server environment.', 'configuration');
      return;
    }

    enabled.forEach((provider) => {
      const label = `${provider.name} (${provider.model || 'default'})`;
      hermesProviderSelect.append(new Option(label, provider.name));
    });
    const preferred = enabled.find((provider) => provider.name === 'glm') || enabled[0];
    hermesProviderSelect.value = preferred.name;
    renderHermesModels();
  } catch (error) {
    hermesProvider.textContent = 'provider: unavailable';
    appendHermesMessage('assistant', `Could not load Hermes models: ${error.message}`, 'configuration');
  }
}

function appendHermesMessage(role, content, meta = '') {
  const item = document.createElement('article');
  item.className = `hermes-message ${role}`;
  const title = document.createElement('p');
  title.className = 'eyebrow';
  title.textContent = role === 'user' ? 'You' : 'Hermes';
  const body = document.createElement('p');
  body.textContent = content;
  item.append(title, body);
  if (meta) {
    const detail = document.createElement('p');
    detail.className = 'muted';
    detail.textContent = meta;
    item.append(detail);
  }
  hermesMessages.append(item);
  hermesMessages.scrollTop = hermesMessages.scrollHeight;
}

function renderHermesAnswer(answer) {
  const suggestions = Array.isArray(answer.suggestions) ? answer.suggestions.filter(Boolean) : [];
  const meta = [
    answer.mode ? `mode: ${answer.mode}` : '',
    answer._hermes?.provider ? `provider: ${answer._hermes.provider}` : '',
    answer._hermes?.model ? `model: ${answer._hermes.model}` : ''
  ].filter(Boolean).join(' | ');
  appendHermesMessage('assistant', answer.answer || JSON.stringify(answer, null, 2), meta);
  if (answer._hermes?.provider) {
    hermesProvider.textContent = `provider: ${answer._hermes.provider}`;
  }
  if (suggestions.length) {
    appendHermesMessage('assistant', suggestions.map((item, index) => `${index + 1}. ${item}`).join('\n'), 'suggestions');
  }
}

async function askHermes() {
  const message = hermesInput.value.trim();
  if (!message) {
    setStatus('Write a Hermes question first.');
    return;
  }
  const provider = selectedHermesProvider();
  hermesSendButton.disabled = true;
  hermesInput.value = '';
  appendHermesMessage('user', message);
  setStatus('Hermes is thinking...');
  try {
    const data = await api('/api/hermes/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        task: 'paper-analysis',
        provider: provider?.name || '',
        model: hermesModelSelect.value || provider?.model || ''
      })
    });
    renderHermesAnswer(data.answer || {});
    setStatus('Hermes answered.');
  } catch (error) {
    appendHermesMessage('assistant', `Hermes failed: ${error.message}`, 'error');
    setStatus(`Hermes failed: ${error.message}`);
  } finally {
    hermesSendButton.disabled = false;
  }
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return map[char];
  });
}

function short(text, length = 280) {
  if (!text) return '';
  return text.length > length ? `${text.slice(0, length)}...` : text;
}

function publishedTime(value) {
  const time = Date.parse(value || '');
  return Number.isNaN(time) ? Number.POSITIVE_INFINITY : time;
}

function sortByPublished(items) {
  return [...items].sort((left, right) => {
    const dateDiff = publishedTime(left.published) - publishedTime(right.published);
    if (dateDiff !== 0) return dateDiff;
    return String(left.title || '').localeCompare(String(right.title || ''));
  });
}

function splitMeta(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  return String(value || '')
    .split(/[,;|]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatAuthors(authors) {
  if (Array.isArray(authors)) {
    return authors.join(', ');
  }
  return String(authors || '');
}

function safeUrl(value) {
  if (!value) return '#';
  try {
    const url = new URL(value, window.location.origin);
    if (url.protocol === 'http:' || url.protocol === 'https:') {
      return url.href;
    }
  } catch {
    return '#';
  }
  return '#';
}

function chip(label, variant = '') {
  const span = document.createElement('span');
  span.className = `chip${variant ? ` ${variant}` : ''}`;
  span.textContent = label;
  return span;
}

function miniChip(label) {
  return `<span class="mini-chip">${escapeHtml(label)}</span>`;
}

function renderPaperChips(paper) {
  paperChips.replaceChildren();
  if (!paper) return;

  paperChips.append(chip(paper.source || 'manual', 'source'));
  if (paper.external_id) {
    paperChips.append(chip(paper.external_id));
  }
  splitMeta(paper.categories).slice(0, 4).forEach((category) => {
    paperChips.append(chip(category, 'category'));
  });
  if (paper.analysis?.mode) {
    paperChips.append(chip(`analysis: ${paper.analysis.mode}`, 'mode'));
  }
}

function renderLibrary() {
  paperList.replaceChildren();
  if (!library.length) {
    paperList.innerHTML = '<p class="muted">No papers saved yet.</p>';
    return;
  }

  library.forEach((paper) => {
    const item = document.createElement('button');
    const categories = splitMeta(paper.categories).slice(0, 2);
    item.type = 'button';
    item.className = `paper-item${selectedPaper?.id === paper.id ? ' active' : ''}`;
    item.innerHTML = `
      <h3>${escapeHtml(paper.title)}</h3>
      <p class="muted">${escapeHtml(paper.authors || 'Unknown authors')}</p>
      <div class="mini-chips">${categories.map(miniChip).join('')}</div>
      <p>${escapeHtml(short(paper.abstract, 180))}</p>
    `;
    item.addEventListener('click', () => selectPaper(paper.id));
    paperList.append(item);
  });
}

function renderReferences() {
  referenceList.replaceChildren();
  if (!referencePapers.length) {
    referenceList.innerHTML = '<p class="muted">No reference papers loaded.</p>';
    return;
  }

  referencePapers.forEach((paper) => {
    const item = document.createElement('article');
    const link = safeUrl(paper.url);
    const chips = [paper.category, paper.role].filter(Boolean).slice(0, 2);
    item.className = 'reference-item';
    item.innerHTML = `
      <p class="eyebrow">${escapeHtml(paper.published || 'No date')}</p>
      <h3>${escapeHtml(paper.title)}</h3>
      <div class="mini-chips">${chips.map(miniChip).join('')}</div>
      <p>${escapeHtml(short(paper.summary, 220))}</p>
      <div class="actions">
        <button type="button">Save</button>
        <a href="${link}" target="_blank" rel="noreferrer">Open</a>
      </div>
    `;
    item.querySelector('button').addEventListener('click', async () => {
      await importReferencePapers([paper.id]);
    });
    referenceList.append(item);
  });
}

function setEmpty(target, message) {
  target.classList.add('empty-state');
  target.replaceChildren();
  target.textContent = message;
}

function renderValue(container, value) {
  if (Array.isArray(value)) {
    const list = document.createElement('ul');
    list.className = 'study-list';
    value.filter(Boolean).forEach((item) => {
      const li = document.createElement('li');
      li.textContent = String(item);
      list.append(li);
    });
    container.append(list);
    return;
  }

  const text = typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : String(value || '');
  const paragraph = document.createElement('p');
  paragraph.textContent = text;
  container.append(paragraph);
}

function renderAnalysis(analysis) {
  analysisOutput.classList.remove('empty-state');
  analysisOutput.replaceChildren();

  if (!analysis || analysis.message) {
    setEmpty(analysisOutput, analysis?.message || 'No analysis generated yet.');
    return;
  }

  if (analysis.one_sentence) {
    const lead = document.createElement('article');
    lead.className = 'analysis-lead';
    lead.textContent = analysis.one_sentence;
    analysisOutput.append(lead);
  }

  const meta = document.createElement('div');
  meta.className = 'chips';
  meta.append(chip(`mode: ${analysis.mode || 'unknown'}`, 'mode'));
  splitMeta(analysis.keywords).slice(0, 10).forEach((keyword) => {
    meta.append(chip(keyword, 'category'));
  });
  analysisOutput.append(meta);

  const grid = document.createElement('div');
  grid.className = 'analysis-grid';
  analysisFields.forEach(([key, label]) => {
    const value = analysis[key];
    if (!value || (Array.isArray(value) && !value.length)) return;

    const field = document.createElement('article');
    field.className = 'analysis-field';
    const heading = document.createElement('h3');
    heading.textContent = label;
    field.append(heading);
    renderValue(field, value);
    grid.append(field);
  });

  if (grid.children.length) {
    analysisOutput.append(grid);
  }
}

function renderAnswer(answer) {
  answerOutput.classList.remove('empty-state');
  answerOutput.replaceChildren();

  if (!answer) {
    setEmpty(answerOutput, 'Answers will appear here.');
    return;
  }

  const main = document.createElement('article');
  main.className = 'answer-card';
  main.innerHTML = `<h3>Answer</h3><p>${escapeHtml(answer.answer || 'No answer returned.')}</p>`;
  answerOutput.append(main);

  if (Array.isArray(answer.evidence) && answer.evidence.length) {
    const evidence = document.createElement('article');
    evidence.className = 'answer-card';
    evidence.innerHTML = '<h3>Evidence</h3>';
    renderValue(evidence, answer.evidence);
    answerOutput.append(evidence);
  }

  if (answer.next_step) {
    const next = document.createElement('article');
    next.className = 'answer-card';
    next.innerHTML = `<h3>Next Step</h3><p>${escapeHtml(answer.next_step)}</p>`;
    answerOutput.append(next);
  }

  const meta = document.createElement('div');
  meta.className = 'chips';
  meta.append(chip(`mode: ${answer.mode || 'unknown'}`, 'mode'));
  answerOutput.append(meta);
}

function renderPractice(items = []) {
  practiceOutput.replaceChildren();
  if (!items.length) {
    practiceOutput.innerHTML = '<p class="empty-state">Generate Q&A to build an active-recall study pack.</p>';
    return;
  }

  items.forEach((item, index) => {
    const details = document.createElement('details');
    details.className = 'qa-item';
    details.open = index === 0;

    const summary = document.createElement('summary');
    const number = document.createElement('span');
    number.className = 'question-index';
    number.textContent = `Q${index + 1}`;

    const question = document.createElement('span');
    question.textContent = item.question || 'Untitled question';

    const kind = document.createElement('span');
    kind.className = 'question-kind';
    kind.textContent = item.kind || 'concept';

    summary.append(number, question, kind);

    const answer = document.createElement('div');
    answer.className = 'qa-answer';
    answer.textContent = item.answer || 'No answer generated.';

    details.append(summary, answer);
    practiceOutput.append(details);
  });
}

function renderNotes(notes = []) {
  notesOutput.replaceChildren();
  if (!notes.length) {
    notesOutput.innerHTML = '<p class="muted">No notes yet.</p>';
    return;
  }
  notes.forEach((note) => {
    const item = document.createElement('article');
    item.className = 'note-item';
    const content = document.createElement('p');
    content.textContent = note.content;
    const time = document.createElement('p');
    time.className = 'muted';
    time.textContent = note.created_at;
    item.append(content, time);
    notesOutput.append(item);
  });
}

function renderPaper(paper, notes = [], practiceItems = []) {
  selectedPaper = paper;
  paperTitle.textContent = paper.title;
  paperMeta.textContent = `${paper.authors || 'Unknown authors'} ${paper.published ? `| ${paper.published}` : ''}`;
  paperAbstract.textContent = paper.abstract || 'No abstract saved yet.';

  const link = safeUrl(paper.url || paper.pdf_url);
  paperLink.href = link;
  paperLink.style.visibility = link !== '#' ? 'visible' : 'hidden';

  renderPaperChips(paper);
  renderAnalysis(paper.analysis || { message: 'No analysis generated yet.' });
  renderPractice(practiceItems);
  renderNotes(notes);
  renderLibrary();
}

async function loadLibrary() {
  setStatus('Loading library...');
  const data = await api('/api/papers');
  library = sortByPublished(data.papers);
  renderLibrary();
  if (!selectedPaper && library[0]) {
    await selectPaper(library[0].id);
  }
  setStatus(`Loaded ${library.length} paper(s).`);
}

async function loadReferencePapers() {
  const data = await api('/api/reference-papers');
  referencePapers = sortByPublished(data.papers);
  renderReferences();
}

async function importReferencePapers(ids = []) {
  importReferenceButton.disabled = true;
  setStatus(ids.length ? 'Importing reference paper...' : 'Importing dated reference pack...');
  try {
    const data = await api('/api/reference-papers/import', {
      method: 'POST',
      body: JSON.stringify({ ids })
    });
    await loadLibrary();
    if (data.papers[0]) {
      await selectPaper(data.papers[0].id);
    }
    setStatus(`Imported ${data.papers.length} reference paper(s).`);
  } catch (error) {
    setStatus(`Reference import failed: ${error.message}`);
  } finally {
    importReferenceButton.disabled = false;
  }
}

async function selectPaper(id) {
  setStatus('Loading paper...');
  const data = await api(`/api/papers/${id}`);
  renderPaper(data.paper, data.notes, data.practice_items || []);
  renderAnswer(null);
  setStatus('Paper loaded.');
}

function renderMineResults(results) {
  mineResults.replaceChildren();
  if (!results.length) {
    mineResults.innerHTML = '<p class="muted">No arXiv results found.</p>';
    return;
  }
  results.forEach((paper) => {
    const item = document.createElement('article');
    const categories = splitMeta(paper.categories).slice(0, 3);
    const link = safeUrl(paper.url);
    item.className = 'result-item';
    item.innerHTML = `
      <h3>${escapeHtml(paper.title)}</h3>
      <p class="muted">${escapeHtml(formatAuthors(paper.authors) || 'Unknown authors')}</p>
      <div class="mini-chips">${categories.map(miniChip).join('')}</div>
      <p>${escapeHtml(short(paper.abstract))}</p>
      <div class="actions">
        <button type="button">Save to Library</button>
        <a href="${link}" target="_blank" rel="noreferrer">Open</a>
      </div>
    `;
    item.querySelector('button').addEventListener('click', async () => {
      const saved = await api('/api/papers/import', {
        method: 'POST',
        body: JSON.stringify(paper)
      });
      setStatus(`Saved: ${saved.paper.title}`);
      await loadLibrary();
      await selectPaper(saved.paper.id);
    });
    mineResults.append(item);
  });
}

async function mine() {
  const seed = seedInput.value.trim();
  if (!seed) {
    setStatus('Enter a seed paper, title, abstract, or keyword first.');
    return;
  }
  mineButton.disabled = true;
  setStatus('Mining arXiv...');
  try {
    const data = await api('/api/mine', {
      method: 'POST',
      body: JSON.stringify({ seed, max_results: 8 })
    });
    renderMineResults(data.results);
    setStatus(`Found ${data.results.length} candidate paper(s).`);
  } catch (error) {
    setStatus(`Mining failed: ${error.message}`);
  } finally {
    mineButton.disabled = false;
  }
}

async function analyze() {
  if (!selectedPaper) return;
  const paperId = selectedPaper.id;
  analyzeButton.disabled = true;
  setStatus('Generating analysis...');
  try {
    const data = await api(`/api/papers/${paperId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ force_llm: false })
    });
    renderAnalysis(data.analysis);
    await loadLibrary();
    await selectPaper(paperId);
    setStatus(`Analysis generated by ${data.analysis.mode}.`);
  } catch (error) {
    setStatus(`Analysis failed: ${error.message}`);
  } finally {
    analyzeButton.disabled = false;
  }
}

async function ask() {
  if (!selectedPaper) return;
  const question = questionInput.value.trim();
  if (!question) {
    setStatus('Write a question first.');
    return;
  }
  askButton.disabled = true;
  setStatus('Answering...');
  try {
    const data = await api(`/api/papers/${selectedPaper.id}/question`, {
      method: 'POST',
      body: JSON.stringify({ question })
    });
    renderAnswer(data.answer);
    setStatus(`Answered by ${data.answer.mode}.`);
  } catch (error) {
    setStatus(`Question failed: ${error.message}`);
  } finally {
    askButton.disabled = false;
  }
}

async function generatePractice() {
  if (!selectedPaper) return;
  const paperId = selectedPaper.id;
  practiceButton.disabled = true;
  setStatus('Generating practice questions...');
  try {
    const data = await api(`/api/papers/${paperId}/practice`, {
      method: 'POST',
      body: JSON.stringify({ count: 8 })
    });
    renderPractice(data.items);
    await selectPaper(paperId);
    setStatus(`Generated ${data.items.length} practice item(s).`);
  } catch (error) {
    setStatus(`Practice generation failed: ${error.message}`);
  } finally {
    practiceButton.disabled = false;
  }
}

async function saveNote() {
  if (!selectedPaper) return;
  const content = noteInput.value.trim();
  if (!content) return;
  await api(`/api/papers/${selectedPaper.id}/notes`, {
    method: 'POST',
    body: JSON.stringify({ content })
  });
  noteInput.value = '';
  await selectPaper(selectedPaper.id);
  setStatus('Note saved.');
}

mineButton.addEventListener('click', mine);
clearMineButton.addEventListener('click', () => {
  seedInput.value = '';
  mineResults.replaceChildren();
});
refreshLibraryButton.addEventListener('click', loadLibrary);
importReferenceButton.addEventListener('click', () => importReferencePapers());
analyzeButton.addEventListener('click', analyze);
askButton.addEventListener('click', ask);
practiceButton.addEventListener('click', generatePractice);
saveNoteButton.addEventListener('click', saveNote);
hermesSendButton.addEventListener('click', askHermes);
hermesClearButton.addEventListener('click', () => {
  hermesMessages.replaceChildren();
  hermesProvider.textContent = 'provider: ready';
});
hermesInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    askHermes();
  }
});
hermesProviderSelect.addEventListener('change', renderHermesModels);

appendHermesMessage('assistant', 'Hermes is connected to the paper learning system. Ask me to mine papers, unpack methods, compare research lines, or generate practice questions.', 'ready');
Promise.all([loadHermesProviders(), loadReferencePapers(), loadLibrary()]).catch((error) => setStatus(`Startup failed: ${error.message}`));
