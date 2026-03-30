import logging

logging.basicConfig(
    level=logging.WARNING,
    force=True
)

from flask import Flask, redirect, render_template, request, session, jsonify, url_for, g
from flask_session import Session
from helpers import toSQLDATETIME, toJSStringDate, login_required, \
    startEvent, stopEvent, getEventStatus, addSale, updateSale, getPastEvents, getItems, getMenus, getSubscriptions, \
    newMenu, updateItem, deleteItem, updateDeal, checkLogin,createUser, getUserId, addSubscription, addSubscriber 
from cs50 import SQL
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from validator import validator


import os


from supabase_client import get_supabase



app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


currentSales = {}



@app.before_request
def inject_supabase():
    g.supabase = get_supabase()


# Client-to-Server APIs
# ---------------------------------------------------------------
@app.route("/event-status", methods=["GET", "POST"])
def getEvent():
    if request.method == "GET":
        eventData = getEventStatus()
        if (eventData):
            return jsonify(eventData["active"])
        else:
            return jsonify(False)
    elif request.method == "POST":
        data = request.get_json()
        newStatus = data.get("eventStatus")

        # Validation of data
        if (newStatus != True and newStatus != False):
            print("Error: json request not formatted correctly")
            return "Error: json request not formatted correctly"

        #Return values
        if newStatus == True:
            # Check if event has already started
            eventCost = data.get("cost")
            menuId = data.get("menu_id")
            if not isinstance(eventCost, (int, float)):
                 return jsonify({
                            "success": False,
                            "status": True,
                            "error": "Error: event cost must be a decimal or integer"
                        })
            
            success = startEvent(eventCost, menuId)

            if not success:
                return jsonify({
                            "success": False,
                            "status": True,
                            "error": "Error: someone has already started an event"
                        })
        else:
            result = stopEvent()         
        return jsonify({
            "success": True,
            "status": newStatus
            })
    
@app.route("/update-subscriber", methods=["POST"])
def subscriptionUpdate():
    subscriber = request.get_json()
    if not subscriber:
        return jsonify({"error":"JSON data not provided"}), 400


    subscriberId = subscriber.get("id")

    # Validate sale data TODO
    

    # Newly created sale
    if not subscriberId:
        success, content = addSubscriber(subscriber)
        if not success:
            print("Error: ", content["error"])
        return jsonify(content)
    else:
        pass


    

@app.route("/update-sale", methods=["POST"])
def saleUpdate():
    #TODO: Validate data
    sale = request.get_json()

    if not sale:
        return jsonify({"error":"JSON data not provided"}), 400


    saleId = sale.get("id")

    # Validate sale data
    valid, error = validator.sale_data(sale)
    if not valid: 
        return jsonify(error)
    

    # Newly created sale
    if not saleId:
        success, content = addSale(sale)
        if not success:
            print("Error: ", content["error"])
        return jsonify(content)
    else:
        success, content = updateSale(sale)
        if not success:
            print("Error: ", content["error"])
        return jsonify(content)

@app.route("/new-item", methods=["POST"])
def newItem():
    #TODO: Validate data, check if Item id is a number, check if item name already used
    #Check if item already exists
    item = request.get_json()

    #Add validator here

    success, content = updateItem(item)
    return jsonify(content)
    

@app.route("/delete-item", methods=["POST"])
def removeItem():
    #TODO: Validate data
    #Check if item exists

    item = request.get_json()
    success, content = deleteItem(item)
    return jsonify(content)

@app.route("/new-subscription", methods=["POST"])
def newSubscription():
    subData = request.get_json()
    
    success, content = addSubscription(subData)
    return jsonify(content)

@app.route("/update-deal", methods=["POST"])
def changeDeal():
    #TODO: Validate data
    #TODO: Check that dealId is valid

    deal = request.get_json()
    
    success, content = updateDeal(deal)
    return jsonify(content)
# Pages ----------------------------


# Login pages:

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "GET":
        return render_template("verify.html", codeSent=False)

    if request.method == "POST":
        if not request.form.get("emailCode"):
            # Send the code via email
            email = request.form.get("email")
            session["emailToVerify"] = email
            if getUserId(email):
                return render_template("verify.html", codeSent = False, error = "There is already a user associated with this email")
            

            #TODO: Check that the email doesn't already have an account
            code = send_verification_code(email)
            session["emailCode"] = code
            return render_template("verify.html", codeSent = True)
        else:
            # TODO: Verify the user entered the correct email code
            emailCode = request.form.get("emailCode")

            if emailCode == session["emailCode"]:
                session["email"] = session["emailToVerify"]
                return redirect("/register")
            else:
                return render_template("verify.html", codeSent = False, error = "The verification code you entered was not correct. Try again.")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmPassword")

        if getUserId(username):
            return render_template("register.html", error="Username already in use.")
        if password == None or password == "":
            return render_template("register.html", error="Please enter a password.")
        
        if password != confirmation:
            return render_template("register.html", error="Passwords do not match each other.")
        
        session["username"] = username
        success, newUser = createUser(session["username"], password)
        session["user_id"] = newUser["id"]
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        loginSuccessful, content = checkLogin(username, password)
        if loginSuccessful:
            return redirect("/")
        else:
            return render_template("login.html", loginFailed=True)

# Content pages:

@app.route("/")
@login_required
def index():
    status = getEventStatus()
    if status:
        status = True
    else:
        status = False
    
    menus = g.supabase.table("menus").select("*").execute()
    menus = menus.data
    return render_template("home.html",eventActive=status, menus=menus)

@app.route("/history")
@login_required
def history():
    events = getPastEvents()
    return render_template("history.html", events = events)

@app.route("/analytics")
@login_required
def analytics():
    events = getPastEvents()

    

    return render_template("analytics.html", events = events)

@login_required
@app.route("/inventory", methods=["GET", "POST"])
def Inventory():
     if request.method == "GET":
        menus = getMenus()
        subscriptions = getSubscriptions()
        return render_template("inventory.html", menus=menus, subscriptions=subscriptions)
     elif request.method == "POST":
        menuData = request.get_json()
        menuId = menuData.get("id")
        print("The id is ", menuId)
        if not menuData.get("id"): # Create a new menu
            success, content = newMenu(menuData.get("name"))
            if success:
                menuId = content["menuId"]
            else:
                return jsonify(content)
        
        return jsonify({"success":True, "redirect": url_for("Items", menuId=menuId)})
     
@login_required


@app.route("/items", methods=["GET", "POST"])
@login_required
def Items():
    if request.method == "GET":
        menuId = request.args.get("menuId")
        print("menuId", menuId)
        menu = g.supabase.table("menus").select("id, name").eq("id", menuId).execute()
        if menu.data == []:
            return redirect("inventory")
        menu = menu.data[0]
        
        items = getItems(True, menuId)

        for item in items:
            item["unit_cost"] = item["cost"] / item["quantity"]
        return render_template("items.html", items=items, menu=menu)

@app.route("/event")
@login_required
def Event():
    #TODO: Re-add sales automatically when page reloads
    eventStatus = getEventStatus()
    if eventStatus:

        current_event_id = g.supabase.table("event_lock").select("current_event_id").execute().data[0]["current_event_id"]

        menuId = g.supabase.table("events").select("menu_id").eq("id", current_event_id).execute().data[0]["menu_id"]
        items = getItems(True, menuId) # A list of all items and their deals

        #TODO: add validation for if current_event_id is null

        # Previous sales made during this event
        sales = g.supabase.table("sales") \
            .select("*") \
            .eq("event_id", current_event_id) \
            .eq("user_id", session["user_id"]) \
            .order("id", desc=True) \
            .order("sale_time", desc=True) \
            .execute().data

        subSales = g.supabase.table("subscribers") \
            .select("*") \
            .eq("event_id", current_event_id) \
            .execute().data  
        
        for subSale in subSales:
            subscription = g.supabase.table("subscriptions") \
                .select("*") \
                .eq("id", subSale["subscription_id"]) \
                .execute().data[0]
            subSale["price"] = subscription["price"]
        
        subscriptions = g.supabase.table("subscriptions")\
            .select("*") \
            .execute().data

        subscribers = g.supabase.table("subscribers")\
            .select("*") \
            .order("name") \
            .execute().data    

        return render_template("event.html", items=items, eventSales=sales, eventSubSales = subSales, subscriptions=subscriptions, subscribers=subscribers)
    else:
        return jsonify("No event currently being held")

#TODO: SQL DATABASE with unique ID for different events, and unique ID for different sales

# Analytics page to display statistics like ranking all-time best-selling items, best-selling items in inventory.
# Inventory page to update the items and any deals they may have
# Auto-price calculator
# Display previous events & previous transactions, as well as total revenue from each sale
# Login page

#Minor details
# Add total profit counter for events page

