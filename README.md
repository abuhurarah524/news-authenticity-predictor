# News Authenticity Predictor · Margin

Margin is a local web interface for reading and reviewing articles. It accepts a public article URL or pasted text, extracts the story, and displays a reading workspace.

## Run

From the project directory on Windows:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:8000**. Select **Paste text**, or use **Try a sample article** to explore without fetching a website. Article history is not stored.

## Environment

Python 3.12 is recommended. Dependencies are listed in `requirements.txt`:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

The interface uses HTML, CSS, and JavaScript without a frontend build step. Fonts load from Google Fonts, with local serif and sans-serif fallbacks. Article extraction uses `newspaper3k`.

## Model connection

Train and connect the experimental model with:

```powershell
.\.venv\Scripts\python.exe train_model.py
```

This saves the complete raw-text pipeline to `artifacts/pipeline.joblib` and held-out metrics to `artifacts/evaluation.json`. It removes explicit rating sentences and ruling sections, deduplicates cleaned article bodies, drops conflicting duplicate bodies, and fits TF-IDF only on the training split. The saved model retains its untouched 20% evaluation split; it is not refit on evaluation examples. The server detects model-file updates automatically.

The interface does not invent authenticity scores. With no model installed, articles remain readable and the result clearly indicates that classification is unavailable.

To enable classification, save a trusted, trained scikit-learn pipeline to `artifacts/pipeline.joblib`. It must accept a list of raw strings, include all fitted preprocessing and vectorization, and return string labels from `predict`. The notebook's standalone classifier pickle is incompatible with this contract because it does not include its feature transformations. Load only trusted model files.

The existing research datasets include verdict text and source shortcuts. Correct the data and evaluate a complete pipeline on held-out data before presenting its predictions as meaningful. Predictions are research outputs, not fact verification.

## Netlify deployment

Netlify serves `web/` and the JavaScript functions configured in `netlify.toml`. The exported TF-IDF vocabulary, IDF values, and SVM coefficients run directly in Node.js; a separate Python server is not needed. Article extraction uses Mozilla Readability. The URL fetcher validates public addresses, pins DNS results, checks redirects, and limits response sizes.

After retraining, regenerate the deployment model and parity fixtures:

```powershell
.\.venv\Scripts\python.exe scripts\export_model.py
.\.venv\Scripts\python.exe scripts\parity_fixtures.py
npm install
npm test
```

To deploy, sign in to your Netlify account and run:

```powershell
npx netlify login
npm run deploy
```

For an existing Netlify project, run `npx netlify link` first. A Netlify account is required for serverless functions. The publish directory is `web`; the functions directory is `netlify/functions`. The generated model in `netlify/generated/model.json` must be included. Do not deploy only the HTML folder through Netlify Drop, because the prediction and extraction APIs also need deployment.

On this Windows checkout, the portable runtime is available through `scripts/netlify.ps1`. Use `.\scripts\netlify.ps1 login` to authorize the CLI and `.\scripts\netlify.ps1 deploy` to publish without installing Node globally.

## Source files

- `app.py`: local HTTP server and article extraction API.
- `web/`: responsive interface, input validation, and result rendering.
- `NewsAuthenticityPredictor.ipynb`: original research notebook.
- `requirements.txt`: Python dependencies.
