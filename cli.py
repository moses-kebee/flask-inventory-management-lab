#!/usr/bin/env python3
"""
CLI Frontend - Inventory Management System

A simple command-line interface that talks to the Flask API over HTTP.
Run the Flask server first (python app.py), then run this in a second
terminal: python cli.py
"""

import requests

API_URL = "http://localhost:5000"


def list_inventory():
    try:
        response = requests.get(f"{API_URL}/inventory")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error contacting API: {e}")
        return

    items = response.json()
    if not items:
        print("Inventory is empty.")
        return

    print("\n--- Inventory ---")
    for item in items:
        print(
            f"[{item['id']}] {item['product_name']} "
            f"({item.get('brands', 'N/A')}) - "
            f"${item.get('price', 0):.2f} x {item.get('quantity', 0)}"
        )
    print()


def view_item():
    item_id = input("Enter item ID: ").strip()
    if not item_id.isdigit():
        print("Invalid ID. Must be a number.")
        return

    try:
        response = requests.get(f"{API_URL}/inventory/{item_id}")
    except requests.RequestException as e:
        print(f"Error contacting API: {e}")
        return

    if response.status_code == 404:
        print("Item not found.")
        return

    item = response.json()
    print("\n--- Item Details ---")
    for key, value in item.items():
        print(f"{key}: {value}")
    print()


def add_item():
    product_name = input("Product name: ").strip()
    if not product_name:
        print("Product name is required.")
        return

    brands = input("Brand (optional): ").strip()
    try:
        price = float(input("Price (e.g. 3.99): ") or 0)
        quantity = int(input("Quantity in stock: ") or 0)
    except ValueError:
        print("Price and quantity must be numbers.")
        return

    payload = {
        "product_name": product_name,
        "brands": brands,
        "price": price,
        "quantity": quantity,
    }

    try:
        response = requests.post(f"{API_URL}/inventory", json=payload)
    except requests.RequestException as e:
        print(f"Error contacting API: {e}")
        return

    if response.status_code == 201:
        print(f"Added item with ID {response.json()['id']}")
    else:
        print(f"Failed to add item: {response.json()}")


def update_item():
    item_id = input("Enter item ID to update: ").strip()
    if not item_id.isdigit():
        print("Invalid ID. Must be a number.")
        return

    print("Leave a field blank to keep it unchanged.")
    price_input = input("New price: ").strip()
    quantity_input = input("New quantity: ").strip()

    payload = {}
    if price_input:
        try:
            payload["price"] = float(price_input)
        except ValueError:
            print("Invalid price, skipping that field.")
    if quantity_input:
        try:
            payload["quantity"] = int(quantity_input)
        except ValueError:
            print("Invalid quantity, skipping that field.")

    if not payload:
        print("No changes provided.")
        return

    try:
        response = requests.patch(f"{API_URL}/inventory/{item_id}", json=payload)
    except requests.RequestException as e:
        print(f"Error contacting API: {e}")
        return

    if response.status_code == 200:
        print("Item updated successfully.")
    elif response.status_code == 404:
        print("Item not found.")
    else:
        print(f"Failed to update item: {response.json()}")


def delete_item():
    item_id = input("Enter item ID to delete: ").strip()
    if not item_id.isdigit():
        print("Invalid ID. Must be a number.")
        return

    try:
        response = requests.delete(f"{API_URL}/inventory/{item_id}")
    except requests.RequestException as e:
        print(f"Error contacting API: {e}")
        return

    if response.status_code == 204:
        print("Item deleted successfully.")
    elif response.status_code == 404:
        print("Item not found.")
    else:
        print(f"Failed to delete item: {response.status_code}")


def find_on_external_api():
    barcode = input("Enter barcode to look up: ").strip()
    if not barcode:
        print("Barcode is required.")
        return

    try:
        response = requests.get(f"{API_URL}/external/barcode/{barcode}")
    except requests.RequestException as e:
        print(f"Error contacting API: {e}")
        return

    if response.status_code == 404:
        print("Product not found via external API.")
        return

    product = response.json()
    print("\n--- Product Found ---")
    for key, value in product.items():
        print(f"{key}: {value}")

    add_choice = input("\nAdd this product to inventory? (y/n): ").strip().lower()
    if add_choice == "y":
        try:
            price = float(input("Price: ") or 0)
            quantity = int(input("Quantity: ") or 0)
        except ValueError:
            print("Invalid price/quantity, using defaults of 0.")
            price, quantity = 0.0, 0

        add_response = requests.post(
            f"{API_URL}/inventory/from-barcode/{barcode}",
            json={"price": price, "quantity": quantity},
        )
        if add_response.status_code == 201:
            print(f"Added to inventory with ID {add_response.json()['id']}")
        else:
            print(f"Failed to add: {add_response.json()}")


def print_menu():
    print("""
==== Inventory Management CLI ====
1. View all inventory
2. View single item
3. Add new item
4. Update item (price/quantity)
5. Delete item
6. Find item on external API (by barcode)
7. Exit
""")


def main():
    while True:
        print_menu()
        choice = input("Choose an option (1-7): ").strip()

        if choice == "1":
            list_inventory()
        elif choice == "2":
            view_item()
        elif choice == "3":
            add_item()
        elif choice == "4":
            update_item()
        elif choice == "5":
            delete_item()
        elif choice == "6":
            find_on_external_api()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please select 1-7.")


if __name__ == "__main__":
    main()
