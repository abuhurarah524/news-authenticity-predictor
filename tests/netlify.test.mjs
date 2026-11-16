import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { cleanText, predict } from '../netlify/lib/model.mjs';
import { parseArticle, resolvePublicURL } from '../netlify/lib/article.mjs';
import analyze from '../netlify/functions/analyze.mjs';
import status from '../netlify/functions/status.mjs';

test('JavaScript inference matches the fitted Python pipeline', () => {
  const fixtures = JSON.parse(readFileSync('.tools/model-parity.json', 'utf8'));
  for (const fixture of fixtures) {
    assert.equal(cleanText(fixture.text), fixture.cleaned);
    const result = predict(fixture.text);
    assert.equal(result.label, fixture.label);
    result.scores.forEach((score, index) => assert.ok(Math.abs(score - fixture.scores[index]) < 1e-9));
  }
});

test('article extraction returns story text, not markup', () => {
  const text = 'Neighbours are collecting books for a community reading room. Volunteers meet each Saturday to organise the shelves and welcome new visitors. '.repeat(20);
  const result = parseArticle(`<html><head><title>Community reading room</title></head><body><article><h1>Community reading room</h1><p>${text}</p></article></body></html>`, 'https://example.com/article');
  assert.equal(result.title, 'Community reading room');
  assert.ok(result.text.includes('Volunteers meet'));
  assert.ok(!result.text.includes('<p>'));
});

test('article fetching rejects private networks and unsafe schemes', async () => {
  for (const url of ['http://127.0.0.1', 'http://[::1]/', 'http://169.254.169.254/', 'file:///etc/passwd', 'https://user:pass@example.com']) {
    await assert.rejects(resolvePublicURL(url));
  }
});

test('deployed API returns the model label with the experimental flag', async () => {
  const text = 'Astronomers used an infrared telescope to observe a distant star and the cloud of dust around it. They compared several images and described the observations in a research paper. Further measurements will help explain the structures.';
  const response = await analyze(new Request('https://margin.example/api/analyze', { method: 'POST', body: JSON.stringify({ mode: 'text', value: text, title: 'A distant star' }) }));
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.label, predict(`A distant star ${text}`).label);
  assert.equal(result.experimental, true);
  assert.equal(result.model_ready, true);
  assert.equal((await (await status()).json()).model_ready, true);
});

test('API rejects malformed, short, and oversized input', async () => {
  const submit = (body) => analyze(new Request('https://margin.example/api/analyze', { method: 'POST', body }));
  assert.equal((await submit('{')).status, 400);
  assert.equal((await submit(JSON.stringify({ mode: 'text', value: 'Too short.' }))).status, 400);
  assert.equal((await submit('x'.repeat(120001))).status, 413);
  assert.equal((await analyze(new Request('https://margin.example/api/analyze'))).status, 405);
});
