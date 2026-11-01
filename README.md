# Restaurant Invoice Ingestor & Price Creep Watchdog (Vercel-Ready)

A modern, serverless web app and normalization API built for restaurants, cafes, bakeries, and food trucks. Ingests supplier delivery invoices (Sysco, US Foods, purveyors), normalizes vendor item shorthand, calculates cost per unit, and detects distributor **Price Creep** before margins erode.

---

## 🚀 Features

* **Supplier Normalization Engine:** Automatically converts supplier invoice codes (e.g., `SYSCO BRAND - BEEF GND 80/20 CH - 60# CS`) into standardized master ingredients.
* **Pack Size & Multiplier Unpacker:** Parses pack quantities like `4/10# CS` $\rightarrow$ 40 lbs.
* **Price Creep Watchdog:** Instantly flags when a purveyor increases prices by $>5\%$ (Warning) or $>10\%$ (Critical Spike) against baseline rates.
* **Serverless Architecture:** Ready to deploy to **Vercel** with a single click.

---

## ⚡ Deployment to Vercel

### Option 1: Using Vercel CLI
```bash
npm i -g vercel
vercel
```

### Option 2: Push to GitHub & Connect to Vercel
1. Create a repository on GitHub (e.g. `restaurant-invoice-ingestor`).
2. Push this directory:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/restaurant-invoice-ingestor.git
   git push -u origin main
   ```
3. In [Vercel Dashboard](https://vercel.com/new), select "Import Git Repository" and click **Deploy**.

---

## 💻 Local Development

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload
```
Open `http://127.0.0.1:8000` in your browser.

---

## 📜 License
MIT License
