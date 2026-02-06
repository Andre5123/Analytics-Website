eventsContainer = document.querySelector("#events")
eventTemplate = document.querySelector("#eventTemplate")


var pastEvents = window.events;


for (const event of pastEvents) {
    newEventDiv = eventTemplate.cloneNode(true);
    newEventDiv.style.display = "";
    newEventDiv.querySelector("h2").innerHTML = "Event: "+event["start_date"]
    eventsContainer.appendChild(newEventDiv, eventTemplate.nextSibling);

    let eventRevenue = 0;
    let totalSalesCost = 0;
    let eventProfit = 0;
    let sales = event["sales"];
    

    let items = {}
    for (let i=0; i<sales.length; i++){
        let item = sales[i]["item"];
        if (!(items[item])) {
            items[item] = {"totalCost": 0, "totalRevenue": 0, "unitsSold":0};
        }
        items[item]["unitsSold"] += sales[i]["quantity"];
        items[item]["totalRevenue"] += sales[i]["revenue"];
        items[item]["totalCost"] += sales[i]["cost"];
    }

    for (let item in items) {
        let itemTag = document.createElement("h3");
        itemTag.innerHTML = item;
        newEventDiv.append(itemTag);

        let revenue = document.createElement("p");
        revenue.innerHTML = "Total revenue from item: $"+items[item]["totalRevenue"];
        newEventDiv.append(revenue);
        eventRevenue += items[item]["totalRevenue"];

        let quantity = document.createElement("p");
        quantity.innerHTML = "Total units sold: "+items[item]["unitsSold"];
        newEventDiv.append(quantity);

        let cost = document.createElement("p");
        cost.innerHTML = "Total cost from item: $"+ items[item]["totalCost"];
        newEventDiv.append(cost);
        totalSalesCost += items[item]["totalCost"];
    }

    let eventCost = event["cost"]
    eventProfit = eventRevenue - Math.max(eventCost, totalSalesCost);

    // Display the event totals
    const totalRevenueHeader = newEventDiv.querySelector("#totalRevenue")
    const totalProfitHeader = newEventDiv.querySelector("#totalProfit")
    const eventCostHeader = newEventDiv.querySelector("#eventCost")
    const totalSalesCostHeader = newEventDiv.querySelector("#totalSalesCost")
    const menuHeader = newEventDiv.querySelector("#menu")
    totalRevenueHeader.textContent = "Total Revenue: $"+eventRevenue.toFixed(2);
    totalProfitHeader.textContent = "Total Profit: $"+eventProfit.toFixed(2);
    eventCostHeader.textContent = "Event Cost: $"+eventCost.toFixed(2);
    totalSalesCostHeader.textContent = "Total Sales Cost: $"+totalSalesCost.toFixed(2);
    menuHeader.textContent = "Menu: "+event["menu_name"]
}

