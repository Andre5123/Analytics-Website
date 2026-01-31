from db.supabase_client import supabase

from werkzeug.security import check_password_hash, generate_password_hash

def checkLogin(username, password):
    # TODO: username validation
    
    user_info = supabase.table("users") \
        .select("id, password_hash") \
        .eq("username", username) \
        .execute().data
    
    if user_info != []:
        if check_password_hash(user_info[0]["password_hash"], password):
            return True, user_info[0]["id"]
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
    