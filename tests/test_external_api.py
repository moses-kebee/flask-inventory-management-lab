#!/usr/bin/env python3
"""
Tests for external_api.py - the OpenFoodFacts integration layer.
Uses unittest.mock to simulate API responses without making real
network requests during test runs.
"""

import sys
import os
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from external_api import fetch_product_by_barcode, search_products_by_name  # noqa: E402


class TestFetchProductByBarcode:
    @patch("external_api.requests.get")
    def test_fetch_product_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "status": 1,
            "product": {
                "product_name": "Organic Almond Milk",
                "brands": "Silk",
                "ingredients_text": "Filtered water, almonds, cane sugar",
            },
        }
        mock_get.return_value = mock_response

        result = fetch_product_by_barcode("0025293001165")

        assert result is not None
        assert result["product_name"] == "Organic Almond Milk"
        assert result["brands"] == "Silk"
        assert result["barcode"] == "0025293001165"

    @patch("external_api.requests.get")
    def test_fetch_product_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"status": 0}
        mock_get.return_value = mock_response

        result = fetch_product_by_barcode("0000000000")

        assert result is None

    @patch("external_api.requests.get")
    def test_fetch_product_request_fails(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        result = fetch_product_by_barcode("1234567890")

        assert result is None


class TestSearchProductsByName:
    @patch("external_api.requests.get")
    def test_search_returns_results(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "products": [
                {
                    "product_name": "Almond Milk",
                    "brands": "Silk",
                    "ingredients_text": "almonds, water",
                    "code": "111",
                },
                {
                    "product_name": "Oat Milk",
                    "brands": "Oatly",
                    "ingredients_text": "oats, water",
                    "code": "222",
                },
            ]
        }
        mock_get.return_value = mock_response

        results = search_products_by_name("milk")

        assert results is not None
        assert len(results) == 2
        assert results[0]["product_name"] == "Almond Milk"

    @patch("external_api.requests.get")
    def test_search_no_results(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"products": []}
        mock_get.return_value = mock_response

        results = search_products_by_name("nonexistentproductxyz")

        assert results == []

    @patch("external_api.requests.get")
    def test_search_request_fails(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Timeout")

        results = search_products_by_name("milk")

        assert results is None
