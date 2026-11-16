# News Authenticity Predictor | Margin

**Live app: [margin-news-authenticity.netlify.app](https://margin-news-authenticity.netlify.app)**

Margin is a news classification project with a responsive web interface, a trained machine learning pipeline, and a serverless deployment on Netlify. Submit a public article URL or paste an article to read its content and see a predicted truthfulness category.

> This is an experimental research project. Predictions reflect patterns in the training data; they do not independently verify claims or establish whether an article is true.

## Features

- **Links and pasted text:** extract articles from public webpages or submit text directly.
- **Six categories:** True, Mostly true, Half true, Mostly false, Pants on fire, and False.
- **Reading workspace:** article preview, word count, reading time, copy action, and original source link.
- **Responsive design:** an editorial interface with accessible tabs, loading states, and input validation.
- **Local and hosted runtimes:** run with Python locally or use Netlify's JavaScript functions.
- **Consistent inference:** a complete Python pipeline and an equivalent JavaScript model export.

The application does not store article history. Submitted articles are sent to the app server for processing. Paywalled, blocked, or unusually structured pages may require pasting the text instead.

## How it works

1. Accept pasted text or extract the headline and body from an article URL.
2. Normalize the content, filter explicit rating sentences and ruling sections, and remove selected source markers.
3. Transform the text using the fitted TF-IDF vocabulary of unigrams and bigrams, sublinear term frequency, and L2 normalization.
4. Predict a string label using a class-balanced linear support vector classifier (`LinearSVC`).
5. Display the article alongside an explicitly experimental prediction.

The model does not search for supporting evidence, compare sources, or perform live fact-checking.

## Dataset and results

Six CSV datasets contain `headline`, `text`, and `label` columns, totaling **26,068 rows**. Training retains **25,932 articles** after filtering short or missing content, removing conflicting duplicate bodies, and deduplicating cleaned article bodies.

| Item | Configuration or result |
| --- | --- |
| Classifier | Class-balanced `LinearSVC`, `C=1.0` |
| Features | TF-IDF unigrams and bigrams; up to 60,000 features |
| Training articles | 20,745 |
| Held-out evaluation articles | 5,187 |
| Split | Stratified 80/20 split, random seed 42 |
| Held-out accuracy | **88.53%** |
| Held-out macro-F1 | **0.741** |

The vectorizer is fitted only on training articles. The saved model is not refitted on the held-out evaluation split. See [evaluation.json](artifacts/evaluation.json) for per-class metrics and the confusion matrix.

### Limitations

- The data mixes original news with fact-check reports about other people's claims, so labels do not have a consistent meaning across every article type.
- Explicit verdict text is filtered, but indirect verdict cues and publisher/style shortcuts may remain.
- The evaluation split shares the source collection used for training. These scores do not establish performance on unseen publishers or future news.
- Middle truth categories perform substantially worse than True and False; overall accuracy hides this difference.
- Coverage is largely political news and fact-checking. Predictions on unfamiliar subjects, such as astronomy, may be unreliable.

The original [research notebook](NewsAuthenticityPredictor.ipynb) compares multiple classifiers and imbalance techniques. Its historical outputs come from an earlier workflow with evaluation and inference issues. The results above describe the current `train_model.py` pipeline, rather than the notebook's saved scores.

## Technology

| Layer | Tools |
| --- | --- |
| Interface | HTML, CSS, vanilla JavaScript |
| Training | Python, pandas, scikit-learn, joblib |
| Local API and extraction | Python HTTP server, newspaper3k |
| Hosted API | Netlify Functions, Node.js 22 |
| Hosted article extraction | Mozilla Readability, linkedom |
| Hosting | Netlify |

The interface has no frontend build step. Fonts load from Google Fonts with local fallbacks. On Netlify, the exported TF-IDF and SVM parameters run directly in JavaScript, so a separate Python hosting service or running local computer is unnecessary.

## Run locally

These commands use PowerShell, Python 3.12, and [uv](https://docs.astral.sh/uv/).

```powershell
git clone https://github.com/abuhurarah524/news-authenticity-predictor.git
cd news-authenticity-predictor
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python.exe train_model.py
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:8000**. Use **Try a sample article**, or provide your own link or text.

Training generates `artifacts/pipeline.joblib` and `artifacts/evaluation.json`. The Python model binary is excluded from Git, so train it after a fresh clone. Without a model, the local app can still prepare articles and explicitly reports that predictions are unavailable. Only load trusted joblib files.

## Test the Netlify runtime

With Node.js 22 or later installed, export the trained model and generate Python comparison fixtures:

```powershell
.\.venv\Scripts\python.exe scripts\export_model.py
.\.venv\Scripts\python.exe scripts\parity_fixtures.py
npm ci
npm test
```

Tests cover Python/JavaScript prediction parity, article extraction, private-network URL rejection, API responses, and invalid inputs. The current parity suite compares **155 examples**, including labels and decision scores.

Use `npm run preview` for a local preview of the Netlify runtime.

## Netlify deployment

**Production: [https://margin-news-authenticity.netlify.app](https://margin-news-authenticity.netlify.app)**

The deployment is configured in `netlify.toml`:

| Setting | Value |
| --- | --- |
| Publish directory | `web` |
| Functions directory | `netlify/functions` |
| Exported model | `netlify/generated/model.json` |
| Health endpoint | `GET /api/status` |
| Prediction endpoint | `POST /api/analyze` |

After retraining, regenerate the export and rerun the tests above. Then sign in, link the intended project, and deploy:

```powershell
npx netlify login
npx netlify link
npm run deploy
```

A Netlify account is required for serverless functions. Deploy the complete project through the CLI: uploading only `web/` through Netlify Drop will not deploy the prediction and extraction APIs.

For the prepared Windows checkout, `scripts/netlify.ps1` provides `login`, `status`, and `deploy` commands using the portable Node runtime. `scripts/setup_node.py` downloads and verifies that runtime when needed.

## Project structure

```text
app.py                         Local Python web server and API
model_text.py                  Shared Python text preprocessing
train_model.py                 Model training and held-out evaluation
NewsAuthenticityPredictor.ipynb Original research and model comparisons
*.csv                          Six labeled source datasets
artifacts/
  pipeline.joblib              Generated Python pipeline (ignored by Git)
  evaluation.json              Current evaluation results
web/                           Interface HTML, CSS, and JavaScript
netlify/
  functions/                   Hosted status and prediction endpoints
  lib/                         JavaScript inference and article extraction
  generated/model.json         Exported deployment model
scripts/                       Export, test-fixture, and deployment helpers
tests/netlify.test.mjs          JavaScript inference and API tests
netlify.toml                   Hosting configuration
requirements.txt               Python dependencies
package.json                   JavaScript dependencies and commands
```

## License

Project code is provided under the [MIT License](LICENSE). Dataset provenance and third-party article rights should be checked separately before reuse or redistribution.
