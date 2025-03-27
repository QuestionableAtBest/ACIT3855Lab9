/* UPDATE THESE VALUES TO MATCH YOUR SETUP */
const PROCESSING_STATS_API_URL = "http://microservices-acit3855-harry.westus2.cloudapp.azure.com/processing/stats"
const ANALYZER_API_URL = {
    stats: "http://microservices-acit3855-harry.westus2.cloudapp.azure.com/analyzer/stats",
    watch: "http://microservices-acit3855-harry.westus2.cloudapp.azure.com/analyzer/scale?index=",
    scale: "http://microservices-acit3855-harry.westus2.cloudapp.azure.com/analyzer/watch?index="
}

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            console.log("Received data: ", result)
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

const updateCodeDiv = (result, elemId) => document.getElementById(elemId).innerText = JSON.stringify(result)

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()
    makeReq(PROCESSING_STATS_API_URL, (result) => updateCodeDiv(result, "processing-stats"))
    makeReq(ANALYZER_API_URL.stats, (result) => {
        updateCodeDiv(result, "analyzer-stats")
        randWatch = ANALYZER_API_URL.watch + String(Math.floor(Math.random()*result["num_w"]))
        randScale = ANALYZER_API_URL.scale + String(Math.floor(Math.random()*result["num_s"]))
        makeReq(randWatch, (result) => updateCodeDiv(result, "event-watch"))
        makeReq(randScale, (result) => updateCodeDiv(result, "event-scale"))
        makeReq("http://microservices-acit3855-harry.westus2.cloudapp.azure.com/consistency_check/checks", (result) => updateCodeDiv(result, "event-consistency"))
    })
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds
}

document.addEventListener('DOMContentLoaded', setup)