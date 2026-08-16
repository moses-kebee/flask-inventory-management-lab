#!/usr/bin/env python3
"""
Inventory Management System - Flask REST API

Provides CRUD endpoints for managing inventory items, plus a helper
route that queries the OpenFoodFacts API to fetch real product data
by barcode, which can then be added directly to the inventory.
"""

from flask import Flask, jsonify, request
from external_api import fetch_product_by_barcode, search_products_by_name

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory "database" - a simple list simulating persistent storage.
# Each item is a dict with at least: id, product_name, brands, price, quantity
# ---------------------------------------------------------------------------
inventory = [
    {
        "id": 1,
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "ingredients_text": "Filtered water, almonds, cane sugar",
        "barcode": "0025293001165",
        "price": 3.99,
        "quantity": 25,
    },
    {
        "id": 2,
        "product_name": "Dark Chocolate Bar",
        "brands": "Lindt",
        "ingredients_text": "Cocoa mass, sugar, cocoa butter",
        "barcode": "3046920029759",
        "price": 2.49,
        "quantity": 40,
    },
]


def find_item(item_id):
    """Helper to locate an inventory item by id. Returns None if not found."""
    return next((item for item in inventory if item["id"] == item_id), None)


def next_id():
    """Generate the next available id (max existing id + 1, or 1 if empty)."""
    return max((item["id"] for item in inventory), default=0) + 1


# ---------------------------------------------------------------------------
# Root route
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the Inventory Management API"}), 200


# ---------------------------------------------------------------------------
# CRUD routes for /inventory
# ---------------------------------------------------------------------------
@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Return all inventory items."""
    return jsonify(inventory), 200


@app.route("/inventory/<int:id>", methods=["GET"])
def get_inventory_item(id):
    """Return a single inventory item by id, or 404 if not found."""
    item = find_item(id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def create_inventory_item():
    """
    Create a new inventory item from JSON input.
    Required field: product_name
    Optional fields: brands, ingredients_text, barcode, price, quantity
    """
    data = request.get_json()

    if not data or "product_name" not in data or not data["product_name"]:
        return jsonify({"error": "product_name is required"}), 400

    new_item = {
        "id": next_id(),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "barcode": data.get("barcode", ""),
        "price": data.get("price", 0.0),
        "quantity": data.get("quantity", 0),
    }
    inventory.append(new_item)

    return jsonify(new_item), 201


@app.route("/inventory/<int:id>", methods=["PATCH"])
def update_inventory_item(id):
    """
    Update one or more fields of an existing inventory item.
    Accepts a partial JSON body - only provided fields are updated.
    """
    item = find_item(id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400

    # Only update fields that were actually provided in the request
    updatable_fields = [
        "product_name", "brands", "ingredients_text",
        "barcode", "price", "quantity",
    ]
    for field in updatable_fields:
        if field in data:
            item[field] = data[field]

    return jsonify(item), 200


@app.route("/inventory/<int:id>", methods=["DELETE"])
def delete_inventory_item(id):
    """Remove an inventory item by id."""
    item = find_item(id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    inventory.remove(item)
    return "", 204


# ---------------------------------------------------------------------------
# External API helper routes
# ---------------------------------------------------------------------------
@app.route("/external/barcode/<barcode>", methods=["GET"])
def lookup_by_barcode(barcode):
    """
    Query OpenFoodFacts for a product by barcode.
    Does NOT add it to inventory - just returns the fetched data so the
    CLI/front end can preview it before deciding to add it.
    """
    result = fetch_product_by_barcode(barcode)
    if result is None:
        return jsonify({"error": "Product not found in external API"}), 404
    return jsonify(result), 200


@app.route("/external/search", methods=["GET"])
def lookup_by_name():
    """
    Query OpenFoodFacts for products matching a name.
    Usage: GET /external/search?query=almond+milk
    """
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "query parameter is required"}), 400

    results = search_products_by_name(query)
    if results is None:
        return jsonify({"error": "External API request failed"}), 502
    return jsonify(results), 200


@app.route("/inventory/from-barcode/<barcode>", methods=["POST"])
def add_inventory_from_barcode(barcode):
    """
    Fetch a product from OpenFoodFacts by barcode and add it directly
    to the inventory array. Optionally accepts JSON body with 'price'
    and 'quantity' to set those fields, since OpenFoodFacts doesn't
    provide retail pricing/stock info.
    """
    product = fetch_product_by_barcode(barcode)
    if product is None:
        return jsonify({"error": "Product not found in external API"}), 404

    data = request.get_json(silent=True) or {}

    new_item = {
        "id": next_id(),
        "product_name": product.get("product_name", "Unknown"),
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "barcode": barcode,
        "price": data.get("price", 0.0),
        "quantity": data.get("quantity", 0),
    }
    inventory.append(new_item)

    return jsonify(new_item), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
