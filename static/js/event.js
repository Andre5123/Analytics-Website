const newSaleButton = document.querySelector("#newSale")
const saleTemplate = document.querySelector("#sale_template")

const salesContainer = document.querySelector("#sales")

const items = window.items

const itemOptions = document.querySelector("#itemOptions")
const errorText = document.querySelector("#errorMessage")


// Create new sale
itemOptions.addEventListener("click", (event)=>{
    item = event.target

    if (item.id.includes("Item")) {
        // Create new sale
        newSale = saleTemplate.cloneNode(true);
        newSale.querySelector("#item").textContent = item.textContent
        newSale.classList.remove("d-none");
        newSale.classList.add("d-flex");
        newSale.id = '';
        const date = new Date();
        newSale.querySelector("#date").textContent = date.toString();
        salesContainer.insertBefore(newSale,salesContainer.firstElementChild);
    }
})

// This function calculates the cheapest price for the sale of a quantity of an item, based on the best combination of that item's deals.
function calculatePrice(itemName, quantity) {
    deals = window.items.find(item => item.name === itemName).deals;

    if (deals.length == 0){
        console.log("error, this item has no deals");
        return {"price": 0, "dealsApplied": []};
    }
    price = 0;
    // Get the cost per unit for every deal
    for (let i =0; i < deals.length; i++) {
        // Deal does not apply since the deal's quantity is larger than the sale's.
        deals[i]["revenuePerItem"] = deals[i]["revenue"]/ deals[i]["quantity"]
    }

    // To keep tabs on all of the deals that are used
    dealsApplied = []
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
    sale = event.target.closest(".sale")
    if (sale) {
        updateButton = sale.querySelector("#update")
        updateButton.classList.remove("saved");
        updateButton.classList.add("unsaved");

        let amtPaid = sale.querySelector("#amtPaid");
        let customAmtPaid = sale.querySelector("#customAmtPaid");
        let itemName = sale.querySelector("#item").textContent;
        let quantity = sale.querySelector("#quantity").value;
        price = calculatePrice(itemName, quantity);
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
        }
        else {
            console.log("Error, sale did not successfully save", data)
            errorText.textContent = "Error: "+data.error;
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



