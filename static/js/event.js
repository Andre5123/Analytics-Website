const newSaleButton = document.querySelector("#newSale")
const saleTemplate = document.querySelector("#sale_template")
const subscriptionTemplate = document.querySelector("#subscription_template")
const salesContainer = document.querySelector("#sales")
const subSalesContainer = document.querySelector("#subscriptionSales")
const items = window.items

const itemOptions = document.querySelector("#itemOptions")
const quantityOptions = document.querySelector("#quantityOptions")
const customRevenueOption = document.querySelector("#customRevenueToggle")
const customRevenueField = document.querySelector("#customRevField")

const paymentMethodOptions = document.querySelector("#paymentMethodOptions")

const subscriptionContainer = document.querySelector("#subscriptionOptions")
const subscriptionOptions = document.querySelector("#subscriptions")
const subscriberNameField = document.querySelector("#subscriberNameField")
const newSubscription = document.querySelector("#newSubscription")

const errorText = document.querySelector("#errorMessage")

let selectedItem = null
let selectedPaymentMethod = null
let selectedQuantity = null
let customRevenue = null
let selectedSubscription = null
let selectedSubscriber = null

// Create new sale
newSale.addEventListener("click", (event)=>{


    if (selectedItem != null && selectedPaymentMethod!=null && selectedQuantity!=null) {
        // Create new sale
        let newSale = saleTemplate.cloneNode(true);
        newSale.querySelector("#item").textContent = selectedItem;
        newSale.querySelector("#quantity").value = selectedQuantity;
        newSale.querySelector("#paymentMethod").value = selectedPaymentMethod;
        if (customRevenue != null){
            customRevenue = customRevenueField.value
            newSale.querySelector("#amtPaid").textContent = customRevenue;
            newSale.querySelector("#customAmtPaid").value = customRevenue;
        }
        else {
            let price = calculatePrice(selectedItem, selectedQuantity);
            newSale.querySelector("#amtPaid").textContent = price["price"].toFixed(2);
            let dealsApplied = price["dealsApplied"]
            let dealsAppliedCont = newSale.querySelector("#dealsApplied")

            for (let i = 0; i<dealsApplied.length; i++) {
                let p = document.createElement("p");
                timesApplied = dealsApplied[i]["quantityCovered"] / dealsApplied[i]["dealQuantity"]
                p.textContent = "("+dealsApplied[i]["dealQuantity"].toFixed(2) + " for " + dealsApplied[i]["dealPrice"]+") x " + timesApplied.toFixed(2);
                p.style.fontSize = 8;
                dealsAppliedCont.append(p);
            }
        }

        if (selectedPaymentMethod == "subscription"){
            newSale.querySelector("#subscriber").value = document.querySelector("#subscriberSelect").value
        }

        newSale.classList.remove("d-none");
        newSale.classList.add("d-flex");
        newSale.id = '';
        const date = new Date();
        newSale.querySelector("#date").textContent = date.toString();
        salesContainer.insertBefore(newSale,salesContainer.firstElementChild);

        selectedItem = null;
        selectedQuantity = null;
        selectedPaymentMethod = null;
        customRevenue = null;

        Array.from(quantityOptions.children).forEach(option => {
            option.classList.remove("selected");
        })

        Array.from(itemOptions.children).forEach(option => {
            option.classList.remove("selected");
        })
        Array.from(paymentMethodOptions.children).forEach(option => {
            option.classList.remove("selected");
        })

        customRevenueOption.classList.remove("selected");

        // Save the newly created sale
        updateSale(salesContainer.firstElementChild);
    }
})

// Select a subscription
subscriptionOptions.addEventListener("click", (event)=>{
    let sub = event.target;
    console.log(sub, "is the thing")
    
    if (sub.id.includes("Subscription")) {
        // Select the subscription
        
        selectedSubscription = parseInt(sub.textContent);

        // Add css for selecting the current option and remove from the other options
        Array.from(subscriptionOptions.children).forEach(option => {
            console.log("OK ", option);
            option.classList.remove("selected")
        })
        sub.classList.add("selected")
    }
})

// Register a subscription
newSubscription.addEventListener("click", (event)=> {
    let subscriberName = subscriberNameField.value || null
    if (subscriberName === "" || subscriberName == null){
        errorText.textContent = "Please enter the name of the subscriber"
        return
    }
    console.log("selected subscription is", selectedSubscription)
    if (selectedSubscription == null) {
        errorText.textContent = "Please select a subscription"
        return
    }

    let newSub = subscriptionTemplate.cloneNode(true);
    newSub.querySelector("#price").textContent = selectedSubscription+"$ Subscription sold to:";
    newSub.querySelector("#name").textContent = subscriberName;

    newSub.classList.remove("d-none");
    newSub.classList.add("d-flex");
    newSub.id = '';
    


    data = {
        "id":null,
        "price":selectedSubscription,
        "name":subscriberName,
    }

    fetch("/update-subscriber",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.subscriberId) { // First time saving sale, it will be assigned an ID by the server
                newSub.id = data.subscriberId;
                
                
            console.log("Sub Sale id successfully created")

            }
            console.log("Sub Sale successfully saved")
            window.location.reload();
        }
        else {
            console.log("Error, sub sale did not successfully save", data)
            errorText.textContent = "Error: "+data.error;
        }
    })
    .catch(error => console.error("Error:", error));
    subSalesContainer.insertBefore(newSub,subSalesContainer.firstElementChild.nextElementSibling);
    selectedSubscription = null;

    

    Array.from(subscriptionOptions.children).forEach(option => {
        option.classList.remove("selected");
    })

})

// Select an item
quantityOptions.addEventListener("click", (event)=>{
    let quantity = event.target;

    
    if (quantity.id.includes("Quantity")) {
        // Create new sale
        if (quantity.id === "customQuantity"){
            customQuantity = quantityOptions.querySelector("#customQtyField").value;
            selectedQuantity = customQuantity;
        }
        else {
            selectedQuantity = parseInt(quantity.textContent);
        }

        // Add css for selecting the current option and remove from the other options
        Array.from(quantityOptions.children).forEach(option => {
            console.log("OK ", option);
            option.classList.remove("selected")
        })
        quantity.classList.add("selected")
    }
})

// Update custom quantity
quantityOptions.addEventListener("input", (event)=>{
    let customQtyButton = quantityOptions.querySelector("#customQuantity")
    let quantityField = event.target;
    if (quantityField.id === "customQtyField" && customQtyButton.classList.contains("selected")){
        selectedQuantity = quantityField.value
    }
})

itemOptions.addEventListener("click", (event)=>{
    let item = event.target;

    if (item.id.includes("Item")) {
        // Create new sale
        selectedItem = item.textContent

        // Add css for selecting the current option and remove from the other options
        Array.from(itemOptions.children).forEach(option => {
            option.classList.remove("selected")
        })
        item.classList.add("selected")

    }

    
})

customRevenueOption.addEventListener("click", (event)=>{
    if (customRevenueOption.classList.contains("selected")) {
        customRevenueOption.classList.remove("selected");
        customRevenue = null;
    }
    else {
        customRevenue = customRevenueField.value;
        customRevenueOption.classList.add("selected");
    }
})

customRevenueField.addEventListener("input", (event)=>{
    if (customRevenueOption.classList.contains("selected")) {
        customRevenue = customRevenueField.value;
    }
})

paymentMethodOptions.addEventListener("click", (event)=>{
    let paymentMethod = event.target;

    if (paymentMethod.id.includes("PaymentMethod")) {
        // Create new sale
        selectedPaymentMethod = paymentMethod.textContent.toLowerCase();

        // Add css for selecting the current option and remove from the other options
        Array.from(paymentMethodOptions.children).forEach(option => {
            option.classList.remove("selected")
        })
        paymentMethod.classList.add("selected")
    }

    
})


// This function calculates the cheapest price for the sale of a quantity of an item, based on the best combination of that item's deals.
function calculatePrice(itemName, quantity) {
    let deals = window.items.find(item => item.name === itemName).deals;

    if (deals.length == 0){
        console.log("error, this item has no deals");
        return {"price": 0, "dealsApplied": []};
    }
    let price = 0;
    // Get the cost per unit for every deal
    for (let i =0; i < deals.length; i++) {
        // Deal does not apply since the deal's quantity is larger than the sale's.
        deals[i]["revenuePerItem"] = deals[i]["revenue"]/ deals[i]["quantity"]
    }

    // To keep tabs on all of the deals that are used
    let dealsApplied = []
    // Account for the entire quantity with the best deals
    while (quantity > 0) {
        let cheapestDealIndex = 0;
        for (let i=1; i<deals.length; i++) {
            // Find the cheapest deal that is within the quantity range
            if (deals[i]["revenuePerItem"] < deals[cheapestDealIndex]["revenuePerItem"] && deals[i]["quantity"] <= quantity) {
                cheapestDealIndex = i;

            }
        }
        let cheapestDeal = deals[cheapestDealIndex];
        console.log("the cheapest deal is ", cheapestDeal);
        let quantityCovered = quantity - quantity % cheapestDeal["quantity"];

        // Special case where there is no deal with a quantity smaller than or equal to the sale's quantity, should not happen.
        if (cheapestDeal["quantity"] > quantity) {
            quantityCovered = quantity;
        }
        price += quantityCovered * cheapestDeal["revenuePerItem"];
        quantity -= quantityCovered;
        dealsApplied.push({"dealQuantity": cheapestDeal["quantity"], "dealPrice": cheapestDeal["revenue"], "quantityCovered":quantityCovered})
    }
    return {"price": price, "dealsApplied": dealsApplied};
}

// Visual feedback to show that the sale has unsaved changes
salesContainer.addEventListener("input", (event)=>{
    console.log("new input");
    let sale = event.target.closest(".sale")
    if (sale) {
        updateButton = sale.querySelector("#update")
        updateButton.classList.remove("saved");
        updateButton.classList.add("unsaved");

        let amtPaid = sale.querySelector("#amtPaid");
        let customAmtPaid = sale.querySelector("#customAmtPaid");
        let itemName = sale.querySelector("#item").textContent;
        let quantity = sale.querySelector("#quantity").value;
        let price = calculatePrice(itemName, quantity);
        amtPaid.textContent = (customAmtPaid.value == "")? (price["price"]).toFixed(2): customAmtPaid.value;

        let dealsApplied = price["dealsApplied"]
        let dealsAppliedCont = sale.querySelector("#dealsApplied")
        //Erase any previous deals to reapply them
        dealsAppliedCont.innerHTML = "<h6>Deals applied:</h6>";
        if (customAmtPaid.value == "") {

            for (let i = 0; i<dealsApplied.length; i++) {
                let p = document.createElement("p");
                timesApplied = dealsApplied[i]["quantityCovered"] / dealsApplied[i]["dealQuantity"]
                p.textContent = "("+dealsApplied[i]["dealQuantity"].toFixed(2) + " for " + dealsApplied[i]["dealPrice"]+") x " + timesApplied.toFixed(2);
                p.style.fontSize = 8;
                dealsAppliedCont.append(p);
            }
        }

        //GUI visuals: Making the subscriber list visible if payment is by subscription
        let payment_method = sale.querySelector("#paymentMethod");
        console.log("about ", payment_method)
        console.log(payment_method.value)
        if (payment_method.value == "subscription"){
            console.log("change it")
            sale.querySelector("#subscriber").style.display = "inline"
            console.log(sale.querySelector("#subscriber"))
        }
        else {
            sale.querySelector("#subscriber").style.display = "none"
        }
    }
})
// Updates the server that a new sale has been added or an existing one was modified
function updateSale(sale) {
    const id = sale.id || null;
    const item = sale.querySelector("#item").textContent;
    const quantity = Number(sale.querySelector("#quantity").value);
    const amtPaid = Number(sale.querySelector("#amtPaid").textContent);
    const date = new Date(sale.querySelector("#date").textContent);
    const paymentMethod = sale.querySelector("#paymentMethod").value;


    data = {
        "id":id,
        "item":item,
        "quantity":quantity,
        "revenue":amtPaid,
        "sale_time":date,
        "payment_method":paymentMethod
    }

    if (paymentMethod == "subscription"){
        data["subscriber_id"] = sale.querySelector("#subscriber").value
    }

    fetch("/update-sale",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.saleId) { // First time saving sale, it will be assigned an ID by the server
                sale.id = data.saleId;
            console.log("Sale id successfully created")

            }
            console.log("Sale successfully saved")
            if (paymentMethod == "subscription"){
                window.location.reload();
            }
        }
        else {
            console.log("Error, sale did not successfully save", data)
            errorText.textContent = "Error: "+data.error;
            if (paymentMethod == "subscription"){
                window.location.reload();
            }
        }
    })
    .catch(error => console.error("Error:", error));
}

// Save the changes to the sale
salesContainer.addEventListener("click", (event)=>{
    event.preventDefault();
    updateButton = event.target
    sale = updateButton.closest(".sale")
    if (updateButton.id == "update" && !(updateButton.classList.contains("saved"))) {
        // Visual feedback
        updateButton.classList.remove("unsaved");
        updateButton.classList.add("saved");
        updateSale(sale);
    }
})

//To end the event
const endEvent = document.querySelector("#endEvent")

endEvent.addEventListener("click", ()=>{
    CurrentEvent = false;
    fetch("/event-status", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"eventStatus": false})
        })
        .then(response => response.json())
        .then(event => {
            if (event.success == true){
                if (CurrentEvent == false){
                    window.location.href = "/";
                }
            }
            else {
                console.log("An error occurred trying to update the server");
            }
        })
        .catch(error => console.log(error));
})



