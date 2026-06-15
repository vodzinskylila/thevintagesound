# routes/orders.py
import uuid, json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_conn
from datetime import datetime

orders_bp = Blueprint("orders", __name__)


def row_to_order(row):
    return {
        "id": row["id"], "orderNumber": row["order_number"],
        "userId": row["user_id"],
        "items": json.loads(row["items"]),
        "shippingAddress": json.loads(row["shipping_address"]),
        "paymentMethod": row["payment_method"],
        "subtotal": row["subtotal"], "shipping": row["shipping"], "total": row["total"],
        "status": row["status"],
        "statusHistory": json.loads(row["status_history"]),
        "createdAt": row["created_at"],
    }


@orders_bp.post("/")
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    data    = request.get_json() or {}
    address = data.get("shippingAddress")
    payment = data.get("paymentMethod")

    if not address or not payment:
        return jsonify(success=False, message="Endereço e método de pagamento são obrigatórios."), 422
    if payment not in ("credit_card", "pix"):
        return jsonify(success=False, message="Método inválido. Use: credit_card ou pix."), 422

    with get_conn() as conn:
        cart = conn.execute(
            """SELECT c.id, c.quantity,
                      p.id as pid, p.title, p.artist, p.price, p.image_url, p.stock
               FROM cart_items c JOIN products p ON p.id=c.product_id
               WHERE c.user_id=?""",
            (user_id,),
        ).fetchall()

        if not cart:
            return jsonify(success=False, message="Seu carrinho está vazio."), 400

        order_items = []
        subtotal    = 0.0
        for item in cart:
            if item["stock"] < item["quantity"]:
                return jsonify(success=False,
                    message=f'Estoque insuficiente para "{item["title"]}". Disponível: {item["stock"]}.'), 400
            item_sub = round(item["price"] * item["quantity"], 2)
            subtotal += item_sub
            order_items.append({
                "productId": item["pid"], "title": item["title"],
                "artist": item["artist"], "price": item["price"],
                "imageUrl": item["image_url"],
                "quantity": item["quantity"], "subtotal": item_sub,
            })
            conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (item["quantity"], item["pid"]))

        subtotal   = round(subtotal, 2)
        shipping   = 0.0 if subtotal >= 200 else 29.90
        total      = round(subtotal + shipping, 2)
        now        = datetime.utcnow().isoformat()
        order_id   = str(uuid.uuid4())
        order_num  = f"TVS-{int(datetime.utcnow().timestamp()) % 100000000:08d}"
        history    = json.dumps([{"status": "pending", "timestamp": now, "note": "Pedido recebido."}])

        conn.execute(
            """INSERT INTO orders
               (id,order_number,user_id,items,shipping_address,payment_method,
                subtotal,shipping,total,status,status_history,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (order_id, order_num, user_id, json.dumps(order_items),
             json.dumps(address), payment, subtotal, shipping, total,
             "pending", history, now),
        )
        conn.execute("DELETE FROM cart_items WHERE user_id=?", (user_id,))
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()

    return jsonify(success=True, message=f"Pedido #{order_num} realizado com sucesso!",
                   data=row_to_order(row)), 201


@orders_bp.get("/my")
@jwt_required()
def my_orders():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    return jsonify(success=True, data=[row_to_order(r) for r in rows], total=len(rows))


@orders_bp.get("/my/<order_id>")
@jwt_required()
def get_my_order(order_id):
    user_id = get_jwt_identity()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE (id=? OR order_number=?) AND user_id=?",
            (order_id, order_id, user_id),
        ).fetchone()
    if not row:
        return jsonify(success=False, message="Pedido não encontrado."), 404
    return jsonify(success=True, data=row_to_order(row))


@orders_bp.get("/")
@jwt_required()
def all_orders():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if not user or user["role"] != "admin":
        return jsonify(success=False, message="Acesso restrito a administradores."), 403

    status = request.args.get("status", "")
    page   = max(1, request.args.get("page", 1, type=int))
    limit  = min(100, max(1, request.args.get("limit", 20, type=int)))

    where  = "WHERE status=?" if status else ""
    params = [status] if status else []
    with get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM orders {where}", params).fetchone()[0]
        rows  = conn.execute(
            f"SELECT * FROM orders {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, (page - 1) * limit],
        ).fetchall()
    return jsonify(success=True, data=[row_to_order(r) for r in rows],
                   pagination={"total": total, "page": page, "limit": limit})


@orders_bp.patch("/<order_id>/status")
@jwt_required()
def update_status(order_id):
    user_id = get_jwt_identity()
    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if not user or user["role"] != "admin":
        return jsonify(success=False, message="Acesso restrito a administradores."), 403

    data   = request.get_json() or {}
    status = data.get("status", "")
    note   = data.get("note", "")
    valid  = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if status not in valid:
        return jsonify(success=False, message=f"Status inválido. Use: {', '.join(valid)}."), 400

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            return jsonify(success=False, message="Pedido não encontrado."), 404
        history = json.loads(row["status_history"])
        history.append({"status": status, "timestamp": datetime.utcnow().isoformat(), "note": note})
        conn.execute("UPDATE orders SET status=?, status_history=? WHERE id=?",
                     (status, json.dumps(history), order_id))
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return jsonify(success=True, message="Status atualizado.", data=row_to_order(row))
