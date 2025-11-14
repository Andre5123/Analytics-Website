const eventButton = document.querySelector("#eventButton")

// Check if an event is ongoing when loading the page
fetch("/event-status")
    .then(response => response.json())
    .then(eventStatus => {
        CurrentEvent = eventStatus.active;
        if (CurrentEvent) {
            eventButton.value = "Continue event"
        }
        else {
            eventButton.value = "Create new event"

        }
    })
    .catch(error => console.error("Error:", error));



eventButton.addEventListener("click", ()=>{
    if (CurrentEvent == false) {
        CurrentEvent = true;
        console.log("current event status:", CurrentEvent);
        fetch("/event-status", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"eventStatus": true})
        })
        .then(response => response.json())
        .then(event => {
            if (event.success == true){
                if (CurrentEvent == true){
                    eventButton.value = "Continue event";
                    window.location.href = "/event";
                }
            }
            else {
                console.log("An error occurred trying to update the server");
            }
        })
        .catch(error => console.log(error));
    }
    else {
        window.location.href = "/event";
    }
})

