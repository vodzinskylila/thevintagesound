# routes/cart.py
import uuid, json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_conn
from datetime import datetime

cart_bp = Blueprint("cart", __name__)


def get_cart_data(user_id):
    with get_conn() as conn:
        items = conn.execute(
            """SELECT c.id, c.quantity, c.added_at,
                      p.id as product_id, p.title, p.artist, p.price,
                      p.image_url, p.pressing, p.genre, p.stock
               FROM cart_items c
               JOIN products p ON p.id = c.product_id
               WHERE c.user_id=?""",
            (user_id,),
        ).fetchall()

    result = []
    subtotal = 0.0
    for i in items:
        item_sub = round(i["price"] * i["quantity"], 2)
        subtotal += item_sub
        result.append({
            "id": i["id"], "quantity": i["quantity"], "addedAt": i["added_at"],
            "product": {
                "id": i["product_id"], "title": i["title"], "artist": i["artist"],
                "price": i["price"], "imageUrl": i["image_url"],
                "pressing": i["pressing"], "genre": i["genre"], "stock": i["stock"],
            },
            "subtotal": item_sub,
        })

    subtotal  = round(subtotal, 2)
    shipping  = 0.0 if subtotal >= 200 else 29.90
    total     = round(subtotal + shipping, 2)
    item_count = sum(i["quantity"] for i in items)

    return {"items": result, "subtotal": subtotal, "shipping": shipping,
            "total": total, "itemCount": item_count}


@cart_bp.get("/")
@cart_bp.get("")
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    return jsonify(success=True, data=get_cart_data(user_id))


@cart_bp.post("/items")
@jwt_required()
def add_item():
    user_id    = get_jwt_identity()
    data       = request.get_json() or {}
    product_id = data.get("productId", "").strip()
    quantity   = max(1, int(data.get("quantity", 1)))

    if not product_id:
        return jsonify(success=False, message="productId é obrigatório."), 422

    with get_conn() as conn:
        product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not product:
            return jsonify(success=False, message="Produto não encontrado."), 404
        if product["stock"] < quantity:
            return jsonify(success=False, message=f"Estoque insuficiente. Disponível: {product['stock']}."), 400

        existing = conn.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id=? AND product_id=?",
            (user_id, product_id),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE cart_items SET quantity=? WHERE id=?",
                (existing["quantity"] + quantity, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO cart_items (id,user_id,product_id,quantity,added_at) VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), user_id, product_id, quantity, datetime.utcnow().isoformat()),
            )

    cart = get_cart_data(user_id)
    return jsonify(success=True, message=f'"{product["title"]}" adicionado ao carrinho.', data=cart)


@cart_bp.patch("/items/<item_id>")
@jwt_required()
def update_item(item_id):
    user_id  = get_jwt_identity()
    quantity = int((request.get_json() or {}).get("quantity", 1))

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM cart_items WHERE id=? AND user_id=?", (item_id, user_id)
        ).fetchone()
        if not row:
            return jsonify(success=False, message="Item não encontrado."), 404

        if quantity <= 0:
            conn.execute("DELETE FROM cart_items WHERE id=?", (item_id,))
        else:
            conn.execute("UPDATE cart_items SET quantity=? WHERE id=?", (quantity, item_id))

    return jsonify(success=True, message="Carrinho atualizado.", data=get_cart_data(user_id))


@cart_bp.delete("/items/<item_id>")
@jwt_required()
def remove_item(item_id):
    user_id = get_jwt_identity()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM cart_items WHERE id=? AND user_id=?", (item_id, user_id)
        ).fetchone()
        if not row:
            return jsonify(success=False, message="Item não encontrado."), 404
        conn.execute("DELETE FROM cart_items WHERE id=?", (item_id,))
    return jsonify(success=True, message="Item removido.", data=get_cart_data(user_id))


@cart_bp.delete("/")
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        conn.execute("DELETE FROM cart_items WHERE user_id=?", (user_id,))
    return jsonify(success=True, message="Carrinho limpo.")
