// inventory.js
(() => {
    // -------------------- STATE --------------------
    const state = {
        items: window.items || []
    };

    // -------------------- ELEMENTS --------------------
    const itemsContainer = document.querySelector("#items");
    const itemTemplate = itemsContainer.querySelector("#itemTemplate");
    const newItemButton = document.querySelector("#newItem");
    const newNameInput = document.querySelector("#newName");
    const newQuantityInput = document.querySelector("#newQuantity");
    const newCostInput = document.querySelector("#newCost");
    const errorMessage = document.querySelector("#errorMessage");

    // -------------------- HELPERS --------------------
    function showError(msg) {
        errorMessage.textContent = msg || "";
    }

    function validateItem(name, quantity, cost) {
        if (!name || typeof name !== "string") return "Please enter a valid name";
        if (state.items.find(i => i.name === name)) return "This item name has already been used";
        if (Number.isNaN(quantity) || quantity <= 0) return "Please enter a positive quantity";
        if (Number.isNaN(cost) || cost <= 0) return "Please enter a positive cost";
        return null;
    }

    function createItemNode(name, quantity, cost) {
        const newItem = itemTemplate.cloneNode(true);
        newItem.style.display = "";
        newItem.id = "item" + name;

        const itemNameEl = newItem.querySelector("#itemName");
        itemNameEl.textContent = name;

        return newItem;
    }

    function updateDealStats(deal) {
        const itemName = deal.closest(".item").id.replace("item", "");
        const item = state.items.find(i => i.name === itemName);
        const unitCost = item.unit_cost;

        const revenue = Number(deal.querySelector("#revenue").value);
        let quantity = Number(deal.querySelector("#quantity").value);
        quantity = quantity || 1;

        deal.querySelector("#cost").textContent = `Cost: $${(unitCost * quantity).toFixed(2)}`;
        deal.querySelector("#revenuePerItem").textContent = `Revenue per item: $${(revenue / quantity).toFixed(2)}`;
        deal.querySelector("#profitPerItem").textContent = `Profit per item: $${(revenue / quantity - unitCost).toFixed(2)}`;
        deal.querySelector("#profitPerSale").textContent = `Profit per sale: $${(revenue - unitCost * quantity).toFixed(2)}`;
    }

    function apiAddItem(item) {
        return fetch("/new-item", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(item)
        }).then(res => res.json());
    }

    function apiDeleteItem(name) {
        return fetch("/delete-item", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name})
        }).then(res => res.json());
    }

    function apiUpdateDeal(dealData) {
        return fetch("/update-deal", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(dealData)
        }).then(res => res.json());
    }

    // -------------------- EVENT LISTENERS --------------------

    // Add new item
    newItemButton.addEventListener("click", async () => {
        showError("");
        const name = newNameInput.value.trim();
        const quantity = parseInt(newQuantityInput.value);
        const cost = parseFloat(newCostInput.value);

        const validationError = validateItem(name, quantity, cost);
        if (validationError) {
            showError(validationError);
            return;
        }

        const newItemNode = createItemNode(name, quantity, cost);
        itemsContainer.insertBefore(newItemNode, itemTemplate.nextSibling);

        // Update state
        state.items.push({name, quantity, cost, unit_cost: cost / quantity});

        // Send to server
        try {
            const res = await apiAddItem({name, quantity, cost});
            if (!res.success) console.error("Error saving item:", res);
        } catch (err) {
            console.error(err);
        }
    });

    // Delete item
    itemsContainer.addEventListener("click", async (event) => {
        const target = event.target;
        if (target.id !== "deleteItem") return;

        const itemNode = target.closest(".item");
        const itemName = itemNode.id.replace("item", "");

        itemNode.remove();
        state.items = state.items.filter(i => i.name !== itemName);

        try {
            const res = await apiDeleteItem(itemName);
            if (!res.success) console.error("Error deleting item:", res);
        } catch (err) {
            console.error(err);
        }
    });

    // Add new deal
    itemsContainer.addEventListener("click", (event) => {
        const target = event.target;
        if (target.id !== "newDeal") return;

        const itemNode = target.closest(".item");
        const dealsContainer = itemNode.querySelector("#deals");
        const dealTemplate = dealsContainer.querySelector("#dealTemplate");

        const newDeal = dealTemplate.cloneNode(true);
        newDeal.id = "";
        newDeal.classList.remove("d-none");
        newDeal.classList.add("d-flex");

        dealsContainer.insertBefore(newDeal, dealTemplate.nextSibling);
    });

    // Update deal stats on input
    itemsContainer.addEventListener("input", (event) => {
        const deal = event.target.closest(".deal");
        if (!deal) return;

        const updateBtn = deal.querySelector("#update");
        updateBtn.classList.remove("saved");
        updateBtn.classList.add("unsaved");

        updateDealStats(deal);
    });

    // Save deal
    itemsContainer.addEventListener("click", async (event) => {
        event.preventDefault();
        const target = event.target;
        if (target.id !== "update") return;

        const deal = target.closest(".deal");
        if (!deal || target.classList.contains("saved")) return;

        target.classList.remove("unsaved");
        target.classList.add("saved");

        const itemName = deal.closest(".item").id.replace("item", "");
        const id = deal.id || null;
        const quantity = Number(deal.querySelector("#quantity").value);
        const revenue = Number(deal.querySelector("#revenue").value);

        try {
            const res = await apiUpdateDeal({id, item: itemName, quantity, revenue});
            if (!res.success) console.error("Error updating deal:", res);
            else if (res.dealId) deal.id = res.dealId;
        } catch (err) {
            console.error(err);
        }
    });

})();
