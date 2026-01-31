const EventPage = (() => {
    const items = window.items || [];
    const cashContainer = document.querySelector("#cash-sales");
    const tapContainer = document.querySelector("#tap-sales");
    const itemOptions = document.querySelectorAll(".item-option");
    const cashNewSaleBtn = document.querySelector("#cash-new-sale");
    const tapNewSaleBtn = document.querySelector("#tap-new-sale");
    const errorText = document.querySelector("#errorMessage");

    let cashSaleStack = [];
    let tapSaleStack = [];
    let currentCashSale = null;
    let currentTapSale = null;

    // --- Sale Creation ---
    function createSale(paymentMethod, insertBefore = null) {
        const sale = { id: null, items: {}, customRevenue: null, paymentMethod };

        const saleEl = document.createElement("div");
        saleEl.classList.add("sale-panel", "d-flex");
        saleEl.dataset.saleId = "";

        // Header
        const header = document.createElement("div");
        header.classList.add("sale-header");

        const checkboxLabel = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.classList.add("customRevenueToggle");
        checkboxLabel.appendChild(checkbox);
        checkboxLabel.appendChild(document.createTextNode(" Custom Revenue"));

        const customInput = document.createElement("input");
        customInput.type = "number";
        customInput.classList.add("customRevenueInput", "d-none");
        customInput.placeholder = "Custom revenue";

        const totalSpan = document.createElement("span");
        totalSpan.classList.add("sale-total");
        totalSpan.textContent = "Total: $0.00";

        header.appendChild(checkboxLabel);
        header.appendChild(customInput);
        header.appendChild(totalSpan);
        saleEl.appendChild(header);

        // Items container
        const itemsList = document.createElement("div");
        itemsList.classList.add("sale-items-list");
        saleEl.appendChild(itemsList);

        const container = paymentMethod === "tap" ? tapContainer : cashContainer;
        container.insertBefore(saleEl, insertBefore || container.firstElementChild);

        const currentSale = { ...sale, element: saleEl };

        if (paymentMethod === "tap") {
            currentTapSale = currentSale;
            tapSaleStack.push(currentTapSale);
        } else {
            currentCashSale = currentSale;
            cashSaleStack.push(currentCashSale);
        }

        setupHeaderEvents(currentSale);
        return currentSale;
    }

    function setupHeaderEvents(sale) {
        const checkbox = sale.element.querySelector(".customRevenueToggle");
        const customInput = sale.element.querySelector(".customRevenueInput");

        checkbox.addEventListener("change", () => {
            if (checkbox.checked) {
                customInput.classList.remove("d-none");
                sale.customRevenue = parseFloat(customInput.value) || 0;
            } else {
                customInput.classList.add("d-none");
                sale.customRevenue = null;
            }
            recalcSale(sale);
            saveSale(sale);
        });

        customInput.addEventListener("input", () => {
            sale.customRevenue = parseFloat(customInput.value) || null;
            recalcSale(sale);
            saveSale(sale);
        });
    }

    // --- Divider Logic ---
    function handleNewSaleButton(paymentMethod) {
        const container = paymentMethod === "tap" ? tapContainer : cashContainer;
        if (!container.querySelector(".sale-divider")) {
            const hr = document.createElement("hr");
            hr.classList.add("sale-divider");
            container.insertBefore(hr, container.firstElementChild);
        }
    }

    // --- Add/Update Item ---
    function addItemToSale(itemName, paymentMethod) {
        const container = paymentMethod === "tap" ? tapContainer : cashContainer;
        const topDivider = container.querySelector(".sale-divider");

        let currentSale = paymentMethod === "tap" ? currentTapSale : currentCashSale;

        // Create a new sale if no current sale or there's a divider at the top
        if (!currentSale || (topDivider && container.firstElementChild !== currentSale.element)) {
            currentSale = createSale(paymentMethod, topDivider || null);
        }

        if (!currentSale.items[itemName]) {
            currentSale.items[itemName] = { quantity: 1, revenue: 0, dealsApplied: [] };
            createItemElement(currentSale, itemName);
        } else {
            currentSale.items[itemName].quantity++;
            const inputEl = currentSale.element.querySelector(`.sale-item[data-item="${itemName}"] .item-quantity`);
            inputEl.value = currentSale.items[itemName].quantity;
        }

        recalcSale(currentSale);
        saveSale(currentSale);

        if (paymentMethod === "tap") currentTapSale = currentSale;
        else currentCashSale = currentSale;
    }

    // --- Create Item Element ---
    function createItemElement(sale, itemName) {
        const itemsList = sale.element.querySelector(".sale-items-list");

        const itemDiv = document.createElement("div");
        itemDiv.classList.add("sale-item");
        itemDiv.dataset.item = itemName;

        const nameSpan = document.createElement("span");
        nameSpan.classList.add("item-name");
        nameSpan.textContent = itemName;

        const quantityInput = document.createElement("input");
        quantityInput.type = "number";
        quantityInput.classList.add("item-quantity");
        quantityInput.value = 1;
        quantityInput.min = 0; // prevent past sales from dropping below 1

        const costSpan = document.createElement("span");
        costSpan.classList.add("item-cost");
        costSpan.textContent = "Cost: $0.00";

        const revenueSpan = document.createElement("span");
        revenueSpan.classList.add("item-revenue");
        revenueSpan.textContent = "Revenue: $0.00";

        quantityInput.addEventListener("input", () => {
            let val = parseInt(quantityInput.value);
            if (Number.isNaN(val)) val = 0;

            const isCurrentSale =
                (sale.paymentMethod === "tap" && sale === currentTapSale) ||
                (sale.paymentMethod === "cash" && sale === currentCashSale);

            if (val <= 0) {
                if (isCurrentSale) {
                    // ✅ allowed: delete item
                    delete sale.items[itemName];
                    itemDiv.remove();

                    if (Object.keys(sale.items).length === 0) {
                        deleteSale(sale);
                        return;
                    }
                } else {
                    // ❌ past sale: clamp to 1
                    quantityInput.value = 1;
                    sale.items[itemName].quantity = 1;
                }
            } else {
                sale.items[itemName].quantity = val;
            }

            recalcSale(sale);
            saveSale(sale);
        });

        itemDiv.appendChild(nameSpan);
        itemDiv.appendChild(quantityInput);
        itemDiv.appendChild(costSpan);
        itemDiv.appendChild(revenueSpan);
        itemsList.appendChild(itemDiv);
    }

    // --- Price Calculation ---
    function calculatePrice(itemName, quantity) {
        const deals = items.find(i => i.name === itemName)?.deals || [];
        if (deals.length === 0) return { price: 0, dealsApplied: [] };

        deals.forEach(d => d.revenuePerItem = d.revenue / d.quantity);

        const dealsApplied = [];
        let price = 0;

        while (quantity > 0) {
            let cheapest = deals.filter(d => d.quantity <= quantity)
                                .sort((a, b) => a.revenuePerItem - b.revenuePerItem)[0] || deals[0];

            let quantityCovered = Math.min(quantity, cheapest.quantity);
            price += quantityCovered * cheapest.revenuePerItem;
            quantity -= quantityCovered;

            dealsApplied.push({ dealQuantity: cheapest.quantity, dealPrice: cheapest.revenue, quantityCovered });
        }

        return { price, dealsApplied };
    }

    // --- Recalculate Sale ---
    function recalcSale(sale) {
        let total = 0;

        Object.entries(sale.items).forEach(([name, data]) => {
            if (!sale.customRevenue) {
                const priceObj = calculatePrice(name, data.quantity);
                data.revenue = priceObj.price;
                data.dealsApplied = priceObj.dealsApplied;

                const itemDiv = sale.element.querySelector(`.sale-item[data-item="${name}"]`);
                itemDiv.querySelector(".item-name").textContent = name;
                itemDiv.querySelector(".item-cost").textContent = `Cost: $${(data.quantity * (items.find(i => i.name === name).unit_cost)).toFixed(2)}`;
                itemDiv.querySelector(".item-revenue").textContent = `Revenue: $${data.revenue.toFixed(2)}`;

                total += data.revenue;
            }
        });

        if (sale.customRevenue) total = sale.customRevenue;
        sale.element.querySelector(".sale-total").textContent = `Total: $${total.toFixed(2)}`;
    }

    // --- Delete Sale ---
    function deleteSale(sale) {
        sale.element.remove();

        if (sale.id) {
            fetch("/delete-sale", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: sale.id })
            }).then(r => r.json())
              .then(res => {
                  if (!res.success) console.error("Failed to delete sale:", res.error);
              })
              .catch(e => console.error(e));
        }

        if (sale.paymentMethod === "tap") {
            tapSaleStack = tapSaleStack.filter(s => s !== sale);
            currentTapSale = tapSaleStack[tapSaleStack.length - 1] || null;
        } else {
            cashSaleStack = cashSaleStack.filter(s => s !== sale);
            currentCashSale = cashSaleStack[cashSaleStack.length - 1] || null;
        }
    }

    // --- Save Sale ---
    function saveSale(sale) {
        const data = {
            id: sale.id || null,
            payment_method: sale.paymentMethod,
            items: Object.entries(sale.items).map(([name, i]) => ({
                item: name,
                quantity: i.quantity,
                revenue: i.revenue,
                dealsApplied: i.dealsApplied
            })),
            customRevenue: sale.customRevenue,
        };

        if (!sale.id) {
            data.sale_time = new Date();
        }

        fetch("/update-sale", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                // If the server assigned a new sale id, store it
                if (res.saleId) {
                    sale.id = res.saleId;
                    sale.element.dataset.saleId = res.saleId; // optional: keep HTML synced
                }
            } else {
                errorText.textContent = "Error: " + (res.error || "Unknown error");
            }
        })
        .catch(e => console.error(e));
    }


    // --- Event Listeners ---
    itemOptions.forEach(btn => {
        btn.addEventListener("click", () => {
            const method = btn.classList.contains("tap-option") ? "tap" : "cash";
            addItemToSale(btn.textContent, method);
        });
    });

    cashNewSaleBtn.addEventListener("click", () => handleNewSaleButton("cash"));
    tapNewSaleBtn.addEventListener("click", () => handleNewSaleButton("tap"));

    function hydratePreviousSales(prevSales, paymentMethod) {
        if (!Array.isArray(prevSales) || prevSales.length === 0) return;

        // Oldest first so newest ends up as "current"
        prevSales.slice().reverse().forEach((saleData, index) => {
            const sale = createSale(paymentMethod);
            sale.id = saleData.id;
            sale.element.dataset.saleId = saleData.id;
            sale.paymentMethod = paymentMethod;

            // Hydrate items
            saleData.items.forEach(i => {
                sale.items[i.item] = {
                    quantity: i.quantity,
                    revenue: i.revenue,
                    dealsApplied: [] // we don't need historical deal reconstruction
                };

                createItemElement(sale, i.item);

                const itemEl = sale.element.querySelector(
                    `.sale-item[data-item="${i.item}"]`
                );
                itemEl.querySelector(".item-quantity").value = i.quantity;
            });

            // Respect stored totals (don’t auto-recalc yet)
            sale.element.querySelector(".sale-total").textContent =
                `Total: $${saleData.total_revenue.toFixed(2)}`;

            // Track stacks + current sale
            if (paymentMethod === "tap") {
                tapSaleStack.push(sale);
                currentTapSale = sale; // last one wins
            } else {
                cashSaleStack.push(sale);
                currentCashSale = sale;
            }
        });
    }


    hydratePreviousSales(prevCashSales, "cash");
    hydratePreviousSales(prevTapSales, "tap");



})();
