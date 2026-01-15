eventsContainer = document.querySelector("#events")
eventTemplate = document.querySelector("#eventTemplate")


var pastEvents = window.events;


for (let i in pastEvents) {
    newEventDiv = eventTemplate.cloneNode(true);
    newEventDiv.style.display = "";
    newEventDiv.querySelector("h2").innerHTML = "Event: "+events[i]["start_date"]
    eventsContainer.appendChild(newEventDiv, eventTemplate.nextSibling);

    let eventRevenue = 0;
    let eventCost = 0;
    let eventProfit = 0;
    let sales = events[i]["sales"];
    

    items = {}
    for (i=0; i<sales.length; i++){
        let item = sales[i]["item"];
        if (!(items[item])) {
            items[item] = {"totalCost": 0, "totalRevenue": 0, "unitsSold":0};
        }
        items[item]["unitsSold"] += sales[i]["quantity"];
        items[item]["totalRevenue"] += sales[i]["revenue"];
        items[item]["totalCost"] += sales[i]["cost"];
    }

    for (item in items) {
        itemTag = document.createElement("h3");
        itemTag.innerHTML = item;
        newEventDiv.append(itemTag);

        revenue = document.createElement("p");
        revenue.innerHTML = "Total revenue from item: $"+items[item]["totalRevenue"];
        newEventDiv.append(revenue);
        eventRevenue += items[item]["totalRevenue"];

        quantity = document.createElement("p");
        quantity.innerHTML = "Total units sold: "+items[item]["unitsSold"];
        newEventDiv.append(quantity);

        cost = document.createElement("p");
        cost.innerHTML = "Total cost from item: $"+ items[item]["totalCost"];
        newEventDiv.append(cost);
        eventCost += items[item]["totalCost"];
    }

    eventProfit = eventRevenue - eventCost;

    // Display the event totals
    const totalRevenueHeader = newEventDiv.querySelector("#totalRevenue")
    const totalProfitHeader = newEventDiv.querySelector("#totalProfit")
    const totalCostHeader = newEventDiv.querySelector("#totalCost")
    totalRevenueHeader.textContent = "Total Revenue: $"+eventRevenue.toFixed(2);
    totalProfitHeader.textContent = "Total Profit: $"+eventProfit.toFixed(2);
    totalCostHeader.textContent = "Total Cost: $"+eventCost.toFixed(2);
}

