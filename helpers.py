from datetime import datetime
import pytz

from flask import redirect, render_template, session, g
from functools import wraps
from supabase_client import get_supabase

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
    
    user_info = g.supabase.table("users") \
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
    id = g.supabase.table("users") \
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

    user_info = g.supabase.table("users") \
        .insert({"username": username, "password_hash":generate_password_hash(password)}) \
        .execute().data
    return True, {"success":True, "id":user_info[0]["id"]}
    


# Events & Event_Lock Table

# Atomic queries to prevent race conditions on starting events
def startEvent(eventCost, menuId):
    result = g.supabase.table("event_lock") \
        .update({"active": True}) \
        .eq("id", 1) \
        .eq("active", False) \
        .execute()
    
    if result.data == []:
        return False # Failed to start event, someone has already started an event
    else:
        # Success!

        # Make a new entry in the event table
        response = g.supabase.table("events").insert({
            "start_date": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "cost":eventCost,
            "menu_id": menuId,
        }).execute()

        newEventId = response.data[0]["id"]

        # Update the event lock to include the current event's id
        g.supabase.table("event_lock") \
            .update({"current_event_id": newEventId}) \
            .eq("id", 1) \
            .eq("active", True) \
            .execute()
        
        return True

def stopEvent():

    lock_row = g.supabase.table("event_lock") \
        .select("current_event_id") \
        .eq("id", 1) \
        .eq("active", True) \
        .execute()
    
    if not lock_row.data:
        return None #No active event to stop
    
    current_event_id = lock_row.data[0]["current_event_id"] # Save the id of the event that will be stopped
    # Stop the event
    g.supabase.table("event_lock") \
        .update({"active": False, "current_event_id": None}) \
        .eq("id", 1) \
        .eq("active", True) \
        .execute()
    
    # Update the current event's entry
    
    if current_event_id is not None:
        g.supabase.table("events") \
            .update({"end_date": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")}) \
            .eq("id", current_event_id) \
            .is_("end_date", None) \
            .execute()
    
    #Return the id of the stopped event
    return current_event_id

def getEventStatus():
    result = g.supabase.table("event_lock") \
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
    currentEvent = g.supabase.table("event_lock") \
        .select("active, current_event_id") \
        .eq("id", 1) \
        .execute()
    
    if not currentEvent.data:
        return False, {"success":False,"error": "could not find event_lock entry"}
    
    event_id = currentEvent.data[0]["current_event_id"]
    event_active = currentEvent.data[0]["active"]
    if not event_active or not event_id:
        return False, {"success":False, "error": "event is inactive / has been closed"}
    
    subscriberId = sale.get("subscriber_id")
    newSubscriberBalance = 0
    if subscriberId:
        subscriber = g.supabase.table("subscribers") \
            .select("*") \
            .eq("id", subscriberId) \
            .execute().data
        
        if subscriber == []:
            return False, {"success":False, "error": "Could not find subscriber"}
        
        subscriber = subscriber[0]

        
        
        # recalculate the new subscriber Balance by counting up all of their purchases.
        subscription = g.supabase.table("subscriptions").select("*") \
            .eq("id", subscriber["subscription_id"]) \
            .execute().data
        
        if subscription == []:
            return False, {"success":False, "error": "Subscriber does not have an existing subscription"}

        subscription = subscription[0]

        expenditures = g.supabase.table("sales").select("*").eq("subscriber_id", subscriberId).execute().data
        totalSpent = sale.get("revenue")

        for Sale in expenditures:
            totalSpent += Sale["revenue"]

        # subtract the total expenditures from the initial balance
        newSubscriberBalance = subscription["balance"] - totalSpent
        print("new balance is", newSubscriberBalance)
        if newSubscriberBalance < 0:
            print(subscriber, subscription, totalSpent, "are the data")
            return False, {"success":False, "error": "Subscriber does not have enough money, this sale update may not be saved."}
        
        
        result = g.supabase.table("subscribers").update({
                "balance": newSubscriberBalance
            }) \
            .eq("id", subscriberId) \
            .execute()
        
        



    
    # Assumes data has already been server-validated

    itemName = sale.get("item")
    itemData = g.supabase.table("items").select("*").eq("name", itemName).execute().data[0]
    unitCost = itemData["cost"] / itemData["quantity"]
    totalCost = unitCost * sale.get("quantity")
    newSale = g.supabase.table("sales").insert({
        "event_id": event_id,
        "item": sale.get("item"),
        "quantity": sale.get("quantity"),
        "revenue": sale.get("revenue"),
        "cost": totalCost,
        "sale_time": toSQLDATETIME(sale.get("sale_time")),
        "payment_method": sale.get("payment_method"),
        "user_id": session["user_id"],
        "subscriber_id": subscriberId
    }).execute()

    sale_id = newSale.data[0]["id"]

    return True, {"success":True, "saleId":sale_id}
    

def updateSale(sale):
    print("the sale is", sale)
    saleId = sale.get("id")
    if not saleId or not not isinstance(saleId, int):
        return False, {"success":False, "error": "server did not provide a sale id"}

    subscriberId = sale.get("subscriber_id")
    newSubscriberBalance = 0
    if subscriberId:
        subscriber = g.supabase.table("subscribers") \
            .select("*") \
            .eq("id", subscriberId) \
            .execute().data
        
        if subscriber == []:
            return False, {"success":False, "error": "Could not find subscriber"}
        
        subscriber = subscriber[0]

        
        
        # recalculate the new subscriber Balance by counting up all of their purchases.
        subscription = g.supabase.table("subscriptions").select("*") \
            .eq("id", subscriber["subscription_id"]) \
            .execute().data
        
        if subscription == []:
            return False, {"success":False, "error": "Subscriber does not have an existing subscription"}

        subscription = subscription[0]

        expenditures = g.supabase.table("sales").select("*").eq("subscriber_id", subscriberId).execute().data
        totalSpent = sale.get("revenue")

        for Sale in expenditures:
            print(totalSpent)
            totalSpent += Sale["revenue"]

        # subtract the total expenditures from the initial balance
        newSubscriberBalance = subscription["balance"] - totalSpent
        print("new balance is", newSubscriberBalance)
        if newSubscriberBalance < 0:
            print(subscriber, subscription, totalSpent, "are the data")
            return False, {"success":False, "error": "Subscriber does not have enough money, this sale update may not be saved."}
        
        
        result = g.supabase.table("subscribers").update({
                "balance": newSubscriberBalance
            }) \
            .eq("id", subscriberId) \
            .execute()
    
    currentSale = g.supabase.table("sales").select("*").eq("id", saleId).execute().data[0]

    # Recalculate the previous subscriber's balance and reimburse them.
    if currentSale["subscriber_id"] != subscriberId and currentSale["subscriber_id"]:

        prevSubscriber = g.supabase.table("subscribers").select("*") \
            .eq("id", currentSale["subscriber_id"]) \
            .execute().data[0]
        

        g.supabase.table("subscribers").update({
            "balance": prevSubscriber["balance"] + currentSale["revenue"]
        }) \
        .eq("id", currentSale["subscriber_id"]) \
        .execute()

    print("the subscriber's id is", subscriberId)
    result = g.supabase.table("sales").update({
        "item": sale.get("item"),
        "quantity": sale.get("quantity"),
        "revenue": sale.get("revenue"),
        "sale_time": toSQLDATETIME(sale.get("sale_time")),
        "payment_method": sale.get("payment_method"),
        "subscriber_id": subscriberId
    }) \
    .eq("id", saleId) \
    .execute()


    return True, {"success":True}
    
def addSubscription(data):
    
    # Assumes data has already been server-validated

    itemPrice = data.get("price")
    itemBalance= data.get("balance")
    
    if g.supabase.table("subscriptions").select("*").eq("price", itemPrice).execute().data != []:
        return False, {"success":False, "error": "A subscription has already been made with this price"}
    
    newSale = g.supabase.table("subscriptions").insert({
        "price": itemPrice,
        "balance": itemBalance
    }).execute()

    subscription_id = newSale.data[0]["id"]

    return True, {"success":True, "subscriptionId":subscription_id}

def addSubscriber(data):
    
    # Assumes data has already been server-validated

    subPrice = data.get("price")
    subName = data.get("name")
    subscription =  g.supabase.table("subscriptions").select("*").eq("price", subPrice).execute().data # Find the specific subscription by unique price

    currentEvent = g.supabase.table("event_lock") \
        .select("active, current_event_id") \
        .eq("id", 1) \
        .execute()
    
    if not currentEvent.data:
        return False, {"success":False,"error": "could not find event_lock entry"}
    
    event_id = currentEvent.data[0]["current_event_id"]
    event_active = currentEvent.data[0]["active"]
    if not event_active or not event_id:
        return False, {"success":False, "error": "event is inactive / has been closed"}

    if subscription == []:
        return False, {"success":False, "error": "Could not find a subscription with this price"}
    else:
        subscription = subscription[0]
    
    newSubscriber = g.supabase.table("subscribers").insert({
        "subscription_id": subscription["id"], \
        "event_id": event_id, \
        "balance": subscription["balance"], \
        "name": subName \
    }).execute()
    

    subscriber_id = newSubscriber.data[0]["id"]

    return True, {"success":True, "subscriberId":subscriber_id}

def getPastEvents():
    events = g.supabase.table("events") \
        .select("id, start_date, end_date, cost, menu_id") \
        .order("start_date", desc=True) \
        .execute()
    events = events.data # Table containing all event entries
    for event in events:
        eventId = event["id"]
        sales = g.supabase.table("sales") \
        .select("*") \
        .eq("event_id", eventId) \
        .order("sale_time", desc=True) \
        .execute()
        event["sales"] = sales.data

        menuItems = g.supabase.table("items").select("*") \
        .eq("menu_id", event["menu_id"]) \
        .execute()

        menu = g.supabase.table("menus").select("*").eq("id", event["menu_id"]).execute()
        menuName = menu.data[0]["name"]
        event["menu_name"] = menuName 
        event["menu_items"] = menuItems.data

        subSales = g.supabase.table("subscribers") \
            .select("*") \
            .eq("event_id", eventId) \
            .execute().data  
        
        for subSale in subSales:
            subscription = g.supabase.table("subscriptions") \
                .select("*") \
                .eq("id", subSale["subscription_id"]) \
                .execute().data[0]
            subSale["price"] = subscription["price"]

        event["subSales"] = subSales
    return events

def newMenu(name):
    alreadyExists = g.supabase.table("menus").select("*").eq("name",name).execute()
    if alreadyExists.data == []: # create new one
        newMenu = g.supabase.table("menus").insert({
            "name": name
        }, returning="representation").execute()
        return True, {"success": True, "menuId": newMenu.data[0]["id"]}
    else:
        return True, {"success": True, "menuId": alreadyExists.data[0]["id"]}

def getMenus():
    menus = g.supabase.table("menus") \
        .select("*") \
        .execute()
    
    menus = menus.data

    return menus

def getSubscriptions():
    subscriptions = g.supabase.table("subscriptions") \
        .select("*") \
        .order("price") \
        .order("balance") \
        .execute().data
    
    for subscription in subscriptions:
        print(subscription, "is the Subscription")
        subscribers = g.supabase.table("subscribers") \
            .select("*") \
            .eq("subscription_id", subscription["id"]) \
            .execute().data
        
        subscription["subscribers"] = subscribers

    return subscriptions

def getItems(includeDeals, menuId):
    items = g.supabase.table("items") \
        .select("*") \
        .eq("menu_id", menuId) \
        .execute()
    
    items = items.data

    if includeDeals:
        for item in items:
            product_id = item["id"]
            deals = g.supabase.table("deals") \
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
        newItem = g.supabase.table("items").insert({
            "name": item.get("name"),
            "quantity": item.get("quantity"),
            "cost": item.get("cost"),
            "menu_id": item.get("menu_id"),
        }, returning="representation").execute()
        return True, {"success":True, "itemId":newItem.data[0]["id"]}
    else: #item exists, update item
        item = g.supabase.table("items") \
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

    product_id = item.id

    result = g.supabase.table("deals").delete() \
    .eq("product_id", product_id) \
    .execute()

    result = g.supabase.table("items").delete() \
    .eq("id", item.id) \
    .execute()
    
    return True, {"success":True}


# Update a deal on an item
def updateDeal(deal):
    dealId = deal.get("id")
    product_id = deal.get("product_id")
    quantity = deal.get("quantity")
    revenue = deal.get("revenue")
   
    if dealId is None: # item does not exist, add new item
        newDeal = g.supabase.table("deals").insert({
            "product_id": product_id,
            "quantity": quantity,
            "revenue": revenue,
        }, returning="representation").execute()
        return True, {"success": True, "dealId": newDeal.data[0]["id"]}
    else: #item exists, update item
        newDeal = g.supabase.table("deals").update({
            "quantity": quantity,
            "revenue": revenue,
        }) \
        .eq("id", dealId) \
        .execute()
    return True, {"success": True}
