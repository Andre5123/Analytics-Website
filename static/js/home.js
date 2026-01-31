(() => {
    // Wrap in IIFE to avoid globals
    const CurrentEvent = window.eventActive;
    const eventButton = document.querySelector("#eventButton");
    const eventCostField = document.querySelector("#eventCost");
    const errorText = document.querySelector("#errorMessage");

    function startEvent() {
        const eventCost = Number(eventCostField.value) || 0;
        fetch("/event-status", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ eventStatus: true, cost: eventCost })
        })
        .then(res => res.json())
        .then(data => handleServerResponse(data))
        .catch(err => console.error("Error starting event:", err));
    }

    function handleServerResponse(data) {
        if (data.success) {
            // Successfully started or continued
            eventButton.value = "Continue event";
            window.location.href = "/event";
        } else {
            // Display error message
            errorText.textContent = data.error || "Unknown error";
            
            // Special case: someone else already started the event
            if (data.error === "Error: someone has already started an event") {
                eventButton.value = "Continue event";
                eventCostField.style.display = "none";
            }
        }
    }

    eventButton.addEventListener("click", () => {
        if (!CurrentEvent) {
            startEvent();
        } else {
            window.location.href = "/event";
        }
    });
})();
