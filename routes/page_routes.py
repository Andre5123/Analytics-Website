from flask import Blueprint, render_template, session, jsonify
from utils.decorators import login_required
from services.event_service import getEventStatus, getPastEvents
from services.items_service import getItems
from db.supabase_client import supabase

page_bp = Blueprint("page", __name__)

@page_bp.route("/")
@login_required
def home():
    status = bool(getEventStatus())
    return render_template("home.html", eventActive=status)

@page_bp.route("/history")
@login_required
def history():
    events = getPastEvents()
    return render_template("history.html", events=events)

@page_bp.route("/analytics")
@login_required
def analytics():
    events = getPastEvents()
    items = getItems(True)
    return render_template("analytics.html", events=events, items=items)

@page_bp.route("/inventory")
@login_required
def inventory():
    items = getItems(True)
    for item in items:
        item["unit_cost"] = item["cost"] / item["quantity"]
    return render_template("inventory.html", items=items)

@page_bp.route("/event")
@login_required
def event_page():
    eventStatus = getEventStatus()
    if not eventStatus:
        return jsonify({"error": "No event currently being held"}), 400

    items = getItems(True)

    current_event_id = (
        supabase.table("event_lock")
        .select("current_event_id")
        .eq("id", 1)
        .execute()
        .data[0]["current_event_id"]
    )

    # --- Fetch sales ---
    sales = (
        supabase.table("sales")
        .select("*")
        .eq("event_id", current_event_id)
        .eq("user_id", session["user_id"])
        .order("sale_time", desc=True)
        .execute()
        .data
    )

    if not sales:
        return render_template(
            "event.html",
            items=items,
            cashSales=[],
            tapSales=[]
        )

    sale_ids = [s["id"] for s in sales]

    # --- Fetch sale items ---
    sale_items = (
        supabase.table("sale_items")
        .select("*")
        .in_("sale_id", sale_ids)
        .execute()
        .data
    )

    # --- Group items by sale_id ---
    items_by_sale = {}
    for si in sale_items:
        items_by_sale.setdefault(si["sale_id"], []).append({
            "item": si["item"],
            "quantity": si["quantity"],
            "revenue": si["revenue"],
            "cost": si["cost"]
        })

    # --- Attach items to sales ---
    formatted_sales = []
    for s in sales:
        formatted_sales.append({
            "id": s["id"],
            "payment_method": s["payment_method"],
            "sale_time": s["sale_time"],
            "total_revenue": s["total_revenue"],
            "total_cost": s["total_cost"],
            "items": items_by_sale.get(s["id"], [])
        })

    # --- Split by payment method ---
    cashSales = [s for s in formatted_sales if s["payment_method"] == "cash"]
    tapSales = [s for s in formatted_sales if s["payment_method"] == "tap"]

    return render_template(
        "event.html",
        items=items,
        cashSales=cashSales,
        tapSales=tapSales
    )
