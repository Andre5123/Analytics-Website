const errorMessage = document.querySelector("#errorMessage")

const menus = document.querySelector("#menus")

const newMenu = document.querySelector("#newMenu")
const newMenuButton = document.querySelector("#newMenuButton")
// Add new item

Array.from(menus.children).forEach(menu => {
    let data = {
        "id": (menu.id == "")? null: menu.id,
        "name": menu.textContent
    }
    menu.addEventListener("click", ()=>{
        fetch("/inventory",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Successfully redirected");
                if (data.redirect){
                    window.location.href = data.redirect;
                }
            }
            else {
                errorMessage.textContent = data.error;
                console.log("Error, could not redirect");
            }
        })
    })
    
})

newMenuButton.addEventListener("click", ()=>{
    let data = {
        "id": null,
        "name": (newMenu.value=="")? null: newMenu.value,
    }
    fetch("/inventory",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.redirect){
                window.location.href = data.redirect;
            }
            console.log("Successfully created menu")
        }
        else {
            errorMessage.textContent = data.error;       
            console.log("Error, could not create menu")
        }
    })
})

const subscriptions = document.querySelector("#subscriptions")

const newSubscriptionPrice = document.querySelector("#subscriptionPrice")
const newSubscriptionBalance = document.querySelector("#subscriptionBalance")
const newSubscriptionButton = document.querySelector("#newSubscriptionButton")

const subscriptionsContainer = document.querySelector("#subscriptions")
const subscriptionTemplate = document.querySelector("#subscriptionTemplate")


newSubscriptionButton.addEventListener("click", ()=>{
    let subData = {
        "price": parseFloat(newSubscriptionPrice.value),
        "balance": parseFloat(newSubscriptionBalance.value),
    }
    fetch("/new-subscription",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(subData)
        })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            newSub = subscriptionTemplate.cloneNode(true);
            newSub.style.display = "block";
            newSub.querySelector("#price").textContent = subData["price"]+"$ Subscription";
            newSub.querySelector("#balance").textContent = subData["balance"]+"$ Balance";
            newSub.id = data.subscriptionId;
            subscriptionsContainer.prepend(newSub);
            console.log("Successfully created subscription");
        }
        else {
            errorMessage.textContent = data.error;       
            console.log("Error, could not create subscription")
        }
    })
})