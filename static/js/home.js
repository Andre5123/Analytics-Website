
// When the page loads, the server passes a bool through Jinja for if an event is currently active
let CurrentEvent = window.eventActive;

const eventButton = document.querySelector("#eventButton");
const selectMenu = document.querySelector("#selectMenu");
const eventCost = document.querySelector("#eventCost");
console.log(CurrentEvent, "event active?")



eventButton.addEventListener("click", ()=>{
    console.log(eventCost.value)
    if (CurrentEvent == false) {
        CurrentEvent = true;
        console.log("current event status:", CurrentEvent);
        fetch("/event-status", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"eventStatus": true, "cost": parseFloat(eventCost.value) || 0, "menu_id":parseInt(selectMenu.value)})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success == true){
                if (CurrentEvent == true){
                    eventButton.value = "Continue event";
                    window.location.href = "/event";
                }
            }
            else {
                errorText = document.querySelector("#errorMessage");
                errorText.innerHTML = data.error;

                if (data.error === "Error: someone has already started an event") {
                    eventButton.value = "Continue event";
                    eventButton.style.display="block";
                    eventCost.style.display = "none";
                }
                console.log("An error occurred trying to update the server", data.error);
            }
        })
        .catch(error => console.log(error));
    }
    else {
        window.location.href = "/event";
    }
})

