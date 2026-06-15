# routes/subscriptions.py
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_conn, SUBSCRIPTION_PLANS
from datetime import datetime
from dateutil.relativedelta import relativedelta

subs_bp = Blueprint("subscriptions", __name__)


def find_plan(plan_id):
    return next((p for p in SUBSCRIPTION_PLANS if p["id"] == plan_id), None)


@subs_bp.get("/plans")
def list_plans():
    return jsonify(success=True, data=SUBSCRIPTION_PLANS)


@subs_bp.post("/")
@jwt_required()
def subscribe():
    user_id = get_jwt_identity()
    data    = request.get_json() or {}
    plan_id = data.get("planId", "")
    payment = data.get("paymentMethod", "")

    plan = find_plan(plan_id)
    if not plan:
        return jsonify(success=False, message="Plano não encontrado."), 404
    if payment not in ("credit_card", "pix"):
        return jsonify(success=False, message="Método de pagamento inválido."), 422

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id, plan_name FROM subscriptions WHERE user_id=? AND status='active'", (user_id,)
        ).fetchone()
        if existing:
            return jsonify(success=False,
                message=f'Você já possui uma assinatura ativa: "{existing["plan_name"]}".'), 409

        now      = datetime.utcnow()
        next_bill = (now + relativedelta(months=1)).isoformat()
        sub_id   = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO subscriptions
               (id,user_id,plan_id,plan_name,price,interval_type,status,
                payment_method,start_date,next_billing,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sub_id, user_id, plan_id, plan["name"], plan["price"],
             plan["interval"], "active", payment,
             now.isoformat(), next_bill, now.isoformat()),
        )
        row = conn.execute("SELECT * FROM subscriptions WHERE id=?", (sub_id,)).fetchone()

    return jsonify(success=True,
        message=f'Assinatura "{plan["name"]}" ativada! Bem-vindo ao clube.',
        data=dict(row)), 201


@subs_bp.get("/my")
@jwt_required()
def my_subscription():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id=? AND status='active'", (user_id,)
        ).fetchone()
    if not row:
        return jsonify(success=True, data=None, message="Nenhuma assinatura ativa.")
    plan = find_plan(row["plan_id"])
    result = dict(row)
    result["planDetails"] = plan
    return jsonify(success=True, data=result)


@subs_bp.delete("/<sub_id>")
@jwt_required()
def cancel(sub_id):
    user_id = get_jwt_identity()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM subscriptions WHERE id=? AND user_id=? AND status='active'",
            (sub_id, user_id),
        ).fetchone()
        if not row:
            return jsonify(success=False, message="Assinatura não encontrada."), 404
        conn.execute(
            "UPDATE subscriptions SET status='cancelled', cancelled_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), sub_id),
        )
        row = conn.execute("SELECT * FROM subscriptions WHERE id=?", (sub_id,)).fetchone()
    return jsonify(success=True,
        message="Assinatura cancelada. Acesso mantido até o fim do período.", data=dict(row))


@subs_bp.get("/")
@jwt_required()
def all_subscriptions():
    user_id = get_jwt_identity()
    with get_conn() as conn:
        user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    if not user or user["role"] != "admin":
        return jsonify(success=False, message="Acesso restrito a administradores."), 403
    status = request.args.get("status", "")
    with get_conn() as conn:
        if status:
            rows = conn.execute("SELECT * FROM subscriptions WHERE status=?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM subscriptions").fetchall()
    revenue = sum(r["price"] for r in rows if r["status"] == "active")
    return jsonify(success=True, data=[dict(r) for r in rows],
                   total=len(rows), revenue=round(revenue, 2))
