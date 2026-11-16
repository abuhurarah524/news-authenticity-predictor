const $ = (selector) => document.querySelector(selector);
let mode = 'url';
let latest = null;
let busy = false;
function selectMode(next) {
  mode = next;
  for (const name of ['url', 'text']) {
    const active = name === mode;
    $(`#${name}-tab`).classList.toggle('active', active);
    $(`#${name}-tab`).setAttribute('aria-selected', String(active));
    $(`#${name}-tab`).tabIndex = active ? 0 : -1;
    $(`#${name}-panel`).hidden = !active;
  }
  $('#form-error').hidden = true;
}
for (const name of ['url', 'text']) {
  $(`#${name}-tab`).addEventListener('click', () => selectMode(name));
  $(`#${name}-tab`).addEventListener('keydown', (event) => {
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      selectMode(event.key === 'Home' ? 'url' : event.key === 'End' ? 'text' : mode === 'url' ? 'text' : 'url');
      $(`#${mode}-tab`).focus();
    }
  });
}
function countWords() {
  const count = $('#article-text').value.trim().split(/\s+/).filter(Boolean).length;
  $('#word-count').textContent = `${count.toLocaleString()} words`;
  return count;
}
$('#article-text').addEventListener('input', countWords);
$('#sample-button').addEventListener('click', () => {
  selectMode('text');
  $('#article-title').value = 'The small library bringing a neighbourhood together';
  $('#article-text').value = 'On a quiet residential street, a small community library has become a meeting point for neighbours. Volunteers collect donated books, keep the shelves organised, and invite anyone passing by to borrow a title.\n\nThe library opens on Saturday mornings. Alongside the books, visitors can find a noticeboard with local events and a table where children can read. Organisers say the idea began with a handful of books in a wooden box and grew as more residents offered their time.\n\nThis is an illustrative sample written for this interface. It is not a published news report and has no verified authenticity label.';
  countWords();
  $('#article-text').focus();
});
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}
function renderResult(data) {
  latest = data;
  const container = $('#result-content');
  container.className = 'review';
  container.replaceChildren();
  $('#result-tag').textContent = data.label ? 'EXPERIMENTAL MODEL' : 'READY TO READ';
  container.append(element('span', 'review-kicker', 'YOUR READING DESK'), element('h3', '', data.title));
  const meta = element('div', 'review-meta');
  meta.append(element('span', '', `${data.words.toLocaleString()} words`), element('span', '', `${Math.max(1, Math.ceil(data.words / 220))} min read`));
  if (data.source) meta.append(element('span', '', new URL(data.source).hostname));
  container.append(meta, element('div', 'review-preview', data.text.slice(0, 2400) + (data.text.length > 2400 ? '…' : '')));
  const note = element('div', 'model-note');
  const labelNames = {'TRUE': 'True', 'FALSE': 'False', 'HALF-TRUE': 'Half true', 'MOSTLY-TRUE': 'Mostly true', 'MOSTLY-FALSE': 'Mostly false', 'PANTS-FIRE': 'Pants on fire'};
  note.append(element('strong', '', data.label ? `Model prediction: ${labelNames[data.label] || data.label}` : 'Article ready. Model not connected yet.'), element('p', '', data.label ? 'Experimental research model. Training data has source and style biases; unfamiliar topics may be unreliable. This prediction does not verify facts. Check the original evidence.' : 'You can read and prepare articles here. An authenticity prediction will appear once the trained model is connected.'));
  container.append(note);
  const actions = element('div', 'review-actions');
  const copy = element('button', '', 'Copy article');
  copy.type = 'button';
  copy.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(`${data.title}\n\n${data.text}`); copy.textContent = 'Copied'; }
    catch { copy.textContent = 'Copy unavailable'; }
    setTimeout(() => copy.textContent = 'Copy article', 2000);
  });
  actions.append(copy);
  if (data.source) {
    const link = element('a', '', 'Open original ↗');
    link.href = data.source; link.target = '_blank'; link.rel = 'noopener noreferrer';
    actions.append(link);
  }
  container.append(actions);
}
$('#article-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy) return;
  const value = (mode === 'url' ? $('#article-url').value : $('#article-text').value).trim();
  const errorNode = $('#form-error');
  errorNode.hidden = true;
  if (!value || (mode === 'text' && countWords() < 30)) {
    errorNode.textContent = mode === 'url' ? 'Add an article link to get started.' : 'Paste at least 30 words of article text.';
    errorNode.hidden = false;
    return;
  }
  if (mode === 'url') {
    try { if (!['https:', 'http:'].includes(new URL(value).protocol)) throw new Error(); }
    catch { errorNode.textContent = 'Use a complete article URL beginning with https:// or http://.'; errorNode.hidden = false; return; }
  }
  busy = true;
  $('#analyze-button').disabled = true;
  $('#analyze-button').firstElementChild.textContent = 'Taking a closer look…';
  $('#result-panel').setAttribute('aria-busy', 'true');
  $('#result-tag').textContent = 'READING YOUR ARTICLE';
  const content = $('#result-content');
  content.className = 'empty-state'; content.replaceChildren(element('div', 'loading-orbit'), element('h3', '', 'Finding the full story…'), element('p', '', 'Getting your reading workspace ready.'));
  try {
    const response = await fetch('/api/analyze', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ mode, value, title: $('#article-title').value }), signal: AbortSignal.timeout(60000) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'We couldn’t read that article. Please try again.');
    renderResult(data);
  } catch (error) {
    errorNode.textContent = error.name === 'TimeoutError' ? 'This website took too long. Try pasting the article text.' : error instanceof TypeError ? 'Cannot reach the reader. Check your connection and try again.' : error.message;
    errorNode.hidden = false;
    if (latest) renderResult(latest);
    else {
      $('#result-tag').textContent = 'TRY ANOTHER WAY';
      content.replaceChildren(element('h3', '', 'Let’s try that again.'), element('p', '', 'Paste the article text if the link is unavailable.'));
    }
  } finally {
    busy = false;
    $('#analyze-button').disabled = false;
    $('#analyze-button').firstElementChild.textContent = 'Take a closer look';
    $('#result-panel').setAttribute('aria-busy', 'false');
  }
});
const dialog = $('#about-dialog');
document.querySelectorAll('.about-trigger').forEach(button => button.addEventListener('click', () => dialog.showModal()));
$('#close-dialog').addEventListener('click', () => dialog.close());
$('#dialog-done').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) { const box = dialog.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close(); } });
