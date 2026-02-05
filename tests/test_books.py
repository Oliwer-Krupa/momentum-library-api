BOOK_PAYLOAD = {
    "serial_number": "000001",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt",
}


def _create_book(client, **overrides):
    payload = {**BOOK_PAYLOAD, **overrides}
    return client.post("/books/", json=payload)


# ---------- POST /books/ ----------


def test_create_book_success(client):
    resp = _create_book(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["serial_number"] == "000001"
    assert data["title"] == "The Pragmatic Programmer"
    assert data["author"] == "David Thomas, Andrew Hunt"
    assert data["status"] == "AVAILABLE"
    assert data["borrowed_at"] is None
    assert data["borrower_card_number"] is None


def test_create_book_duplicate(client):
    _create_book(client)
    resp = _create_book(client)
    assert resp.status_code == 409


def test_create_book_invalid_serial_number(client):
    resp = _create_book(client, serial_number="ABC")
    assert resp.status_code == 422


def test_create_book_missing_fields(client):
    resp = client.post("/books/", json={})
    assert resp.status_code == 422


# ---------- GET /books/ ----------


def test_list_books_empty(client):
    resp = client.get("/books/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_books_returns_all_sorted(client):
    _create_book(client, serial_number="000003", title="C")
    _create_book(client, serial_number="000001", title="A")
    _create_book(client, serial_number="000002", title="B")
    resp = client.get("/books/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert [b["serial_number"] for b in data] == ["000001", "000002", "000003"]


def test_list_books_filter_by_status(client):
    _create_book(client, serial_number="000001")
    _create_book(client, serial_number="000002")
    client.patch("/books/000001/borrow", json={"borrower_card_number": "999999"})

    resp_borrowed = client.get("/books/", params={"status": "BORROWED"})
    assert resp_borrowed.status_code == 200
    assert len(resp_borrowed.json()) == 1
    assert resp_borrowed.json()[0]["serial_number"] == "000001"

    resp_available = client.get("/books/", params={"status": "AVAILABLE"})
    assert resp_available.status_code == 200
    assert len(resp_available.json()) == 1
    assert resp_available.json()[0]["serial_number"] == "000002"


# ---------- DELETE /books/{serial_number} ----------


def test_delete_book_success(client):
    _create_book(client)
    resp = client.delete("/books/000001")
    assert resp.status_code == 204

    resp_list = client.get("/books/")
    assert resp_list.json() == []


def test_delete_book_not_found(client):
    resp = client.delete("/books/999999")
    assert resp.status_code == 404


# ---------- PATCH /books/{serial_number}/borrow ----------


def test_borrow_book_success(client):
    _create_book(client)
    resp = client.patch("/books/000001/borrow", json={"borrower_card_number": "654321"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "BORROWED"
    assert data["borrower_card_number"] == "654321"
    assert data["borrowed_at"] is not None
    # Verify ISO-8601 format with timezone info
    assert "T" in data["borrowed_at"]


def test_borrow_book_already_borrowed(client):
    _create_book(client)
    client.patch("/books/000001/borrow", json={"borrower_card_number": "654321"})
    resp = client.patch("/books/000001/borrow", json={"borrower_card_number": "111111"})
    assert resp.status_code == 409


def test_borrow_book_not_found(client):
    resp = client.patch("/books/999999/borrow", json={"borrower_card_number": "654321"})
    assert resp.status_code == 404


def test_borrow_book_invalid_card_number(client):
    _create_book(client)
    resp = client.patch("/books/000001/borrow", json={"borrower_card_number": "ABC"})
    assert resp.status_code == 422


# ---------- PATCH /books/{serial_number}/return ----------


def test_return_book_success(client):
    _create_book(client)
    client.patch("/books/000001/borrow", json={"borrower_card_number": "654321"})
    resp = client.patch("/books/000001/return")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "AVAILABLE"
    assert data["borrowed_at"] is None
    assert data["borrower_card_number"] is None


def test_return_book_not_borrowed(client):
    _create_book(client)
    resp = client.patch("/books/000001/return")
    assert resp.status_code == 409


def test_return_book_not_found(client):
    resp = client.patch("/books/999999/return")
    assert resp.status_code == 404


# ---------- GET /health ----------


def test_healthcheck(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
