

const newName = document.querySelector("#newName")
const newQuantity = document.querySelector("#newQuantity")
const newCost = document.querySelector("#newCost")
const errorMessage = document.querySelector("#errorMessage")
const itemsContainer = document.querySelector("#items")
const itemTemplate = itemsContainer.querySelector("#itemTemplate")

newItemButton = document.querySelector("#newItem")
// Add new item
newItemButton.addEventListener("click", ()=>{
    // Client side validation
    console.log(newName.value, newQuantity.value);
    let name = newName.value;
    quantity = parseInt(newQuantity.value)
    cost = parseFloat(newCost.value)
    errorMessage.innerHTML = "";

    if (typeof(name) !== "string" || name==="") {
        errorMessage.innerHTML = "Please enter a valid name";
        return;
    }
    else if (itemsContainer.querySelector("#item"+name)) {
        errorMessage.innerHTML = "This item name has already been used";
        return;
    }
    else if (newQuantity.value === "" || newQuantity.value <= 0 || newCost.value === "") {
        errorMessage.innerHTML = "Please enter a valid quantity and cost";
        return;
    }
    if(Number.isNaN(quantity) || quantity <=0) {
        errorMessage.innerHTML = "Please enter a positive quantity"
        return;
    }
    if(Number.isNaN(cost) || cost <=0) {
        errorMessage.innerHTML = "Please enter a positive cost"
        return;
    }
    newItem = itemTemplate.cloneNode(true);
    newItem.style.display = '';
    newItem.id = "item"+name;
    itemName = newItem.querySelector("#itemName")
    itemName.innerHTML = name;

    itemsContainer.insertBefore(newItem, itemTemplate.nextSibling);

    data = {
        "name": name,
        "quantity": quantity,
        "cost": cost
    }
    window.items.push({"name":name, "quantity":quantity, "cost":cost, "unit_cost":cost/quantity})
    // Update the server that a new item has been added
    fetch("/new-item",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Item successfully registered in server")
        }
        else {
            console.log("Error, item did not successfully save")
        }
    })

})

// Delete an item
function deleteItem(item) {
    let itemName = item.closest(".item").id
    itemName = itemName.replace("item", "")

    data = {
        "name":itemName,
    }
    //Delete the item in html
    item.remove();

    // Send a request to the server to delete the item from the database
    fetch("/delete-item",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        if (data.success) {
            console.log("Item successfully deleted")

        }
        else {
            console.log("Error, item did not successfully delete")
        }
    })
    .catch(error => console.error("Error:", error));

    // Delete the item's entry in this script
    window.items = window.items.filter(item => item.name != itemName)
}

// Delete an item
itemsContainer.addEventListener("click", (event) => {
    delButton = event.target;
    if (!(delButton.id ==="deleteItem")) return;
    item = delButton.closest(".item");
    if (item) {
        deleteItem(item);
    }
})


// ----- Deals on items ------

// Add new deal
itemsContainer.addEventListener("click", (event) => {

    newDealButton = event.target
    if (!(newDealButton.id === "newDeal")) return;

    item = newDealButton.closest(".item")
    if (!item) return;

    dealsContainer = item.querySelector("#deals")
    dealTemplate = dealsContainer.querySelector("#dealTemplate")
    newDeal = dealTemplate.cloneNode(true);
    // The deal will be given a unique generated id from the server later
    newDeal.id = "";
    newDeal.classList.remove("d-none");
    newDeal.classList.add("d-flex");
    dealsContainer.insertBefore(newDeal, dealTemplate.nextSibling);
})

function updateDeal(deal) {
    const id = deal.id || null;
    let itemName = deal.closest(".item").id
    itemName = itemName.replace("item", "")
    const quantity = Number(deal.querySelector("#quantity").value);
    const revenue = Number(deal.querySelector("#revenue").value);


    data = {
        "id":id,
        "item":itemName,
        "quantity":quantity,
        "revenue":revenue,
    }

    fetch("/update-deal",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        if (data.success) {
            if (data.dealId) { // First time saving sale, it will be assigned an ID by the server
                deal.id = data.dealId;
            console.log("Deal id successfully created")

            }
            console.log("Deal successfully saved")
        }
        else {
            console.log("Error, deal did not successfully save")
        }
    })
    .catch(error => console.error("Error:", error));
}


// Save the item deal to the server when update button is clicked
itemsContainer.addEventListener("click", (event)=>{
    event.preventDefault();
    updateButton = event.target
    deal = updateButton.closest(".deal")
    if (updateButton.id == "update" && !(updateButton.classList.contains("saved"))) {
        // Visual feedback
        updateButton.classList.remove("unsaved");
        updateButton.classList.add("saved");
        updateDeal(deal);
    }
})

// Visual feedback to show that the deal has unsaved changes
itemsContainer.addEventListener("input", (event)=>{
    deal = event.target.closest(".deal")
    if (deal) {
        updateButton = deal.querySelector("#update")
        updateButton.classList.remove("saved");
        updateButton.classList.add("unsaved");
        const itemName = deal.closest(".item").id.replace("item", "");
        const costPerItem = window.items.find(item => item.name === itemName)["unit_cost"];
        const revenuePerItem = deal.querySelector("#revenuePerItem");
        const profitPerItem = deal.querySelector("#profitPerItem");
        const profitPerSale = deal.querySelector("#profitPerSale");
        const cost = deal.querySelector("#cost")
        const revenue = deal.querySelector("#revenue").value
        let quantity = deal.querySelector("#quantity").value
        quantity = (quantity === "" || quantity===0)? 1 : quantity;

        cost.innerHTML = "Cost: $"+(costPerItem*quantity).toFixed(2);
        revenuePerItem.innerHTML = "Revenue per item: $"+(revenue/quantity).toFixed(2);
        profitPerItem.innerHTML = "Profit per item: $"+(revenue/quantity - costPerItem).toFixed(2);
        profitPerSale.innerHTML = "Profit per sale: $"+(revenue - costPerItem*quantity).toFixed(2);

    }
})
