# routes/auth.py
import uuid, bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import get_conn
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    first_name = (data.get("firstName") or "").strip()
    last_name  = (data.get("lastName")  or "").strip()
    email      = (data.get("email")     or "").strip().lower()
    password   = (data.get("password")  or "")
    newsletter = bool(data.get("newsletter", False))

    if not all([first_name, last_name, email, password]):
        return jsonify(success=False, message="Preencha todos os campos."), 422
    if len(password) < 8:
        return jsonify(success=False, message="Senha deve ter pelo menos 8 caracteres."), 422

    with get_conn() as conn:
        if conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            return jsonify(success=False, message="Este e-mail já está cadastrado."), 409

        user_id = str(uuid.uuid4())
        hashed  = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        now     = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO users (id,first_name,last_name,email,password,role,newsletter,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, first_name, last_name, email, hashed, "customer", int(newsletter), now),
        )

    token = create_access_token(identity=user_id)
    user  = {"id": user_id, "firstName": first_name, "lastName": last_name,
             "email": email, "role": "customer", "newsletter": newsletter}
    return jsonify(success=True, message="Conta criada com sucesso!", token=token, user=user), 201


@auth_bp.post("/login")
def login():
    data     = request.get_json() or {}
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return jsonify(success=False, message="Preencha e-mail e senha."), 422

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    if not row or not bcrypt.checkpw(password.encode(), row["password"].encode()):
        return jsonify(success=False, message="E-mail ou senha incorretos."), 401

    token = create_access_token(identity=row["id"])
    user  = {"id": row["id"], "firstName": row["first_name"], "lastName": row["last_name"],
             "email": row["email"], "role": row["role"], "newsletter": bool(row["newsletter"])}
    return jsonify(success=True, message="Login realizado com sucesso.", token=token, user=user)


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        return jsonify(success=False, message="Usuário não encontrado."), 404
    user = {"id": row["id"], "firstName": row["first_name"], "lastName": row["last_name"],
            "email": row["email"], "role": row["role"], "newsletter": bool(row["newsletter"])}
    return jsonify(success=True, user=user)


@auth_bp.patch("/me")
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data    = request.get_json() or {}
    fields, values = [], []
    if "firstName"  in data: fields.append("first_name=?");  values.append(data["firstName"].strip())
    if "lastName"   in data: fields.append("last_name=?");   values.append(data["lastName"].strip())
    if "newsletter" in data: fields.append("newsletter=?");  values.append(int(data["newsletter"]))
    if not fields:
        return jsonify(success=False, message="Nenhum campo para atualizar."), 400
    values.append(user_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", values)
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    user = {"id": row["id"], "firstName": row["first_name"], "lastName": row["last_name"],
            "email": row["email"], "role": row["role"], "newsletter": bool(row["newsletter"])}
    return jsonify(success=True, message="Perfil atualizado.", user=user)
