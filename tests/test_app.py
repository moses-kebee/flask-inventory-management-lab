#!/usr/bin/env python3
"""
Tests for the Flask REST API endpoints (GET, POST, PATCH, DELETE)
and the external-API-backed helper routes, using unittest.mock to
avoid making real network calls during testing.
"""

import sys
import os
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module  # noqa: E402


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True

    # Reset inventory to a known state before each test
    app_module.inventory.clear()
    app_module.inventory.extend([
        {
            "id": 1,
            "product_name": "Test Product A",
            "brands": "Acme",
            "ingredients_text": "water, sugar",
            "barcode": "1111111111",
            "price": 1.99,
            "quantity": 10,
        },
        {
            "id": 2,
            "product_name": "Test Product B",
            "brands": "Globex",
            "ingredients_text": "flour, salt",
            "barcode": "2222222222",
            "price": 4.50,
            "quantity": 5,
        },
    ])

    return app_module.app.test_client()


class TestIndexRoute:
    def test_index_returns_welcome_message(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data


class TestGetInventory:
    def test_get_all_inventory(self, client):
        response = client.get("/inventory")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_single_item(self, client):
        response = client.get("/inventory/1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["product_name"] == "Test Product A"

    def test_get_single_item_not_found(self, client):
        response = client.get("/inventory/999")
        assert response.status_code == 404


class TestCreateInventory:
    def test_create_item_success(self, client):
        payload = {"product_name": "New Item", "price": 9.99, "quantity": 3}
        response = client.post("/inventory", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["product_name"] == "New Item"
        assert "id" in data

    def test_create_item_missing_name(self, client):
        response = client.post("/inventory", json={"price": 5.00})
        assert response.status_code == 400

    def test_create_item_appears_in_list(self, client):
        client.post("/inventory", json={"product_name": "Another Item"})
        response = client.get("/inventory")
        data = response.get_json()
        assert len(data) == 3


class TestUpdateInventory:
    def test_update_item_success(self, client):
        response = client.patch("/inventory/1", json={"price": 2.99})
        assert response.status_code == 200
        data = response.get_json()
        assert data["price"] == 2.99
        # Unchanged fields should remain the same
        assert data["product_name"] == "Test Product A"

    def test_update_item_not_found(self, client):
        response = client.patch("/inventory/999", json={"price": 1.00})
        assert response.status_code == 404

    def test_update_item_no_data(self, client):
        response = client.patch("/inventory/1", json={})
        assert response.status_code == 400


class TestDeleteInventory:
    def test_delete_item_success(self, client):
        response = client.delete("/inventory/1")
        assert response.status_code == 204

        # Confirm it's actually gone
        get_response = client.get("/inventory/1")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client):
        response = client.delete("/inventory/999")
        assert response.status_code == 404


class TestExternalApiRoutes:
    @patch("app.fetch_product_by_barcode")
    def test_lookup_by_barcode_found(self, mock_fetch, client):
        mock_fetch.return_value = {
            "product_name": "Mock Product",
            "brands": "MockBrand",
            "ingredients_text": "mock ingredients",
            "barcode": "0000000000",
        }

        response = client.get("/external/barcode/0000000000")
        assert response.status_code == 200
        data = response.get_json()
        assert data["product_name"] == "Mock Product"

    @patch("app.fetch_product_by_barcode")
    def test_lookup_by_barcode_not_found(self, mock_fetch, client):
        mock_fetch.return_value = None

        response = client.get("/external/barcode/9999999999")
        assert response.status_code == 404

    @patch("app.search_products_by_name")
    def test_search_by_name_success(self, mock_search, client):
        mock_search.return_value = [
            {"product_name": "Result 1", "brands": "", "ingredients_text": "", "barcode": ""}
        ]

        response = client.get("/external/search?query=milk")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

    def test_search_by_name_missing_query(self, client):
        response = client.get("/external/search")
        assert response.status_code == 400

    @patch("app.fetch_product_by_barcode")
    def test_add_from_barcode_success(self, mock_fetch, client):
        mock_fetch.return_value = {
            "product_name": "Barcode Product",
            "brands": "BrandX",
            "ingredients_text": "stuff",
            "barcode": "1234567890",
        }

        response = client.post(
            "/inventory/from-barcode/1234567890",
            json={"price": 5.99, "quantity": 20},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["product_name"] == "Barcode Product"
        assert data["price"] == 5.99

        # Confirm it was actually added to inventory
        get_response = client.get("/inventory")
        assert len(get_response.get_json()) == 3

    @patch("app.fetch_product_by_barcode")
    def test_add_from_barcode_not_found(self, mock_fetch, client):
        mock_fetch.return_value = None

        response = client.post("/inventory/from-barcode/0000000000")
        assert response.status_code == 404
