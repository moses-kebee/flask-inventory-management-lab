# Inventory Management System

A Flask-based REST API for a retail inventory management system, with
CRUD operations, integration with the [OpenFoodFacts API](https://openfoodfacts.github.io/openfoodfacts-server/api/)
for real product data, and a CLI tool for interacting with the API.

## Features

- Full CRUD (Create, Read, Update, Delete) API for inventory items
- Lookup real product data from OpenFoodFacts by barcode or name
- Add products fetched from OpenFoodFacts directly into inventory
- CLI frontend for managing inventory without needing Postman/curl
- Unit tests covering all API routes and the external API integration,
  using `unittest.mock` to avoid live network calls during tests

## Project Structure

```
inventory-lab/
├── app.py                    # Flask API - routes and in-memory data store
├── external_api.py           # OpenFoodFacts integration layer
├── cli.py                    # Command-line interface
├── requirements.txt
├── tests/
│   ├── test_app.py           # Tests for Flask routes
│   └── test_external_api.py  # Tests for OpenFoodFacts integration
└── README.md
```

## Setup

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd inventory-lab
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask server:
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`.

5. In a second terminal (with the venv activated), run the CLI:
   ```bash
   python cli.py
   ```

## API Endpoints

| Method | Route                              | Description                                      |
|--------|-------------------------------------|---------------------------------------------------|
| GET    | `/`                                 | Welcome message                                   |
| GET    | `/inventory`                        | Get all inventory items                           |
| GET    | `/inventory/<id>`                   | Get a single inventory item                       |
| POST   | `/inventory`                        | Create a new inventory item                       |
| PATCH  | `/inventory/<id>`                   | Update one or more fields of an item               |
| DELETE | `/inventory/<id>`                   | Delete an inventory item                           |
| GET    | `/external/barcode/<barcode>`       | Look up a product on OpenFoodFacts by barcode      |
| GET    | `/external/search?query=<name>`     | Search OpenFoodFacts for products matching a name  |
| POST   | `/inventory/from-barcode/<barcode>` | Fetch a product by barcode and add it to inventory |

### Example: Create an item
```bash
curl -X POST http://localhost:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Organic Almond Milk", "brands": "Silk", "price": 3.99, "quantity": 25}'
```

Response (`201 Created`):
```json
{
  "id": 3,
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "ingredients_text": "",
  "barcode": "",
  "price": 3.99,
  "quantity": 25
}
```

### Example: Update an item's price/quantity
```bash
curl -X PATCH http://localhost:5000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 4.49, "quantity": 15}'
```

### Example: Fetch a product from OpenFoodFacts and add it to inventory
```bash
curl -X POST http://localhost:5000/inventory/from-barcode/0025293001165 \
  -H "Content-Type: application/json" \
  -d '{"price": 3.99, "quantity": 20}'
```

## CLI Usage

Once `cli.py` is running, you'll see a menu:

```
==== Inventory Management CLI ====
1. View all inventory
2. View single item
3. Add new item
4. Update item (price/quantity)
5. Delete item
6. Find item on external API (by barcode)
7. Exit
```

Select an option by number and follow the prompts. Option 6 will query
OpenFoodFacts by barcode, display the result, and ask whether you'd
like to add it directly to your inventory (with a price and quantity
you specify, since OpenFoodFacts doesn't track retail pricing/stock).

## Running Tests

```bash
python -m pytest -v
```

All API routes and the external API integration are covered, with
`unittest.mock` used to simulate OpenFoodFacts responses so the test
suite runs without needing network access.

## Notes on Design Decisions

- **In-memory storage**: Inventory data is stored in a Python list for
  simplicity, as specified by the lab. Restarting the Flask server
  resets the data back to two seed items.
- **Separation of concerns**: External API logic lives in
  `external_api.py`, kept separate from Flask routing in `app.py`, so
  it can be tested and reused independently (e.g., by the CLI or
  future features) without depending on Flask.
- **PATCH over PUT**: Updates use PATCH with partial payloads (only
  changed fields need to be sent) rather than requiring a full item
  replacement.
