from db.supabase_client import supabase
from utils.datetime_utils import now_utc_sql

def startEvent(eventCost):
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
        print("event cost is", eventCost)
        response = supabase.table("events").insert({
            "start_date": now_utc_sql(),
            "cost": eventCost,
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
            .update({"end_date": now_utc_sql()}) \
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