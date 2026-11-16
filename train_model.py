"""Train the raw-text pipeline used by Margin; emit a held-out evaluation."""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from model_text import clean_text

ROOT = Path(__file__).resolve().parent
FILES = ['true_news.csv', 'fake_news.csv', 'half-true.csv', 'mostly-true.csv',
         'mostly-false.csv', 'pants-on-fire.csv']


def train():
    frames = [pd.read_csv(ROOT / filename, dtype=str)[['headline', 'text', 'label']]
              for filename in FILES]
    data = pd.concat(frames, ignore_index=True).dropna().copy()
    original_count = len(data)
    data['label'] = data['label'].str.strip().str.upper()
    # Deduplicate the body after cleaning so copied stories cannot cross splits.
    data['body_key'] = data['text'].map(clean_text).str.replace(r'\W+', ' ', regex=True).str.strip()
    conflicting = data.groupby('body_key')['label'].nunique()
    conflict_keys = set(conflicting[conflicting > 1].index)
    data = data[~data['body_key'].isin(conflict_keys)]
    data = data[data['body_key'].str.split().str.len() >= 30]
    data = data.drop_duplicates('body_key')
    raw = data['headline'] + ' ' + data['text']
    x_train, x_test, y_train, y_test = train_test_split(
        raw, data['label'], test_size=.2, random_state=42, stratify=data['label'])
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(preprocessor=clean_text, ngram_range=(1, 2),
                                 min_df=3, max_df=.98, max_features=60000, sublinear_tf=True)),
        ('classifier', LinearSVC(C=1.0, class_weight='balanced', max_iter=10000, random_state=42)),
    ])
    print(f'Training on {len(x_train):,} articles; holding out {len(x_test):,}.', flush=True)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    labels = pipeline.classes_.tolist()
    report = {
        'trained_at': datetime.now(timezone.utc).isoformat(),
        'sklearn_version': sklearn.__version__,
        'model': 'TF-IDF (unigrams + bigrams) + balanced LinearSVC',
        'experimental': True,
        'limitations': [
            'Random stratified holdout uses the same source collection as training; it does not establish publisher or temporal generalization.',
            'Data mixes original news with fact-check reports and contains source/style shortcuts.',
            'Explicit rating sentences and ruling sections are filtered, but other verdict cues may remain.',
            'Predictions are dataset labels, not factual verification. Unrelated domains such as astronomy may be outside training coverage.',
        ],
        'input_rows': original_count, 'retained_rows': len(data),
        'conflicting_body_groups_removed': len(conflict_keys),
        'train_rows': len(x_train), 'test_rows': len(x_test), 'random_state': 42,
        'classes': labels, 'class_counts': data['label'].value_counts().to_dict(),
        'accuracy': accuracy_score(y_test, predictions),
        'classification_report': classification_report(y_test, predictions, output_dict=True, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, predictions, labels=labels).tolist(),
    }
    destination = ROOT / 'artifacts'
    destination.mkdir(exist_ok=True)
    temporary = destination / 'pipeline.tmp.joblib'
    joblib.dump(pipeline, temporary, compress=3)
    restored = joblib.load(temporary)
    assert list(restored.predict(x_test.iloc[:20])) == list(predictions[:20])
    temporary.replace(destination / 'pipeline.joblib')
    (destination / 'evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(classification_report(y_test, predictions, zero_division=0), flush=True)
    print('Saved artifacts/pipeline.joblib and artifacts/evaluation.json', flush=True)


if __name__ == '__main__':
    train()
