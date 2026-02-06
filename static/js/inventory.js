const errorMessage = document.querySelector("#errorMessage")

const menus = document.querySelector("#menus")

const newMenu = document.querySelector("#newMenu")
const newMenuButton = document.querySelector("#newMenuButton")
// Add new item

Array.from(menus.children).forEach(menu => {
    let data = {
        "id": (menu.id == "")? null: menu.id,
        "name": menu.textContent
    }
    menu.addEventListener("click", ()=>{
        fetch("/inventory",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Successfully redirected");
                if (data.redirect){
                    window.location.href = data.redirect;
                }
            }
            else {
                errorMessage.textContent = data.error;
                console.log("Error, could not redirect");
            }
        })
    })
    
})

newMenuButton.addEventListener("click", ()=>{
    let data = {
        "id": null,
        "name": (newMenu.value=="")? null: newMenu.value,
    }
    fetch("/inventory",{
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.redirect){
                window.location.href = data.redirect;
            }
            console.log("Successfully created menu")
        }
        else {
            errorMessage.textContent = data.error;       
            console.log("Error, could not create menu")
        }
    })
})
