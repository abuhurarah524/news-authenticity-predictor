"""Local web interface. Run with the project's virtual-environment Python."""
import ipaddress
import json
from pathlib import Path
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'artifacts' / 'pipeline.joblib'
_model_lock = threading.Lock()
_cached_model = None
_cached_stamp = None


def predict_label(text):
    global _cached_model, _cached_stamp
    import joblib
    with _model_lock:
        stamp = MODEL.stat().st_mtime_ns
        if _cached_model is None or stamp != _cached_stamp:
            _cached_model = joblib.load(MODEL)
            _cached_stamp = stamp
        return str(_cached_model.predict([text])[0])


def public_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Enter a public article URL beginning with https:// or http://.')
    if parsed.port not in (None, 80, 443):
        raise ValueError('Use an article URL on a standard web port.')
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    if any(not ipaddress.ip_address(entry[4][0]).is_global for entry in addresses):
        raise ValueError('Please use a public news website.')
    return value


def extract_article(url):
    import requests
    from newspaper import Article
    for _ in range(6):
        public_url(url)
        with requests.get(url, timeout=(8, 20), allow_redirects=False, stream=True,
                          headers={'User-Agent': 'Mozilla/5.0 (compatible; MarginReader/1.0)'}) as response:
            if response.is_redirect:
                from urllib.parse import urljoin
                url = urljoin(url, response.headers['Location'])
                continue
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > 3_000_000:
                    raise ValueError('This page is too large. Paste the article text instead.')
                chunks.append(chunk)
            article = Article(url)
            article.set_html(b''.join(chunks).decode(response.encoding or 'utf-8', errors='replace'))
            article.parse()
            return article.title, article.text, url
    raise ValueError('This website redirected too many times. Paste the article text instead.')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'web'), **kwargs)

    def send_json(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/status':
            return self.send_json({'model_ready': MODEL.exists(), 'experimental': True})
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/analyze':
            return self.send_json({'error': 'Not found.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 120_000:
                raise ValueError('Please submit an article under 120 KB.')
            payload = json.loads(self.rfile.read(length))
            mode, value = payload.get('mode'), str(payload.get('value', '')).strip()
            if mode == 'url':
                title, text, source = extract_article(value)
            elif mode == 'text':
                title, text, source = str(payload.get('title', '')).strip() or 'Untitled article', value, ''
            else:
                raise ValueError('Choose an article link or article text.')
            if len(text.split()) < 30:
                raise ValueError('We need at least 30 words to work with. Try pasting the full article.')
            result = {'title': title, 'text': text, 'source': source,
                      'words': len(text.split()), 'model_ready': MODEL.exists(), 'label': None}
            if MODEL.exists():
                result['label'] = predict_label(title + ' ' + text)
                result['experimental'] = True
            return self.send_json(result)
        except ValueError as error:
            return self.send_json({'error': str(error)}, 400)
        except Exception:
            return self.send_json({'error': 'We could not read this article. Try pasting its text instead.'}, 422)


if __name__ == '__main__':
    print('Margin is running at http://127.0.0.1:8000', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
