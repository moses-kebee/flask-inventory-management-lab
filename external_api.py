#!/usr/bin/env python3
"""
External API integration - OpenFoodFacts

Wraps calls to the OpenFoodFacts public API so the rest of the app
(Flask routes, CLI) doesn't need to know about request/response details.
Docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
"""

import requests

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 10  # seconds


def fetch_product_by_barcode(barcode):
    """
    Fetch a single product by its barcode.

    Returns a dict with a simplified subset of product fields, or None
    if the product wasn't found or the request failed.
    """
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"

    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None

    data = response.json()

    # OpenFoodFacts returns status: 0 when the barcode isn't found
    if data.get("status") != 1:
        return None

    product = data.get("product", {})

    return {
        "product_name": product.get("product_name", "Unknown"),
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "barcode": barcode,
    }


def search_products_by_name(query, page_size=10):
    """
    Search OpenFoodFacts for products matching a name/keyword.

    Returns a list of simplified product dicts, or None if the request
    failed outright (as opposed to just returning zero results).
    """
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
    }

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None

    data = response.json()
    products = data.get("products", [])

    return [
        {
            "product_name": p.get("product_name", "Unknown"),
            "brands": p.get("brands", ""),
            "ingredients_text": p.get("ingredients_text", ""),
            "barcode": p.get("code", ""),
        }
        for p in products
    ]
