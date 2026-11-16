"""Build local-only regression examples from the original fitted Python model."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
import pandas as pd
from model_text import clean_text

pipeline = joblib.load(ROOT / 'artifacts/pipeline.joblib')
examples = []
for path in ROOT.glob('*.csv'):
    data = pd.read_csv(path, dtype=str).dropna(subset=['headline', 'text'])
    examples.extend((data['headline'] + ' ' + data['text']).sample(n=min(25, len(data)), random_state=42).tolist())
examples.extend([
    'Café naïve Straße İstanbul ½ ① café_123 A I a_ — The evidence matters.',
    'Reuters &amp; researchers &#39;said&#39; the result is real. We rate this claim Mostly False. Our ruling Something else.',
    'Astronomers observed a distant star with an infrared telescope. Further research is needed.',
    'Numbers 2025 10 42 and words with_accents éé 漢字. The headline is not the whole story.',
    '',
])
labels = pipeline.predict(examples)
scores = pipeline.decision_function(examples)
fixtures = [{'text': text, 'cleaned': clean_text(text), 'label': str(label), 'scores': score.tolist()}
            for text, label, score in zip(examples, labels, scores)]
(ROOT / '.tools').mkdir(exist_ok=True)
(ROOT / '.tools/model-parity.json').write_text(json.dumps(fixtures, ensure_ascii=False), encoding='utf-8')
print('Created', len(fixtures), 'Python regression examples.')
