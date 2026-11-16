"""Export the fitted linear text pipeline for equivalent JavaScript inference."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib

pipeline = joblib.load(ROOT / 'artifacts/pipeline.joblib')
vectorizer = pipeline.named_steps['tfidf']
classifier = pipeline.named_steps['classifier']
assert vectorizer.ngram_range == (1, 2) and vectorizer.sublinear_tf and vectorizer.norm == 'l2'
assert vectorizer.stop_words is None and not vectorizer.binary
assert vectorizer.token_pattern == r'(?u)\b\w\w+\b'
model = {
    'format': 1,
    'source_sha256': hashlib.sha256((ROOT / 'artifacts/pipeline.joblib').read_bytes()).hexdigest(),
    'classes': classifier.classes_.tolist(),
    'vocabulary': {term: int(index) for term, index in vectorizer.vocabulary_.items()},
    'idf': vectorizer.idf_.tolist(),
    'coefficients': classifier.coef_.tolist(),
    'intercepts': classifier.intercept_.tolist(),
}
destination = ROOT / 'netlify/generated'
destination.mkdir(parents=True, exist_ok=True)
(destination / 'model.json').write_text(json.dumps(model, separators=(',', ':')), encoding='utf-8')
print('Exported', len(model['vocabulary']), 'features and', len(model['classes']), 'classes.')
