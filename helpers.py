from datetime import datetime
import pytz

from flask import redirect, render_template, session
from functools import wraps
from supabase_client import supabase

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

import os


def toSQLDATETIME(date): #JSON file
    try:
        newDate = datetime.fromisoformat(date.replace("Z", "+00:00"))
        newDate = newDate.strftime("%Y-%m-%d %H:%M:%S")
        return newDate
    except ValueError as e:
        print("Parsing Error:",e)

def toJSStringDate(date): #From SQL format
    # Parse sql format
    dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    tz = "America/Toronto"
    tzInfo = pytz.timezone(tz)
    dt = tzInfo.localize(dt)

    #JS format:

    weekday = dt.strftime("%a")
    month = dt.strftime("%b")
    day = dt.strftime("%d")
    year = dt.strftime("%Y")
    time = dt.strftime("%H:%M:%S")
    gmt_offset = dt.strftime("GMT%z")
    tzname = "Eastern Standard Time"
    return f"{weekday} {month} {day} {year} {time} {gmt_offset} ({tzname})"

def login_required(f):

    loginEnabled = True
    # For debug testing
    
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For debug
        if loginEnabled and session.get("user_id") == "Insert ID":
            session["user_id"] = None
        elif not loginEnabled and session.get("user_id") is None:
            session["user_id"] = "Insert ID"

        if session.get("user_id") is None: #or session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Supabase database helper functions
# ---------------------------------------------------

# Login

def checkLogin(username, password):
    # TODO: username validation
    
    user_info = supabase.table("users") \
        .select("id, password_hash") \
        .eq("username", username) \
        .execute().data
    
    if user_info != []:
        if check_password_hash(user_info[0]["password_hash"], password):
            session["user_id"] = user_info[0]["id"]
            session["username"] = username
            return True, {"success":True}
        else:
            return False, {"success":False, "error":"Incorrect password / username"}
    else:
        return False, {"success":False, "error":"Incorrect password / username"}

# Create new user:

def getUserId(username):
    id = supabase.table("users") \
        .select("id") \
        .eq("username", username) \
        .execute().data
    if id != []:
        return id
    return None

def createUser(username, password):
    # TODO: username validation
    
    if getUserId(username):
        return False, {"success":False, "error":"There is already a user associated with this username"}

    user_info = supabase.table("users") \
        .insert({"username": username, "password_hash":generate_password_hash(password)}) \
        .execute().data
    return True, {"success":True, "id":user_info[0]["id"]}
    


# Events & Event_Lock Table

# Atomic queries to prevent race conditions on starting events
def startEvent():
    result = supabase.table("event_lock") \
        .update({"active": True}) \
        .eq("id", 1) \
        .eq("active", False) \
        .execute()
    
    if result.data == []:
        return False # Failed to start event, someone has already started an event
    else:
        # Success!

        # Make a new entry in the event table
        response = supabase.table("events").insert({
            "start_date": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")
        }).execute()

        newEventId = response.data[0]["id"]

        # Update the event lock to include the current event's id
        supabase.table("event_lock") \
            .update({"current_event_id": newEventId}) \
            .eq("id", 1) \
            .eq("active", True) \
            .execute()
        
        return True

def stopEvent():

    lock_row = supabase.table("event_lock") \
        .select("current_event_id") \
        .eq("id", 1) \
        .eq("active", True) \
        .execute()
    
    if not lock_row.data:
        return None #No active event to stop
    
    current_event_id = lock_row.data[0]["current_event_id"] # Save the id of the event that will be stopped
    # Stop the event
    supabase.table("event_lock") \
        .update({"active": False, "current_event_id": None}) \
        .eq("id", 1) \
        .eq("active", True) \
        .execute()
    
    # Update the current event's entry
    
    if current_event_id is not None:
        supabase.table("events") \
            .update({"end_date": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")}) \
            .eq("id", current_event_id) \
            .is_("end_date", None) \
            .execute()
    
    #Return the id of the stopped event
    return current_event_id

def getEventStatus():
    result = supabase.table("event_lock") \
        .select("active, current_event_id") \
        .eq("id", 1) \
        .execute()
    if not result.data:
        return False
    if result.data[0]["current_event_id"] is None or not result.data[0]["active"]:
        return False

    return result.data[0]

# Sales table

def addSale(sale):
    currentEvent = supabase.table("event_lock") \
        .select("active, current_event_id") \
        .eq("id", 1) \
        .execute()
    
    if not currentEvent.data:
        return False, {"success":False,"error": "could not find event_lock entry"}
    
    event_id = currentEvent.data[0]["current_event_id"]
    event_active = currentEvent.data[0]["active"]
    if not event_active or not event_id:
        return False, {"success":False, "error": "event is inactive / has been closed"}
    
    # Assumes data has already been server-validated

    itemName = sale.get("item")
    itemData = supabase.table("items").select("*").eq("name", itemName).execute().data[0]
    unitCost = itemData["cost"] / itemData["quantity"]
    totalCost = unitCost * sale.get("quantity")
    newSale = supabase.table("sales").insert({
        "event_id": event_id,
        "item": sale.get("item"),
        "quantity": sale.get("quantity"),
        "revenue": sale.get("revenue"),
        "cost": totalCost,
        "sale_time": toSQLDATETIME(sale.get("sale_time")),
        "payment_method": sale.get("payment_method"),
        "user_id": session["user_id"]
    }).execute()

    sale_id = newSale.data[0]["id"]

    return True, {"success":True, "saleId":sale_id}
    

def updateSale(sale):
    saleId = sale.get("id")
    if not saleId or not not isinstance(saleId, int):
        return False, {"success":False, "error": "server did not provide a sale id"}

    result = supabase.table("sales").update({
        "item": sale.get("item"),
        "quantity": sale.get("quantity"),
        "revenue": sale.get("revenue"),
        "sale_time": toSQLDATETIME(sale.get("sale_time")),
        "payment_method": sale.get("payment_method")
    }) \
    .eq("id", saleId) \
    .execute()


    return True, {"success":True}
    
def getPastEvents():
    events = supabase.table("events") \
        .select("id, start_date, end_date") \
        .order("start_date", desc=True) \
        .execute()
    events = events.data # Table containing all event entries
    for event in events:

        eventId = event["id"]
        sales = supabase.table("sales") \
        .select("*") \
        .eq("event_id", eventId) \
        .order("sale_time", desc=True) \
        .execute()
        event["sales"] = sales.data
    return events

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
