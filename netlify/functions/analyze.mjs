import { predict } from '../lib/model.mjs';
import { extractArticle } from '../lib/article.mjs';

export default async function (request) {
  const reply = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
  if (request.method !== 'POST') return reply({ error: 'Use POST to submit an article.' }, 405);
  try {
    // Bound the stream even when Content-Length is absent or incorrect.
    const reader = request.body?.getReader();
    if (!reader) return reply({ error: 'Add an article to review.' }, 400);
    let size = 0; const chunks = [];
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 120000) { await reader.cancel(); return reply({ error: 'Please submit an article under 120 KB.' }, 413); }
      chunks.push(Buffer.from(value));
    }
    let payload;
    try { payload = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
    catch { return reply({ error: 'Submit a valid article request.' }, 400); }
    if (!payload || typeof payload !== 'object') return reply({ error: 'Submit a valid article request.' }, 400);
    const value = String(payload.value || '').trim();
    let article;
    if (payload.mode === 'url') article = await extractArticle(value);
    else if (payload.mode === 'text') article = { title: String(payload.title || '').trim().slice(0, 300) || 'Untitled article', text: value, source: '' };
    else return reply({ error: 'Choose an article link or article text.' }, 400);
    const words = article.text.split(/\s+/).filter(Boolean).length;
    if (words < 30) return reply({ error: 'We need at least 30 words. Try pasting the full article.' }, 400);
    const { label } = predict(`${article.title} ${article.text}`);
    return reply({ ...article, words, model_ready: true, experimental: true, label });
  } catch (error) {
    console.error('Article analysis failed:', error.message);
    return reply({ error: 'We could not read this article. Try pasting its text instead.' }, 422);
  }
}
