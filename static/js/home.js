
// When the page loads, the server passes a bool through Jinja for if an event is currently active
let CurrentEvent = window.eventActive;

const eventButton = document.querySelector("#eventButton");

console.log(CurrentEvent, "event active?")



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

