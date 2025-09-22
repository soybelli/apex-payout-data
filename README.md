# Apex Payouts Scraper & Analytics

This project scrapes payout data from `apextraderfunding.com` and provides a Streamlit web app for analysis by country and month.

## Contents
- `scrape_payouts.js`: Puppeteer scraper to generate `payouts.csv` (pages 1..307)
- `payouts.csv`: Generated CSV (ignored by Git)
- `app.py`: Streamlit app with tables and charts
- `requirements.txt`: Python dependencies

## Run the Streamlit app

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Scrape data (optional)

```bash
npm install
node scrape_payouts.js
```

CSV will be written to `payouts.csv` in the project root.

## Deployment (Streamlit Cloud)
- Push this repo to GitHub
- On Streamlit Cloud, set the app entrypoint to `app.py`
- Ensure `requirements.txt` is present
- Upload `payouts.csv` as a dataset or point to a hosted CSV
