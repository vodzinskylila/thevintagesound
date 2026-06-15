# routes/products.py
import uuid, json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_conn
from datetime import datetime

products_bp = Blueprint("products", __name__)


def row_to_product(row):
    return {
        "id": row["id"], "slug": row["slug"], "title": row["title"],
        "artist": row["artist"], "genre": row["genre"], "year": row["year"],
        "label": row["label"], "pressing": row["pressing"],
        "description": row["description"], "price": row["price"],
        "stock": row["stock"], "imageUrl": row["image_url"],
        "tags": json.loads(row["tags"] or "[]"),
        "featured": bool(row["featured"]),
        "createdAt": row["created_at"],
    }


@products_bp.get("/")
def list_products():
    genre    = request.args.get("genre", "")
    search   = request.args.get("search", "")
    featured = request.args.get("featured", "")
    min_p    = request.args.get("minPrice", type=float)
    max_p    = request.args.get("maxPrice", type=float)
    sort     = request.args.get("sort", "created_at")
    order    = request.args.get("order", "desc")
    page     = max(1, request.args.get("page", 1, type=int))
    limit    = min(50, max(1, request.args.get("limit", 20, type=int)))

    # Mapeamento de campos sort
    sort_map = {"price": "price", "title": "title", "year": "year", "createdAt": "created_at"}
    sort_col = sort_map.get(sort, "created_at")
    order_kw = "ASC" if order == "asc" else "DESC"

    where, params = ["1=1"], []
    if genre:    where.append("genre=?");                params.append(genre)
    if featured == "true": where.append("featured=1")
    if search:   where.append("(title LIKE ? OR artist LIKE ? OR genre LIKE ?)"); params += [f"%{search}%"]*3
    if min_p:    where.append("price>=?");               params.append(min_p)
    if max_p:    where.append("price<=?");               params.append(max_p)

    where_sql = " AND ".join(where)
    with get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM products WHERE {where_sql}", params).fetchone()[0]
        rows  = conn.execute(
            f"SELECT * FROM products WHERE {where_sql} ORDER BY {sort_col} {order_kw} LIMIT ? OFFSET ?",
            params + [limit, (page - 1) * limit],
        ).fetchall()

    total_pages = max(1, -(-total // limit))  # ceil division
    return jsonify(
        success=True,
        data=[row_to_product(r) for r in rows],
        pagination={"total": total, "page": page, "limit": limit,
                    "totalPages": total_pages,
                    "hasNext": page < total_pages, "hasPrev": page > 1},
    )


@products_bp.get("/genres")
def list_genres():
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT genre FROM products ORDER BY genre").fetchall()
    return jsonify(success=True, data=[r["genre"] for r in rows])


@products_bp.get("/<slug_or_id>")
def get_product(slug_or_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE slug=? OR id=?", (slug_or_id, slug_or_id)).fetchone()
    if not row:
        return jsonify(success=False, message="Produto não encontrado."), 404
    p = row_to_product(row)
    with get_conn() as conn:
        related = conn.execute(
            "SELECT * FROM products WHERE genre=? AND id!=? LIMIT 4", (row["genre"], row["id"])
        ).fetchall()
    return jsonify(success=True, data=p, related=[row_to_product(r) for r in related])


@products_bp.post("/")
@jwt_required()
def create_product():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if not user or user["role"] != "admin":
        return jsonify(success=False, message="Acesso restrito a administradores."), 403

    data = request.get_json() or {}
    required = ["title", "artist", "genre", "price"]
    if not all(data.get(f) for f in required):
        return jsonify(success=False, message="Campos obrigatórios: title, artist, genre, price."), 422

    slug = f"{data['artist']}-{data['title']}".lower()
    slug = "".join(c if c.isalnum() else "-" for c in slug).strip("-")
    now  = datetime.utcnow().isoformat()

    with get_conn() as conn:
        if conn.execute("SELECT id FROM products WHERE slug=?", (slug,)).fetchone():
            return jsonify(success=False, message="Produto com este slug já existe."), 409
        pid = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO products (id,slug,title,artist,genre,year,label,pressing,description,
               price,stock,image_url,tags,featured,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pid, slug, data["title"], data["artist"], data["genre"],
             data.get("year"), data.get("label"), data.get("pressing"),
             data.get("description"), float(data["price"]),
             int(data.get("stock", 0)), data.get("imageUrl", ""),
             json.dumps(data.get("tags", [])), int(data.get("featured", False)), now),
        )
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    return jsonify(success=True, message="Produto criado.", data=row_to_product(row)), 201


@products_bp.delete("/<product_id>")
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if not user or user["role"] != "admin":
        return jsonify(success=False, message="Acesso restrito a administradores."), 403
    with get_conn() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    return jsonify(success=True, message="Produto removido.")
