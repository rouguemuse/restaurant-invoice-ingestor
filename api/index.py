"""FastAPI serverless entrypoint for Vercel deployment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.scanner import process_invoice_data

app = FastAPI(
    title="Restaurant Invoice Ingestor & Price Creep Watchdog",
    description="Automated vendor invoice normalization and price creep alerting API for restaurants.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceLinePayload(BaseModel):
    description: str
    quantity: float
    unit: str = "case"
    total_paid: float


class IngestInvoiceRequest(BaseModel):
    vendor: str
    invoice_number: str
    invoice_date: str
    lines: list[InvoiceLinePayload]


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "restaurant-invoice-ingestor"}


@app.post("/api/scan")
def scan_invoice(payload: IngestInvoiceRequest) -> dict[str, Any]:
    lines_dict = [l.model_dump() for l in payload.lines]
    res = process_invoice_data(payload.vendor, payload.invoice_number, payload.invoice_date, lines_dict)
    return res


@app.get("/", response_class=HTMLResponse)
def index_view():
    html_path = Path(__file__).resolve().parent.parent / "public" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Restaurant Invoice Ingestor API running.</h1>"
