from db.supabase_client import supabase
from utils.datetime_utils import toSQLDATETIME

def addSale(sale, user_id):
    """
    Adds a new sale with its items.
    sale = {
        payment_method,
        items: [{item, quantity, revenue, dealsApplied}],
        customRevenue (optional),
        sale_time
    }
    """
    # Get current event
    currentEvent = supabase.table("event_lock") \
        .select("active, current_event_id") \
        .eq("id", 1) \
        .execute()

    if not currentEvent.data:
        return False, {"success": False, "error": "Could not find event_lock entry"}

    event_id = currentEvent.data[0]["current_event_id"]
    event_active = currentEvent.data[0]["active"]

    if not event_active or not event_id:
        print(" EVENT inactive")
        return False, {"success": False, "error": "Event is inactive or closed"}

    # Calculate total revenue and cost
    total_revenue = sum(item["revenue"] for item in sale["items"])
    total_cost = 0
    for item in sale["items"]:
        item_data = supabase.table("items").select("*").eq("name", item["item"]).execute().data[0]
        unit_cost = item_data["cost"] / item_data["quantity"]
        total_cost += unit_cost * item["quantity"]
        item["cost"] = unit_cost * item["quantity"]

    # Insert sale row
    new_sale = supabase.table("sales").insert({
        "event_id": event_id,
        "user_id": user_id,
        "sale_time": toSQLDATETIME(sale.get("sale_time")),
        "payment_method": sale.get("payment_method"),
        "total_revenue": total_revenue,
        "total_cost": total_cost
    }).execute()

    sale_id = new_sale.data[0]["id"]

    # Insert items into sale_items
    for item in sale["items"]:
        supabase.table("sale_items").insert({
            "sale_id": sale_id,
            "item": item["item"],
            "quantity": item["quantity"],
            "revenue": item["revenue"],
            "cost": item["cost"]
        }).execute()

    return True, {"success": True, "saleId": sale_id}


def updateSale(sale):
    sale_id = sale.get("id")
    if not sale_id:
        return False, {"success": False, "error": "Sale ID not provided"}

    items = sale.get("items", [])

    # --- 1. Fetch all item cost data ONCE ---
    item_names = [i["item"] for i in items]

    item_rows = (
        supabase.table("items")
        .select("name, cost, quantity")
        .in_("name", item_names)
        .execute()
        .data
    )

    item_cost_map = {
        r["name"]: r["cost"] / r["quantity"]
        for r in item_rows
    }

    # --- 2. Compute totals ---
    total_revenue = 0
    total_cost = 0

    sale_items_payload = []

    for i in items:
        unit_cost = item_cost_map.get(i["item"], 0)
        cost = unit_cost * i["quantity"]

        total_revenue += i["revenue"]
        total_cost += cost

        sale_items_payload.append({
            "sale_id": sale_id,
            "item": i["item"],
            "quantity": i["quantity"],
            "revenue": i["revenue"],
            "cost": cost
        })

    # --- 3. Update sale header ---

    if sale.get("sale_time"):
        supabase.table("sales").update({
            "payment_method": sale.get("payment_method"),
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "sale_time": toSQLDATETIME(sale.get("sale_time"))
        }).eq("id", sale_id).execute()
    else:
        supabase.table("sales").update({
            "payment_method": sale.get("payment_method"),
            "total_revenue": total_revenue,
            "total_cost": total_cost,
        }).eq("id", sale_id).execute()

    # --- 4. UPSERT sale items (insert + update in one call) ---
    supabase.table("sale_items").upsert(
        sale_items_payload,
        on_conflict="sale_id,item"
    ).execute()

    # --- 5. Delete removed items in ONE query ---
    supabase.table("sale_items") \
        .delete() \
        .eq("sale_id", sale_id) \
        .not_.in_("item", item_names) \
        .execute()

    return True, {"success": True}


def deleteSale(sale_id):
    """
    Deletes a sale and all associated items.
    """
    if not sale_id:
        return False, {"success": False, "error": "Sale ID not provided"}

    supabase.table("sale_items").delete().eq("sale_id", sale_id).execute()
    supabase.table("sales").delete().eq("id", sale_id).execute()

    return True, {"success": True}
