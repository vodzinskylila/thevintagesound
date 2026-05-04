# app.py — The Vintage Sound API (Python + Flask + SQLite)
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from database import init_db, seed_database
from routes.auth          import auth_bp
from routes.products      import products_bp
from routes.cart          import cart_bp
from routes.orders        import orders_bp
from routes.subscriptions import subs_bp

# ── Criar app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET", "vintage_sound_secret_troque_em_producao")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # tokens não expiram (use timedelta em produção)

CORS(app, origins="*", supports_credentials=True)
JWTManager(app)

# ── Registrar rotas ───────────────────────────────────────────────────────────
app.register_blueprint(auth_bp,     url_prefix="/api/auth")
app.register_blueprint(products_bp, url_prefix="/api/products")
app.register_blueprint(cart_bp,     url_prefix="/api/cart")
app.register_blueprint(orders_bp,   url_prefix="/api/orders")
app.register_blueprint(subs_bp,     url_prefix="/api/subscriptions")

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return jsonify(status="ok", service="The Vintage Sound API", version="2.0.0")

@app.get("/")
def index():
    return jsonify(
        name="The Vintage Sound API",
        version="2.0.0",
        endpoints={
            "auth":          "/api/auth",
            "products":      "/api/products",
            "cart":          "/api/cart",
            "orders":        "/api/orders",
            "subscriptions": "/api/subscriptions",
        }
    )

# ── 404 global ────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify(success=False, message="Rota não encontrada."), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify(success=False, message="Erro interno do servidor."), 500

# ── Inicialização ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🎵  The Vintage Sound API  (Python + Flask + SQLite)")
    print("─" * 50)
    init_db()
    seed_database()
    print("\n📡  Endpoints:")
    print("   POST  /api/auth/register")
    print("   POST  /api/auth/login")
    print("   GET   /api/auth/me")
    print("   GET   /api/products")
    print("   GET   /api/cart          (requer login)")
    print("   POST  /api/cart/items    (requer login)")
    print("   POST  /api/orders        (requer login)")
    print("   GET   /api/orders/my     (requer login)")
    print("   GET   /api/subscriptions/plans")
    print("\n🔑  Admin: admin@vintagesound.com / admin123")
    print("💾  Banco de dados: data/vintage_sound.db")
    print(f"\n✅  Servidor em http://localhost:3000\n")
    app.run(host="0.0.0.0", port=3000, debug=True)
