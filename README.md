# Bake Sale Analytics Website
#### Video Demo:  <[https://youtu.be/emxgEkel2gI]>
#### Description:

My Final Project for CS50 is a sale tracker / analytics website designed to assist my school bake sale team.

# Requirements:

The requirements to run this project are listed in requirements.txt
Note that it will not work in the CS50 dev environment because several of the needed modules are missing, such as the supabase module which allows this project to access its cloud-based SQL database.

# Project explanation:

These are the features:
There is a simple registration and login system to differentiate between users. To sign up, you go to the registration page, enter
a username and a password, confirm your password, and then register. To log in, you go to the login page and enter your username and password. There is also server-side validation such as checking if a username has already been used. It will display error messages if the registration fails.

when you log in / register, you end up on the home page, On the home page, you can click "create new event" to host a new sale event.
If an event is already ongoing, the button will say "continue event instead". Clicking this button will take you to the event page, which will be explained later.

From the dashboard, you can go to the inventory tab where users can update the items that they are selling. To add a new item to your inventory, simply fill out its name, the quantity that you bought, and the amount that you bought it for. After adding the item, it will appear in your inventory and you can create new deals for each item. For each deal you set the quantity you are selling and the amount that you are selling it for. You can also make multiple deals. For example, if you were to sell oranges, you could sell make a deal selling 1 orange for $1, but 5 oranges for $3. When you edit a deal, it will automatically calculate the profit.


The event page is only available any time there is an event active. In it, you can document every sale made during the event. To do this, simply click on the button for the type of item that was sold, and a new entry will be made. There are new entry buttons for each item created in the inventory tab. Within the entry, you can fill out (or see)  information like the date, payment method (cash/tap) and quantity sold, and it will automatically show the revenue you should have gained based on the deals you have set. It will calculate the cheapest deals for a given quantity, and can even stack multiple deals on top of each other. If the customer pays a custom amount, you can override the deals by setting an extra field. Every time you create a new entry or edit one, it is important to click "update" to ensure that the entries  are saved, even if you exit out of the event page. Once you are done with your event, you can close it by clicking "end event".

The analytics tab shows statistics like total cost, revenue and profit for all past events (and the current one, if applicable). It also does item by item analysis to show which items generated the most cost, revenue and profit during each event.

The transactions tab displays all of the events and the transactions that occured within each of them, timestamped, as well as all of the information regarding each task.
-
- An analytics tab that provides statistics on each sale event hosted
- A transaction tab that lists every past sale event (and the current ongoing one, if it exists) and all of the sale transactions that occured within each event.

# Files:
app.py: The main code file for this project. It uses flask to load different web pages, as well as handling http-requests from the user, such as saving entries / items.

helpers.py: As the name suggests, this file containes my helper functions, such as different data validators such as the login verification ,flask decorators like @login_required, and functions for getting information out of my SQL database.

validator.py: This file contains more heavy-duty validator functions, like my new sale validation function which needs to check a lot more conditions, and so I felt it was appropriate to put it in a separate file.

supabase_client.py: This file is responsible for setting up my supabase client to be used by the other code files. Supabase is the cloud-based PostgresSQL database that I chose to use for my project.

My database stores information in several different tables:
- items
- deals
- events (past events)
- event_lock (holds the only id / info of the current event)
- users

Race conditions was a concern when designing  my project around the database system. Since it is possible for several of my team members to use the website at once and be on the same event, I addressed this issue by making separate event streams for each user. Every time a user re-enters the event page they are identified by their ID, and they can see and update only the sales that they made previously. This effectively eliminated the possibility of race conditions.

Within static:
templates folder:
Contains all of the HTML templates for all of the aforementioned pages / tabs that are loaded by flask. They use jinja to be more dynamic and pass along information from the server when rendering an html page, such as whether there is an event ongoing or not.

layout.html is the general layout of every page which is built upon by all the other html templates with jinja. It contains the website name, credits, and the dashboard. Using jinja, the dashboard changes to show different tabs depending on whether the user is logged in or not logged in.

verify.html is a deprecated template that was initially used for email-verification before it was scrapped.

js folder:
Contains all of the javascript for different pages.
The most technically dense scripts are the inventory script and the event script.

Both contain functions for http-requests to the server for creating new items / entries, saving them, or deleting them.

The event script has the function calculatePrice() which returns the amount of revenue that should have been earned from the sale of an item (and the deals that would be applied to it). It  loops through the deals for a given item and calculates the cheapest price based on the quantity sold. It can also stack deals on top of each other, in case a quantity fits within the quantities of two deals.

css folder:
Contains the css for this project.
There is only one css file, event.css. It is used to show when the user has unsaved changes to their entries by flashing the update button red / green.
I chose not to make this a css-heavy project because I really wanted to focus on functionality and keep a minimalist design that could be easily used by my team.
