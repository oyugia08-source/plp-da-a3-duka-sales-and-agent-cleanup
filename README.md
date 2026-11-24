README.md

# Duka Electronics & Mobile Money Agent Network Analysis

## Overview
This repository covers two data analysis engagements:
1. **Duka Electronics (H1 2026):** Exploratory sales analysis across branches, sales channels, products, price bands, weekdays vs. weekends, and monthly trends, plus an Excel branch summary workbook and a filtered CSV export.
2. **Mobile Money Agent Network:** Automated, non-hardcoded cleaning and audit of raw agent transactions (`cleaning_pipeline.py`), enrichment with agent county data, summary tables, a six-dimension Data Quality Report, and a cleaned transaction export.

## Duka Electronics Executive Summary
1. Duka Electronics recorded `<N>` orders across January–June 2026 under seed `2026`.
2. Total H1 2026 revenue reached KES `<amount>` across `<M>` branches and `<K>` sales channels.
3. `<Top Branch>` generated the highest revenue at KES `<amount>` (`<X>%` of total revenue).
4. `<Top Product>` led order volume with `<N>` orders and generated KES `<amount>` in revenue.
5. Weekend orders contributed `<X>%` of total revenue, while `<N>` orders fell into the `Premium` price band.

## Agent Network Row Counts
- **Before cleaning (`agent_transactions.csv`):** `<before_rows>` rows
- **After cleaning & merge (`outputs/agent_transactions_clean.csv`):** `<after_rows>` rows

## How to Regenerate Data & Run Notebooks
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
