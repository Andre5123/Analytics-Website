from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from helpers import toSQLDATETIME, toJSStringDate, login_required, \
    startEvent, stopEvent, getEventStatus, addSale, updateSale, getPastEvents, getItems, \
    updateItem, deleteItem, updateDeal, checkLogin,createUser, getUserId
from cs50 import SQL
from datetime import datetime
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from validator import validator

import os


from supabase_client import supabase



app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


currentSales = {}

db = SQL("sqlite:///database.db")

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
            success = startEvent()

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
    


@app.route("/update-sale", methods=["POST"])
def saleUpdate():
    #TODO: Validate data
    sale = request.get_json()

    print(sale)
    if not sale:
        return jsonify({"error":"JSON data not provided"}), 400

    print(sale)

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
        print("THE USER ID IS: ", newUser["id"])
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
            print("login successful, so it should work now right?")
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
    return render_template("home.html",eventActive=status)

@app.route("/history")
@login_required
def history():
    events = getPastEvents()
    return render_template("history.html", events = events)

@app.route("/analytics")
@login_required
def analytics():
    events = getPastEvents()
    items = getItems(True)
    print(events)

    return render_template("analytics.html", events = events, items=items)

@app.route("/inventory", methods=["GET", "POST"])
@login_required
def Inventory():
    if request.method == "GET":
        items = getItems(True)

        for item in items:
            item["unit_cost"] = item["cost"] / item["quantity"]
        return render_template("inventory.html", items=items)

@app.route("/event")
@login_required
def Event():
    #TODO: Re-add sales automatically when page reloads
    eventStatus = getEventStatus()
    if eventStatus:
        items = getItems(True) # A list of all items and their deals

        current_event_id = supabase.table("event_lock").select("current_event_id").execute().data[0]["current_event_id"]

        #TODO: add validation for if current_event_id is null

        # Previous sales made during this event
        sales = supabase.table("sales") \
            .select("*") \
            .eq("event_id", current_event_id) \
            .eq("user_id", session["user_id"]) \
            .execute().data     

        print("THE SALES ARE", sales)
        return render_template("event.html", items=items, eventSales=sales)
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

