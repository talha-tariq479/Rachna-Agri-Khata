# Rachna Agri Khata

A digital **khata (ledger) and inventory management system** for an agricultural supplies shop that sells spray, fertiliser and seed to farmers mostly on credit. It replaces the paper khata register with a relational database so balances, stock and daily profit are always visible and never lost.

**Client:** Rachna Agri Supplies — Owner: Arshad Saleem
**Live Demo:** https://rachna-agri-khata.onrender.com

> Developed as a group project for the **Database Systems** course at PUCIT - FCIT.

## Features

- **Secure Login** — admin account with hashed passwords; every page is login-protected
- **Dashboard** — total stock value, total receivables (udhaar), today's sales and low-stock alerts
- **Customers / Khata** — add farmers, view each customer's ledger, record Sale/Credit and Payments, print a khata statement
- **Inventory** — add products with purchase/sale prices and live stock counts
- **Quick Sale** — one-click sale that decreases stock, increases the customer's balance and writes a stock-ledger entry in a single transaction
- **Lending** — list of all customers with outstanding balances, with Reliable/Overdue status
- **Reports** — today's sales and today's profit, calculated with a 3-table JOIN
- **Backup** — download a copy of the database

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (Jinja2 templates) |
| Backend | Python, Flask, Flask-SQLAlchemy, Gunicorn |
| Database | PostgreSQL (Neon cloud) in production, SQLite for local development |
| Hosting | Render (connected to this GitHub repository) |

## Database Design

5 tables — `users`, `customers`, `inventory`, `transactions`, `stock_ledger` — connected with foreign keys:

- One **customer** has many **transactions** (`transactions.customer_id → customers.id`)
- One **transaction** generates many **stock_ledger** entries (`stock_ledger.transaction_id → transactions.id`)
- One **product** appears in many **stock_ledger** entries (`stock_ledger.product_id → inventory.id`)

## Team

| Name | Roll No | Responsibility |
|---|---|---|
| Talha Tariq | BCSF25A531 | System architecture, backend, database, dashboard, deployment |
| Awais Haider | BCSF25A537 | Customers module (frontend) |
| Mahad Bin Said | BCSF25A548 | Inventory & Reports module (frontend) |

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 and register the first admin account. Locally the app uses SQLite (`khata.db`); on Render it uses the PostgreSQL database URL provided by Neon.
