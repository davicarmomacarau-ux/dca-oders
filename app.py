import os
import re
from urllib.parse import quote
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, abort, send_from_directory, redirect, url_for

from database import get_db, fetch_one, fetch_all

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dca-orders-dev")

STATUSES = [
    "new", "accepted", "preparing", "ready",
    "out_for_delivery", "completed", "cancelled"
]

MARKETING_CHANNELS = {
    "whatsapp": "WhatsApp",
    "instagram": "Instagram",
    "google": "Google",
    "email": "E-mail",
}

MARKETING_OBJECTIVES = {
    "visita": "Visitas ao cardápio",
    "pedido": "Pedidos por WhatsApp",
    "fidelidade": "Fidelização",
    "venda": "Venda de combo",
}

STATUS_LABELS = {
    "new": "Novo",
    "accepted": "Aceito",
    "preparing": "Em preparo",
    "ready": "Pronto",
    "out_for_delivery": "Saiu para entrega",
    "completed": "Concluído",
    "cancelled": "Cancelado",
}


def money(value):
    try:
        return f"R$ {Decimal(str(value)):.2f}".replace(".", ",")
    except (InvalidOperation, TypeError, ValueError):
        return "R$ 0,00"


def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return slug.strip("-")


def build_whatsapp_url(phone, text):
    clean_phone = re.sub(r"[^0-9]", "", str(phone or "558800000000"))
    clean_text = (text or "Quero fazer um pedido").strip()
    return f"https://wa.me/{clean_phone}?text={quote(clean_text)}"


def default_categories_for_type(business_type):
    options = {
        "restaurant": ["Hambúrgueres", "Pizzas", "Bebidas"],
        "lanchonete": ["Lanches", "Porções", "Bebidas", "Sobremesas"],
        "padaria": ["Pães", "Doces", "Cafés", "Frios"],
    }
    return options.get(business_type, options["restaurant"])


def build_intelligence_for_restaurant(restaurant_id):
    restaurant = fetch_one("SELECT * FROM restaurants WHERE id=?", (restaurant_id,))
    if not restaurant:
        return {"restaurant": None, "summary": {"score": 0, "confidence": 0, "demand": []}, "top_products": []}

    demand = fetch_all(
        """
        SELECT p.id, p.name, c.name AS category_name,
               COALESCE(SUM(oi.quantity), 0) AS quantity,
               COALESCE(SUM(oi.subtotal), 0) AS revenue
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN order_items oi ON oi.product_id = p.id
        LEFT JOIN orders o ON o.id = oi.order_id AND o.restaurant_id = p.restaurant_id
        WHERE p.restaurant_id=?
        GROUP BY p.id, p.name, c.name
        ORDER BY quantity DESC, revenue DESC
        LIMIT 6
        """,
        (restaurant_id,),
    )

    top_products = []
    for item in demand:
        if item["quantity"]:
            top_products.append({
                "id": item["id"],
                "name": item["name"],
                "category": item["category_name"],
                "quantity": int(item["quantity"]),
                "revenue": float(item["revenue"]),
                "signal": round(min(100, (float(item["quantity"]) * 15) + (float(item["revenue"]) * 0.5)), 2)
            })

    # Bom algoritmo simples de previsão: combina volume de pedidos, categoria e faturamento.
    total_orders = fetch_one("SELECT COUNT(*) AS n FROM orders WHERE restaurant_id=?", (restaurant_id,))["n"]
    total_revenue = fetch_one("SELECT COALESCE(SUM(total), 0) AS total FROM orders WHERE restaurant_id=?", (restaurant_id,))["total"]
    product_volume = sum(item["quantity"] for item in demand if item["quantity"])
    confidence = min(98, 55 + (product_volume * 5) + (total_orders * 4))
    score = min(100, 45 + (float(total_revenue) / 10) + (product_volume * 7))

    return {
        "restaurant": restaurant,
        "summary": {
            "score": round(score, 2),
            "confidence": round(confidence, 2),
            "demand": top_products[:4],
            "total_orders": total_orders,
            "total_revenue": float(total_revenue or 0),
        },
        "top_products": top_products
    }


@app.get("/")
def home():
    restaurant = fetch_one("SELECT * FROM restaurants ORDER BY id LIMIT 1")
    if not restaurant:
        return "Nenhum restaurante cadastrado.", 404
    return render_template("index.html", restaurant=restaurant, money=money)


@app.get("/menu/<slug>")
def menu(slug):
    restaurant = fetch_one("SELECT * FROM restaurants WHERE slug=?", (slug,))
    if not restaurant:
        abort(404)

    products = fetch_all(
        """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.restaurant_id=? AND p.available=true
        ORDER BY c.sort_order, p.id
        """,
        (restaurant["id"],),
    )
    categories = fetch_all(
        "SELECT * FROM categories WHERE restaurant_id=? ORDER BY sort_order, id",
        (restaurant["id"],),
    )
    return render_template(
        "menu.html",
        restaurant=restaurant,
        products=products,
        categories=categories,
        money=money,
        build_whatsapp_url=build_whatsapp_url,
    )


@app.get("/admin")
def admin():
    restaurant_id = request.args.get("restaurant_id", type=int)
    if not restaurant_id:
        restaurant = fetch_one("SELECT * FROM restaurants ORDER BY id LIMIT 1")
        if not restaurant:
            return "Nenhum restaurante cadastrado.", 404
        restaurant_id = restaurant["id"]
    restaurant = fetch_one("SELECT * FROM restaurants WHERE id=?", (restaurant_id,))
    if not restaurant:
        return "Restaurante não encontrado.", 404

    orders = fetch_all(
        """
        SELECT o.*, r.name AS restaurant_name
        FROM orders o
        JOIN restaurants r ON r.id = o.restaurant_id
        WHERE o.restaurant_id=?
        ORDER BY o.created_at DESC
        """,
        (restaurant["id"],),
    )

    for order in orders:
        order["status_label"] = STATUS_LABELS.get(order["status"], order["status"])

    intelligence = build_intelligence_for_restaurant(restaurant["id"])

    return render_template(
        "admin.html",
        restaurant=restaurant,
        orders=orders,
        statuses=STATUSES,
        status_labels=STATUS_LABELS,
        money=money,
        intelligence=intelligence,
    )


@app.get("/api/restaurants")
def api_restaurants():
    restaurants = fetch_all("SELECT * FROM restaurants ORDER BY id")
    return jsonify(restaurants)


@app.get("/api/menu/<slug>")
def api_menu(slug):
    restaurant = fetch_one("SELECT * FROM restaurants WHERE slug=?", (slug,))
    if not restaurant:
        return jsonify({"error": "Restaurante não encontrado"}), 404

    categories = fetch_all(
        "SELECT * FROM categories WHERE restaurant_id=? ORDER BY sort_order", (restaurant["id"],)
    )
    products = fetch_all(
        """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.restaurant_id=? AND p.available=true
        ORDER BY c.sort_order, p.name
        """,
        (restaurant["id"],),
    )

    return jsonify({"restaurant": restaurant, "categories": categories, "products": products})


@app.post("/api/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    restaurant_id = data.get("restaurant_id")
    customer_name = (data.get("customer_name") or "").strip()
    customer_phone = (data.get("customer_phone") or "").strip()
    order_type = (data.get("order_type") or "delivery").strip()
    address = (data.get("address") or "").strip()
    payment_method = (data.get("payment_method") or "").strip()
    notes = (data.get("notes") or "").strip()
    items = data.get("items") or []

    if not restaurant_id or not customer_name or not items:
        return jsonify({"error": "Dados incompletos para criar o pedido."}), 400

    total = Decimal("0")
    for item in items:
        try:
            price = Decimal(str(item.get("price", 0)))
        except (InvalidOperation, TypeError):
            price = Decimal("0")
        quantity = int(item.get("quantity", 1))
        total += price * quantity

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders (
                restaurant_id, customer_name, customer_phone, order_type,
                address, payment_method, notes, status, total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                restaurant_id,
                customer_name,
                customer_phone,
                order_type,
                address,
                payment_method,
                notes,
                "new",
                float(total),
            ),
        )
        order_id = cur.lastrowid

        for item in items:
            product_name = (item.get("name") or "").strip()
            quantity = int(item.get("quantity", 1))
            unit_price = Decimal(str(item.get("price", 0)))
            subtotal = unit_price * quantity
            cur.execute(
                """
                INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (order_id, item.get("product_id"), product_name, quantity, float(unit_price), float(subtotal)),
            )

        conn.commit()
        return jsonify({"success": True, "order_id": order_id, "total": str(total)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.patch("/api/orders/<int:order_id>/status")
def update_order_status(order_id):
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "new").strip()
    if status not in STATUSES:
        return jsonify({"error": "Status inválido"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        if cur.rowcount == 0:
            return jsonify({"error": "Pedido não encontrado"}), 404
        conn.commit()
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.get("/api/orders")
def list_orders():
    restaurant_id = request.args.get("restaurant_id", type=int)
    if not restaurant_id:
        restaurant = fetch_one("SELECT * FROM restaurants ORDER BY id LIMIT 1")
        restaurant_id = restaurant["id"] if restaurant else None

    orders = fetch_all(
        """
        SELECT o.*, r.name AS restaurant_name
        FROM orders o
        JOIN restaurants r ON r.id = o.restaurant_id
        WHERE o.restaurant_id=?
        ORDER BY o.created_at DESC
        """,
        (restaurant_id,),
    )

    for order in orders:
        order["status_label"] = STATUS_LABELS.get(order["status"], order["status"])

    return jsonify(orders)


@app.get("/api/orders/<int:order_id>")
def order_detail(order_id):
    order = fetch_one("SELECT * FROM orders WHERE id=?", (order_id,))
    if not order:
        return jsonify({"error": "Pedido não encontrado"}), 404

    items = fetch_all("SELECT * FROM order_items WHERE order_id=?", (order_id,))
    order["items"] = items
    order["status_label"] = STATUS_LABELS.get(order["status"], order["status"])
    return jsonify(order)


def estimate_campaign_roi(campaign):
    budget = float(campaign.get("budget") or 0)
    revenue = float(campaign.get("expected_revenue") or 0)
    channel_factor = {
        "whatsapp": 1.70,
        "instagram": 1.95,
        "google": 1.50,
        "email": 1.15,
    }.get(campaign.get("channel"), 1.0)

    if budget <= 0:
        return 0
    return round(((revenue * channel_factor) / budget) * 100, 1)


def campaign_rank(campaigns):
    ranked = []
    for campaign in campaigns:
        campaign["roi_estimate"] = estimate_campaign_roi(campaign)
        campaign["rank_score"] = campaign["roi_estimate"] + (campaign.get("expected_revenue") or 0) / 100
        ranked.append(campaign)
    return sorted(ranked, key=lambda item: item["rank_score"], reverse=True)


def forecast_slot(restaurant_id, channel, audience, objective):
    base = {
        "restaurant": 6,
        "lanchonete": 8,
        "padaria": 7,
    }.get(fetch_one("SELECT business_type FROM restaurants WHERE id=?", (restaurant_id,)) or {"business_type": "restaurant"}, "restaurant")

    channel_boost = {
        "whatsapp": 1.8,
        "instagram": 1.6,
        "google": 1.4,
        "email": 1.0,
    }.get(channel, 1.0)

    objective_boost = {
        "pedido": 1.8,
        "venda": 1.7,
        "visita": 1.4,
        "fidelidade": 1.5,
    }.get(objective, 1.0)

    audience_boost = 1.2 if audience and len(audience) >= 3 else 1.0
    return round(base * channel_boost * objective_boost * audience_boost, 2)


@app.get("/marketplace")
def marketplace_page():
    restaurants = fetch_all("SELECT * FROM restaurants ORDER BY id")
    campaigns = fetch_all(
        """
        SELECT c.*, r.name AS restaurant_name, r.business_type
        FROM campaigns c
        JOIN restaurants r ON r.id = c.restaurant_id
        ORDER BY c.created_at DESC
        """
    )

    offers = fetch_all(
        """
        SELECT o.*, r.name AS restaurant_name, r.business_type
        FROM offers o
        JOIN restaurants r ON r.id = o.restaurant_id
        ORDER BY o.created_at DESC
        """
    )

    campaigns = campaign_rank(campaigns)
    offers = sorted(offers, key=lambda x: (float(x.get("discount") or 0), float(x.get("forecast_score") or 0)), reverse=True)

    # previsão por horário e público
    forecast_by_hour = {
        "11h-13h": 86,
        "13h-15h": 72,
        "18h-21h": 95,
        "21h-23h": 70,
    }
    forecast_by_audience = {
        "delivery": 80,
        "bairro": 76,
        "familia": 89,
        "trabalho": 74,
    }

    return render_template(
        "marketplace.html",
        restaurants=restaurants,
        campaigns=campaigns,
        offers=offers,
        channels=MARKETING_CHANNELS,
        objectives=MARKETING_OBJECTIVES,
        forecast_by_hour=forecast_by_hour,
        forecast_by_audience=forecast_by_audience,
        money=money,
        build_whatsapp_url=build_whatsapp_url,
    )


@app.post("/marketplace/campaign")
def create_marketing_campaign():
    restaurant_id = request.form.get("restaurant_id", type=int)
    title = (request.form.get("title") or "").strip()
    channel = (request.form.get("channel") or "whatsapp").strip()
    objective = (request.form.get("objective") or "pedido").strip()
    audience = (request.form.get("audience") or "").strip()
    message = (request.form.get("message") or "").strip()
    budget = Decimal(str(request.form.get("budget") or "0"))

    if not title or len(title) < 3:
        return jsonify({"error": "O título da campanha é obrigatório."}), 400
    if channel not in MARKETING_CHANNELS:
        return jsonify({"error": "Canal de campanha inválido."}), 400
    if objective not in MARKETING_OBJECTIVES:
        return jsonify({"error": "Objetivo da campanha inválido."}), 400
    if not restaurant_id:
        restaurant = fetch_one("SELECT * FROM restaurants ORDER BY id LIMIT 1")
        if not restaurant:
            return jsonify({"error": "Cadastre uma loja antes de criar campanha."}), 404
        restaurant_id = restaurant["id"]

    expected_revenue = budget * Decimal("5.8")

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO campaigns (
                restaurant_id, title, channel, objective, audience,
                message, budget, expected_revenue, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
            """,
            (restaurant_id, title, channel, objective, audience, message, float(budget), float(expected_revenue)),
        )
        conn.commit()
        return redirect(url_for("marketplace_page"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.get("/api/intelligence")
def intelligence_api():
    restaurant_id = request.args.get("restaurant_id", type=int)
    if not restaurant_id:
        restaurant = fetch_one("SELECT * FROM restaurants ORDER BY id LIMIT 1")
        if not restaurant:
            return jsonify({"error": "Restaurante não encontrado"}), 404
        restaurant_id = restaurant["id"]

    return jsonify(build_intelligence_for_restaurant(restaurant_id))


@app.get("/register")
@app.get("/cadastro")
def register_page():
    return render_template("register.html", business_types={
        "restaurant": "Restaurante",
        "lanchonete": "Lanchonete",
        "padaria": "Padaria",
    }, money=money)


@app.post("/register")
@app.post("/cadastro")
def register_business():
    name = (request.form.get("name") or "").strip()
    slug = slugify(request.form.get("slug") or name)
    whatsapp = (request.form.get("whatsapp") or "").strip()
    business_type = (request.form.get("business_type") or "restaurant").strip()

    if not name or len(name) < 2:
        return jsonify({"error": "Nome da loja é obrigatório."}), 400

    if business_type not in {"restaurant", "lanchonete", "padaria"}:
        return jsonify({"error": "Tipo de loja inválido."}), 400

    if not slug:
        return jsonify({"error": "Slug inválido."}), 400

    exists = fetch_one("SELECT id FROM restaurants WHERE slug=?", (slug,))
    if exists:
        return jsonify({"error": "Slug já existe. Escolha outro nome ou slug."}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO restaurants (name, slug, whatsapp, business_type)
            VALUES (?, ?, ?, ?)
            """,
            (name, slug, whatsapp, business_type),
        )
        restaurant_id = cur.lastrowid

        for category in default_categories_for_type(business_type):
            cur.execute(
                "INSERT INTO categories (restaurant_id, name, sort_order) VALUES (?, ?, ?)",
                (restaurant_id, category, 0),
            )

        conn.commit()
        return redirect(url_for("admin", restaurant_id=restaurant_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.post("/marketplace/offer")
def create_offer():
    restaurant_id = request.form.get("restaurant_id", type=int)
    title = (request.form.get("title") or "").strip()
    message = (request.form.get("message") or "").strip()
    discount = Decimal(str(request.form.get("discount") or "0"))
    audience = (request.form.get("audience") or "").strip()
    channel = (request.form.get("channel") or "whatsapp").strip()

    if not title or len(title) < 3:
        return jsonify({"error": "Título da oferta é obrigatório."}), 400
    if not restaurant_id:
        restaurant = fetch_one("SELECT * FROM restaurants ORDER BY id LIMIT 1")
        if not restaurant:
            return jsonify({"error": "Cadastre uma loja antes de criar a oferta."}), 404
        restaurant_id = restaurant["id"]

    restaurant = fetch_one("SELECT * FROM restaurants WHERE id=?", (restaurant_id,))
    if not restaurant:
        return jsonify({"error": "Loja não encontrada."}), 404

    offer_message = f"{title}: {message}"
    whatsapp_url = build_whatsapp_url(restaurant.get("whatsapp") or "558800000000", offer_message)

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO offers (restaurant_id, title, message, audience, discount, channel, whatsapp_url, forecast_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (restaurant_id, title, message, audience, float(discount), channel, whatsapp_url, forecast_slot(restaurant_id, channel, audience, 'pedido')),
        )
        conn.commit()
        return redirect(url_for("marketplace_page"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.get("/sw.js")
def service_worker():
    return send_from_directory(os.path.join(app.root_path, "static"), "sw.js", mimetype="application/javascript")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "app": "dca-orders"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
