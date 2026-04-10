async function getRandom() {
    var response = await fetch(API_ENDPOINTS.random)
    if (response.ok) {
        var sku = await response.json()
        window.location.href = `/manga/${sku}`
    } else {
        new Error(
            `Ошибка ${response.status}: ${response.statusText}`
        )
    }
}

const randomButton = document.getElementById('random') as HTMLButtonElement
console.log(randomButton);

if (randomButton) {
    randomButton.onclick = getRandom
}