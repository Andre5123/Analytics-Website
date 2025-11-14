from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from helpers import toSQLDATETIME, toJSStringDate
from cs50 import SQL
from datetime import datetime

app = Flask("__name__")

eventStatus = {
    "active": False,
    "id": 0
    }
currentSales = {}

db = SQL("sqlite:///database.db")
# APIs


@app.route("/event-status", methods=["GET", "POST"])
def getEvent():
    if request.method == "GET":
        return jsonify(eventStatus)
    elif request.method == "POST":
        data = request.get_json()
        newStatus = data.get("eventStatus", eventStatus)

        # Validation of data
        if (newStatus != True and newStatus != False):
            print("Error: json request not formatted correctly")
            return "Error: json request not formatted correctly"

        #Return values
        eventStatus["active"] = newStatus
        if newStatus == True:
            print("now creating event")
            startDate = datetime.now()
            startDate = startDate.isoformat(" ")
            eventId = db.execute("INSERT INTO events (startDate) VALUES (?)", startDate)
            eventStatus["id"] = eventId
        else:
            endDate = datetime.now()
            endDate = endDate.isoformat(" ")
            db.execute("UPDATE events SET endDate = ? WHERE (id = ?)", endDate, eventStatus["id"])
        return jsonify({
            "success": True,
            "status": newStatus
            })

@app.route("/past-events", methods=["GET"])
def pastEvents():
    pastEvents = db.execute("SELECT events.id, events.startDate, events.endDate, sales.event_id, sales.item, sales.quantity, sales.amtPaid, sales.saleDate, sales.paymentMethod FROM sales JOIN events ON (events.id = sales.event_id) ORDER BY sales.event_id DESC")
    events = {}
    for row in pastEvents:
        eventId = row["event_id"]
        if eventId not in events:
            events[eventId] = {"eventStart":row["startDate"],
                                   "eventEnd": row["endDate"],
                                   "sales": []
                                   }
        events[eventId]["sales"].append({"item": row["item"],
                                    "quantity": row["quantity"],
                                    "amtPaid": row["amtPaid"],
                                    "saleDate": row["saleDate"],
                                    "paymentMethod": row["paymentMethod"]})
    items = db.execute("SELECT * FROM items")
    print(events)
    return jsonify({"events":events, "items":items})

@app.route("/get-items", methods=["GET"])
def getItems():
    items = db.execute("SELECT * FROM items")
    itemCosts = {}
    for item in items:
        itemCosts[item["name"]] = {"costPerItem": item["cost"]/item["buyQuantity"]}
    return jsonify(itemCosts)

@app.route("/update-sale", methods=["POST"])
def updateSale():
    #TODO: Validate data
    sale = request.get_json();

    print(sale)
    if not sale:
        return jsonify({"error":"JSON data not provided"}), 400

    print(sale)

    saleId = sale.get("id")
    item = sale.get("item")
    quantity = sale.get("quantity")
    paid = sale.get("amtPaid")
    date = sale.get("date")
    date = toSQLDATETIME(date);
    paymentMethod = sale.get("paymentMethod")
    #Todo: Better validation
    if not item or not isinstance(quantity, int) or quantity <0 or not isinstance(paid, (int, float)) or paid<0 or not date or not paymentMethod:
        return jsonify({"error":"JSON data incorrectly formatted"}), 400

    # Newly created sale
    if not saleId:
        newId = db.execute("INSERT INTO sales (event_id, item, quantity, amtPaid, saleDate, paymentMethod) VALUES (?,?,?,?,?,?)", eventStatus["id"], item, quantity, paid, date, paymentMethod)
        return jsonify({"saleId":newId, "success":True})
    else:
        db.execute("UPDATE sales SET item = ?, quantity = ?, amtPaid = ?, saleDate = ?, paymentMethod = ? WHERE id = ?", item, quantity, paid, date, paymentMethod, saleId)
        return jsonify({"success":True})

@app.route("/new-item", methods=["POST"])
def updateItem():
    #TODO: Validate data
    #Check if item already exists

    item = request.get_json()
    print(item)
    name = item.get("name")
    quantity = item.get("buyQuantity")
    cost = item.get("cost")
    itemId = db.execute("INSERT INTO items (name, buyQuantity, cost) VALUES (?,?,?)", name, quantity, cost)
    return jsonify({"success":True})

@app.route("/delete-item", methods=["POST"])
def deleteItem():
    #TODO: Validate data
    #Check if item exists

    item = request.get_json()
    print(item)
    name = item.get("name")
    itemId = db.execute("SELECT id FROM items WHERE name = ?", name)[0]["id"]
    # delete the deals associate with the item
    db.execute("DELETE FROM deals WHERE product_id = ?", itemId)
    # delete the item
    db.execute("DELETE FROM items WHERE id = ?", itemId)
    return jsonify({"success":True})

@app.route("/update-deal", methods=["POST"])
def updateDeal():
    #TODO: Validate data
    #TODO: Check that dealId is valid

    deal = request.get_json()
    print(deal)
    dealId = deal.get("id")
    itemName = deal.get("item")
    quantity = deal.get("quantity")
    price = deal.get("price")

    item_id = db.execute("SELECT id FROM items WHERE name = ?", itemName)[0]["id"];

    # Make a new deal
    if not dealId:

        dealId = db.execute("INSERT INTO deals (product_id, quantity, price) VALUES (?,?,?)", item_id, quantity, price)
        return jsonify({"dealId": dealId, "success":True})
    # Update existing deal
    else:
        db.execute("UPDATE deals SET quantity = ?, price = ? WHERE id = ?", quantity, price, dealId)
    return jsonify({"success":True})
@app.route("/")
def index():
    return render_template("home.html")

@app.route("/history")
def history():
    rows = db.execute("SELECT events.id, events.startDate, events.endDate, sales.event_id, sales.item, sales.quantity, sales.amtPaid, sales.saleDate, sales.paymentMethod FROM sales JOIN events ON (events.id = sales.event_id) ORDER BY sales.event_id DESC")
    events = {}
    for row in rows:
        print("THIS IS THE ROW", row)
        eventId = row["event_id"]
        if eventId not in events:
            events[eventId] = {"eventStart":row["startDate"],
                                   "eventEnd": row["endDate"],
                                   "sales": []
                                   }
        events[eventId]["sales"].append({"item": row["item"],
                                    "quantity": row["quantity"],
                                    "amtPaid": row["amtPaid"],
                                    "saleDate": row["saleDate"],
                                    "paymentMethod": row["paymentMethod"]
                                    })

    return render_template("history.html", events = events)


@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/inventory", methods=["GET", "POST"])
def Inventory():
    if request.method == "GET":
        itemDeals = {}
        items = db.execute("SELECT * FROM items")
        if items:
            for item in items:
                deals = db.execute("SELECT * FROM deals WHERE product_id = ? ORDER BY quantity ASC, price ASC", item["id"])
                itemDeals[item["name"]] = deals
        else:
            print("none")

        itemCosts = {}
        for item in items:
            itemCosts[item["name"]] = {"costPerUnit": item["cost"]/item["buyQuantity"]}

        return render_template("inventory.html", itemDeals = itemDeals, itemCosts=itemCosts)


@app.route("/event")
def Event():
    #TODO: Re-add sales automatically when page reloads
    print(eventStatus["active"], "the new status")
    if eventStatus["active"] == True:
        itemList = db.execute("SELECT id, name FROM items")

        # Pass along all of the deals for each item
        itemDeals = {}
        for item in itemList:
            itemId = item["id"]
            deals = db.execute("SELECT * FROM deals WHERE product_id = ? ORDER BY quantity ASC, price ASC", itemId)
            itemDeals[item["name"]] = deals

        # Previous sales made during this event
        eventSales = db.execute("SELECT id, item, quantity, amtPaid, saleDate, paymentMethod FROM sales WHERE event_id= ?", eventStatus["id"])

        for sale in eventSales:
            sale["saleDate"] = toJSStringDate(sale["saleDate"])


        return render_template("event.html", itemDeals=itemDeals, eventSales=eventSales)
    else:
        return jsonify("No event currently being held");

#TODO: SQL DATABASE with unique ID for different events, and unique ID for different sales

# Analytics page to display statistics like ranking all-time best-selling items, best-selling items in inventory.
# Inventory page to update the items and any deals they may have
# Auto-price calculator
# Display previous events & previous transactions, as well as total revenue from each sale
# Login page

#Minor details
# Add total profit counter for events page

