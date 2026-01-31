
from db.supabase_client import supabase

def getItems(includeDeals):
    items = supabase.table("items") \
        .select("*") \
        .execute()
    
    items = items.data

    if includeDeals:
        for item in items:
            product_id = item["id"]
            deals = supabase.table("deals") \
                .select("*") \
                .eq("product_id", product_id) \
                .order("quantity") \
                .order("revenue") \
                .execute()
            item["deals"] = deals.data
            item["unit_cost"] = item["cost"] / item["quantity"]

    
    return items


# Updates an existing item or adds a new one
def updateItem(item):
    # Update item if item already exists
    if item.get("id") is None: # item does not exist, add new item
        newItem = supabase.table("items").insert({
            "name": item.get("name"),
            "quantity": item.get("quantity"),
            "cost": item.get("cost"),
        }).execute()
    else: #item exists, update item
        item = supabase.table("items") \
            .update({"name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "cost": item.get("cost")
                    }) \
            .eq("id", item.get("id")) \
            .execute()
    
    return True, {"success":True}

# Delete item
def deleteItem(item):
    # Update item if item already exists
    print("ITEM TO DELETE:", item)

    product_id = supabase.table("items").select("id").eq("name", item.get("name")).execute().data[0]["id"]

    result = supabase.table("deals").delete() \
    .eq("product_id", product_id) \
    .execute()

    result = supabase.table("items").delete() \
    .eq("name", item.get("name")) \
    .execute()
    
    return True, {"success":True}


# Update a deal on an item
def updateDeal(deal):
    dealId = deal.get("id")
    itemName = deal.get("item")
    product_id = supabase.table("items").select("id").eq("name", itemName).execute().data[0]["id"]
    quantity = deal.get("quantity")
    revenue = deal.get("revenue")
   
    if dealId is None: # item does not exist, add new item
        newDeal = supabase.table("deals").insert({
            "product_id": product_id,
            "quantity": quantity,
            "revenue": revenue,
        }).execute()
    else: #item exists, update item
        newDeal = supabase.table("deals").update({
            "quantity": quantity,
            "revenue": revenue,
        }) \
        .eq("id", dealId) \
        .execute()
    return True, {"success": True}
