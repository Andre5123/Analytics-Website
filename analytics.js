eventsContainer = document.querySelector("#events")
eventTemplate = document.querySelector("#eventTemplate")


fetch("/past-events")
    .then(response => response.json())
    .then(events => {
        var pastEvents = events["events"];
        let Items = events["items"];

        let itemCosts = {}
        for (let i =0; i < Items.length; i++) {
            const name = Items[i]["name"];
            const cost = Items[i]["cost"];
            const quantity = Items[i]["buyQuantity"];

            itemCosts[name] = cost / quantity;
        }

        for (let eventId in pastEvents) {
            event = pastEvents[eventId];
            newEventDiv = eventTemplate.cloneNode(true);
            newEventDiv.style.display = "";
            newEventDiv.querySelector("h2").innerHTML = "Event: "+event["eventStart"]
            eventsContainer.insertBefore(newEventDiv, eventTemplate.nextSibling);

            let eventRevenue = 0;
            let eventCost = 0;
            let eventProfit = 0;
            let sales = event["sales"];

            items = {}
            for (i=0; i<sales.length; i++){
                let item = sales[i]["item"];
                if (!(items[item])) {
                    items[item] = {"totalRevenue": 0, "unitsSold":0};
                }
                items[item]["unitsSold"] += sales[i]["quantity"];
                items[item]["totalRevenue"] += sales[i]["amtPaid"];
            }

            for (let item in items) {
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
                cost.innerHTML = "Cost for units sold: $"+ itemCosts[item] * items[item]["unitsSold"];
                newEventDiv.append(cost);
                eventCost += itemCosts[item] * items[item]["unitsSold"];
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
    })
    .catch(error => console.error("Error:", error));


