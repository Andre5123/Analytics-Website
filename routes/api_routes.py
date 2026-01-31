from flask import Blueprint, request, jsonify, session
from services.event_service import startEvent, stopEvent, getEventStatus
from services.sales_service import addSale, updateSale, deleteSale
from services.items_service import updateItem, deleteItem, updateDeal
from validator import validator

api_bp = Blueprint("api", __name__)

@api_bp.route("/event-status", methods=["GET", "POST"])
def event_status():
    if request.method == "GET":
        eventData = getEventStatus()
        return jsonify(eventData["active"] if eventData else False)

    data = request.get_json()
    newStatus = data.get("eventStatus")
    eventCost = data.get("cost")
    if newStatus not in [True, False]:
        return jsonify({"error": "Invalid eventStatus"}), 400

    if newStatus:
        success = startEvent(eventCost)
        if not success:
            return jsonify({"success": False, "status": True, "error": "Event already started"})
    else:
        stopEvent()
    return jsonify({"success": True, "status": newStatus})

@api_bp.route("/update-sale", methods=["POST"])
def update_sale():
    sale = request.get_json()
    if not sale:
        print("NO JSON PROVIDED")
        return jsonify({"error": "No JSON provided"}), 400

    user_id = session.get("user_id")
    if not user_id:
        print("NO LOGIN")
        return jsonify({"success": False, "error": "User not logged in"}), 403

    if not sale.get("id"):
        print("NEW ITEM HAS BEEN MADE")
        success, content = addSale(sale, user_id)
    else:
        print("ITEM HAS BEEN UPDATED")
        success, content = updateSale(sale)

    return jsonify(content)


@api_bp.route("/delete-sale", methods=["POST"])
def delete_sale():
    data = request.get_json()
    sale_id = data.get("id")
    if not sale_id:
        return jsonify({"success": False, "error": "Sale ID required"}), 400

    success, content = deleteSale(sale_id)
    return jsonify(content)


@api_bp.route("/new-item", methods=["POST"])
def new_item():
    item = request.get_json()
    success, content = updateItem(item)
    return jsonify(content)

@api_bp.route("/delete-item", methods=["POST"])
def delete_item():
    item = request.get_json()
    success, content = deleteItem(item)
    return jsonify(content)

@api_bp.route("/update-deal", methods=["POST"])
def update_deal():
    deal = request.get_json()
    success, content = updateDeal(deal)
    return jsonify(content)
