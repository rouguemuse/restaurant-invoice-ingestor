"""Core Normalization and Price Creep Watchdog Engine for Restaurant Invoices."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Any

# Standard Foodservice Master Ingredients & Baseline Benchmark Prices
BASELINE_DATABASE = {
    "Beef Tenderloin / Filet": {"category": "Proteins", "unit": "lb", "base_price": 18.50},
    "Ground Beef (80/20)": {"category": "Proteins", "unit": "lb", "base_price": 4.25},
    "Chicken Breast (Boneless)": {"category": "Proteins", "unit": "lb", "base_price": 3.40},
    "Atlantic Salmon Fillet": {"category": "Proteins", "unit": "lb", "base_price": 11.20},
    "Bacon (Thick Cut)": {"category": "Proteins", "unit": "lb", "base_price": 4.80},
    "Jumbo Shrimp (16/20)": {"category": "Proteins", "unit": "lb", "base_price": 9.50},
    "Heavy Cream (36%)": {"category": "Dairy", "unit": "quart", "base_price": 4.20},
    "Whole Milk": {"category": "Dairy", "unit": "gallon", "base_price": 3.60},
    "Unsalted Butter": {"category": "Dairy", "unit": "lb", "base_price": 3.90},
    "Shredded Mozzarella": {"category": "Dairy", "unit": "lb", "base_price": 3.60},
    "Russet Potatoes": {"category": "Produce", "unit": "lb", "base_price": 0.75},
    "Yellow Onions": {"category": "Produce", "unit": "lb", "base_price": 0.85},
    "Roma Tomatoes": {"category": "Produce", "unit": "lb", "base_price": 1.65},
    "Romaine Lettuce": {"category": "Produce", "unit": "head", "base_price": 1.40},
    "Brioche Burger Buns": {"category": "Bakery", "unit": "pack (12)", "base_price": 6.00},
    "Extra Virgin Olive Oil": {"category": "Pantry", "unit": "liter", "base_price": 9.80},
    "Canola Oil (Fryer)": {"category": "Pantry", "unit": "gallon", "base_price": 7.20},
}

VENDOR_ALIASES = {
    "beef tenderloin": "Beef Tenderloin / Filet",
    "filet mignon": "Beef Tenderloin / Filet",
    "bf strip loin": "Beef Tenderloin / Filet",
    "ground beef": "Ground Beef (80/20)",
    "beef ground": "Ground Beef (80/20)",
    "gnd beef 80 20": "Ground Beef (80/20)",
    "beef gnd 80/20": "Ground Beef (80/20)",
    "chicken breast": "Chicken Breast (Boneless)",
    "chk brst bnls": "Chicken Breast (Boneless)",
    "salmon fillet": "Atlantic Salmon Fillet",
    "atl salmon": "Atlantic Salmon Fillet",
    "bacon thick": "Bacon (Thick Cut)",
    "bacon thk cut": "Bacon (Thick Cut)",
    "shrimp jumbo": "Jumbo Shrimp (16/20)",
    "heavy cream": "Heavy Cream (36%)",
    "butter unsalted": "Unsalted Butter",
    "unsalted butter": "Unsalted Butter",
    "russet potato": "Russet Potatoes",
    "potato russet": "Russet Potatoes",
    "yellow onion": "Yellow Onions",
    "brioche bun": "Brioche Burger Buns",
    "olive oil": "Extra Virgin Olive Oil",
}


def normalize_item_name(raw_text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9 ]", " ", raw_text.lower())
    for alias, standard_name in VENDOR_ALIASES.items():
        if alias in clean:
            return standard_name

    master_list = list(BASELINE_DATABASE.keys())
    match = difflib.get_close_matches(raw_text, master_list, n=1, cutoff=0.55)
    return match[0] if match else raw_text.strip()


def parse_pack_size(raw_desc: str, default_qty: float = 1.0, default_unit: str = "case") -> tuple[float, str]:
    match = re.search(r"(\d+)\s*/\s*(\d+(\.\d+)?)\s*#", raw_desc)
    if match:
        return float(match.group(1)) * float(match.group(2)), "lb"

    match_lb = re.search(r"(\d+(\.\d+)?)\s*(lb|lbs|#)", raw_desc.lower())
    if match_lb:
        return float(match_lb.group(1)), "lb"

    return default_qty, default_unit


def process_invoice_data(vendor: str, invoice_number: str, invoice_date: str, lines: list[dict]) -> dict[str, Any]:
    processed_items = []
    creep_alerts = []
    total_invoice_cost = 0.0

    for line in lines:
        raw_desc = line.get("description", "")
        qty = float(line.get("quantity", 1.0))
        unit = line.get("unit", "each")
        total_paid = float(line.get("total_paid", 0.0))

        # Check pack multiplier inside description if unit is case
        if unit.lower() in ("cs", "case"):
            qty, unit = parse_pack_size(raw_desc, qty, unit)

        standard_name = normalize_item_name(raw_desc)
        unit_price = round(total_paid / qty, 4) if qty > 0 else 0.0
        total_invoice_cost += total_paid

        base_info = BASELINE_DATABASE.get(standard_name, {"category": "Other", "unit": unit, "base_price": unit_price})
        base_price = base_info["base_price"]
        creep_pct = round((unit_price - base_price) / base_price, 4) if base_price > 0 else 0.0
        price_diff = round(unit_price - base_price, 4)

        status = "STABLE"
        if creep_pct >= 0.10:
            status = "CRITICAL_SPIKE"
            creep_alerts.append({
                "item": standard_name,
                "vendor": vendor,
                "base_price": base_price,
                "new_price": unit_price,
                "creep_pct": creep_pct,
                "annualized_risk": round(price_diff * 52 * 25, 2),
                "severity": "critical"
            })
        elif creep_pct >= 0.05:
            status = "PRICE_CREEP"
            creep_alerts.append({
                "item": standard_name,
                "vendor": vendor,
                "base_price": base_price,
                "new_price": unit_price,
                "creep_pct": creep_pct,
                "annualized_risk": round(price_diff * 52 * 25, 2),
                "severity": "warning"
            })

        processed_items.append({
            "date": invoice_date,
            "vendor": vendor,
            "invoice_number": invoice_number,
            "raw_description": raw_desc,
            "standard_item": standard_name,
            "quantity": qty,
            "unit": unit,
            "total_paid": total_paid,
            "unit_price": unit_price,
            "base_price": base_price,
            "creep_pct": creep_pct,
            "status": status,
        })

    return {
        "invoice_number": invoice_number,
        "vendor": vendor,
        "date": invoice_date,
        "total_amount": round(total_invoice_cost, 2),
        "items_count": len(processed_items),
        "creep_alerts_count": len(creep_alerts),
        "items": processed_items,
        "alerts": creep_alerts,
    }
