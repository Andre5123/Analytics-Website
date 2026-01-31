// Get references to the container and template
const eventsContainer = document.querySelector("#events");
const eventTemplate = document.querySelector("#eventTemplate");

// Use window.events from server-side rendering
const pastEvents = window.events;

// Utility function to calculate totals per item
function processSales(sales) {
    const items = {};
    let eventRevenue = 0;
    let eventCost = 0;

    for (const sale of sales) {
        const item = sale.item;
        if (!items[item]) {
            items[item] = { totalCost: 0, totalRevenue: 0, unitsSold: 0 };
        }
        items[item].unitsSold += sale.quantity;
        items[item].totalRevenue += sale.revenue;
        items[item].totalCost += sale.cost;
    }

    for (const item in items) {
        eventRevenue += items[item].totalRevenue;
        eventCost += items[item].totalCost;
    }

    const eventProfit = eventRevenue - eventCost;
    return { items, eventRevenue, eventCost, eventProfit };
}

// Utility function to render a single event
function renderEvent(eventData) {
    const newEventDiv = eventTemplate.cloneNode(true);
    newEventDiv.style.display = "";

    // Event header
    const startDate = eventData.start_date;
    newEventDiv.querySelector("h2").textContent = `Event: ${startDate}`;

    // Process sales
    const { items, eventRevenue, eventCost, eventProfit } = processSales(eventData.sales);

    // Render each item
    for (const itemName in items) {
        const itemData = items[itemName];

        const itemHeader = document.createElement("h3");
        itemHeader.textContent = itemName;
        newEventDiv.appendChild(itemHeader);

        const revenueEl = document.createElement("p");
        revenueEl.textContent = `Total revenue from item: $${itemData.totalRevenue.toFixed(2)}`;
        newEventDiv.appendChild(revenueEl);

        const quantityEl = document.createElement("p");
        quantityEl.textContent = `Total units sold: ${itemData.unitsSold}`;
        newEventDiv.appendChild(quantityEl);

        const costEl = document.createElement("p");
        costEl.textContent = `Total cost from item: $${itemData.totalCost.toFixed(2)}`;
        newEventDiv.appendChild(costEl);
    }

    // Render event totals
    newEventDiv.querySelector("#totalRevenue").textContent = `Total Revenue: $${eventRevenue.toFixed(2)}`;
    newEventDiv.querySelector("#totalProfit").textContent = `Total Profit: $${eventProfit.toFixed(2)}`;
    newEventDiv.querySelector("#totalCost").textContent = `Total Cost: $${eventCost.toFixed(2)}`;

    eventsContainer.appendChild(newEventDiv);
}

// Render all events
for (const eventData of pastEvents) {
    renderEvent(eventData);
}
