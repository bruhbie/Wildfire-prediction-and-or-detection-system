let map;
let userMarker;
let latitude;
let longitude;
let selectedLanguage = 'en'; //default language
let fireMarkers = [];
let fireRiskLevels = ["<strong>Low</strong> fire risk level", "<strong>Medium</strong> fire risk level", "<strong>High</strong> fire risk level"];
let currentRiskIndex = 0;


function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, (error) => {
            alert("Error getting location: " + error.message);
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

function showPosition(position) {
    const userLat = position.coords.latitude;
    const userLon = position.coords.longitude;
    console.log("Latitude:", userLat, "Longitude:", userLon);
    document.getElementById("user-lat").value = userLat;
    document.getElementById("user-lon").value = userLon;
    initMap(userLat, userLon);
    fetchFireRisk(userLat, userLon);
    document.getElementById('weather-and-fire-info').style.display = 'block';
}

function showError(error) {
    alert("Error getting location: " + error.message);
}


function initMap(lat, lon) {
    if (isNaN(lat) || isNaN(lon)) {
        console.error("Invalid latitude or longitude:", lat, lon);
        return;
    }

    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: lat, lng: lon },
        zoom: 15,
    });

    new google.maps.Marker({
        position: { lat: lat, lng: lon },
        map: map,
        title: "You are here!",
    });
}


function fetchWeatherAndFireRisk(latitude, longitude) {
    document.getElementById('weather-details').innerText = "Fetching weather data...";
    document.getElementById('fire-risk').innerText = "Fetching fire risk...";

    fetch(`https://api.weather.gov/points/<span class="math-inline">\{latitude\},</span>{longitude}`)
        .then(response => response.json())
        .then(pointsData => {
            console.log("NOAA Points Data:", pointsData); // Debugging
            const forecastUrl = pointsData.properties.forecastHourly;
            return fetch(forecastUrl);
        })
        .then(response => response.json())
        .then(forecastData => {
            console.log("NOAA Forecast Data:", forecastData); // Debugging
            const period = forecastData.properties.periods[0];
            const temp = period.temperature;
            const windSpeed = parseInt(period.windSpeed);
            document.getElementById('weather-details').innerText = `🌡️ Temperature: ${temp}°F, 💨 Wind: ${windSpeed} mph`;
            return fetch('/calculate_fire_risk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ temperature: temp, wind_speed: windSpeed }),
            });
        })
        .then(response => response.json())
        .then(fireRiskData => {
            console.log("Fire Risk Data:", fireRiskData); // Debugging
            document.getElementById('fire-risk').innerText = `🔥 Fire Risk Level: ${fireRiskData.fire_risk}`;
            if (fireRiskData.show_popup) {
                showPopup('alert-popup');
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
            document.getElementById('weather-details').innerText = "❌ Failed to load weather data";
            document.getElementById('fire-risk').innerText = "❌ Failed to load fire risk data";
        });
}


function showPopup(popupId) {
    document.getElementById(popupId).style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
}

function hidePopup(popupId) {
    document.getElementById(popupId).style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}


function fetchActiveFires(latitude, longitude) {
    const current_date = new Date().toISOString().split('T')[0];
    fetch(`https://firms.modaps.eosdis.nasa.gov/api/active_fire/viirs/?api_key=YOUR_API_KEY&start_date=<span class="math-inline">\{current\_date\}&end\_date\=</span>{current_date}&lat=<span class="math-inline">\{latitude\}&lon\=</span>{longitude}&radius=100`)
        .then(response => response.json())
        .then(fires => {
            displayActiveFiresOnMap(fires.features);
        })
        .catch(error => console.error("Error fetching active fires: ", error));
}


function displayActiveFiresOnMap(fires) {
    if (!map) return;
    fires.forEach(fire => {
        const lat = fire.geometry.coordinates[1];
        const lng = fire.geometry.coordinates[0];
        new google.maps.Marker({
            position: { lat: lat, lng: lng },
            map: map,
            title: `Active Fire (${lat}, ${lng})`,
        });
    });
}


function fetchFireRisk(latitude, longitude) {
    document.getElementById('fire-risk').innerText = "Fetching fire confidence data...";

    fetch('/calculate_fire_risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: latitude, longitude: longitude }),
    })
    .then(response => response.json())
    .then(fireData => {
        console.log("Fire Confidence Data:", fireData);
        if (fireData.confidence_levels && fireData.confidence_levels.length > 0) {
            document.getElementById('fire-risk').innerText = `🔥 Fire Confidence Levels: ${fireData.confidence_levels.join(', ')}`;
        } else {
            document.getElementById('fire-risk').innerText = "⚠️ No fire confidence data available.";
        }
    })
    .catch(error => {
        console.error("Error fetching fire confidence data:", error);
        document.getElementById('fire-risk').innerText = "⚠️ Failed to fetch fire confidence data.";
    });
}


function fetchWeatherData(latitude, longitude) {
    const pointsUrl = `https://api.weather.gov/points/${latitude},${longitude}`;

    fetch(pointsUrl)
        .then(response => response.json())
        .then(pointsData => {
            const forecastUrl = pointsData.properties.forecast;
            const forecastHourlyUrl = pointsData.properties.forecastHourly;

            // Fetch daily forecast
            fetch(forecastUrl)
                .then(response => response.json())
                .then(forecastData => {
                    console.log("Daily Forecast:", forecastData);
                    // Extract and display daily forecast data
                    displayForecast(forecastData);
                })
                .catch(error => console.error("Error fetching daily forecast:", error));

            // Fetch hourly forecast
            fetch(forecastHourlyUrl)
                .then(response => response.json())
                .then(hourlyData => {
                    console.log("Hourly Forecast:", hourlyData);
                    // Extract and display hourly forecast data
                    displayHourlyForecast(hourlyData);
                })
                .catch(error => console.error("Error fetching hourly forecast:", error));
        })
        .catch(error => console.error("Error fetching points data:", error));
}

function displayForecast(forecastData) {
    if (forecastData && forecastData.properties && forecastData.properties.periods) {
        let forecastString = "";
        forecastData.properties.periods.forEach(period => {
            forecastString += `<b>${period.name}:</b> ${period.shortForecast}<br>`;
            forecastString += `Temperature: ${period.temperature} ${period.temperatureUnit}<br>`;
            forecastString += `Wind: ${period.windSpeed} ${period.windDirection}<br>`;
            if (period.relativeHumidity) { // Check if humidity data exists
                forecastString += `Humidity: ${period.relativeHumidity.value}%<br>`;
            }
            forecastString += "<br>"; // Add spacing between periods
        });
        document.getElementById("weather-details").innerHTML = forecastString;
    } else {
        document.getElementById("weather-details").innerHTML = "Forecast data not available.";
    }
}

function displayHourlyForecast(hourlyData) {
    if (hourlyData && hourlyData.properties && hourlyData.properties.periods) {
        let forecastString = "";
        hourlyData.properties.periods.slice(0, 12).forEach(period => {
            const startTime = new Date(period.startTime);
            forecastString += `<b>${startTime.toLocaleString()}:</b> ${period.shortForecast}<br>`;
            forecastString += `Temperature: ${period.temperature} ${period.temperatureUnit}<br>`;
            forecastString += `Wind: ${period.windSpeed} ${period.windDirection}<br>`;
            if (period.relativeHumidity) { // Check if humidity data exists
                forecastString += `Humidity: ${period.relativeHumidity.value}%<br>`;
            }
            forecastString += "<br>"; // Add spacing between periods
        });
        document.getElementById("weather-popup-content").innerHTML = forecastString;
    } else {
        document.getElementById("weather-popup-content").innerHTML = "Hourly forecast data not available.";
    }
}

function changeLanguage(lang) {
    selectedLanguage = lang;
    translatePage();
}

function translatePage() {
    translateAndDisplay("Your Location:", "location-label");
    // Add translations for other static text elements here
    fetchWeatherAndFireRisk(latitude, longitude); //reloads the weather data to translate it.
}


function translateAndDisplay(text, elementId) {
    fetch('/translate', {
        // ... your existing code ...
    })
    .then(response => response.json())
    .then(data => {
        if (data.translated_text) {
            document.getElementById(elementId).innerText = data.translated_text;
        } else {
            console.error("Translation failed for:", text, "to:", selectedLanguage);
            document.getElementById(elementId).innerText = "Translation failed";
        }
    })
    .catch(error => {
        console.error("Translation error for:", text, "to:", selectedLanguage, error);
        document.getElementById(elementId).innerText = "Translation error";
    });
}


navigator.geolocation.getCurrentPosition(
    (position) => {
        const { latitude, longitude } = position.coords;
        fetchWeatherData(latitude, longitude);
    },
    (error) => {
        console.error("Error getting location:", error);
    }
);


function showLoadingMessage() {
    document.getElementById("loading-message").style.display = 'block'; // Ensure this div exists
}

function hideLoadingMessage() {
    document.getElementById("loading-message").style.display = 'none';
}


// Function to fetch fire risk data from your backend
function fetchFireRiskData(latitude, longitude) {
    const current_date = new Date().toISOString().split('T')[0]; // Format: YYYY-MM-DD
    // Update the text to "Fetching fire risk..."
    document.getElementById('fire-risk').textContent = "Fetching fire risk...";

    fetch(`https://firms.modaps.eosdis.nasa.gov/api/active_fire/viirs/?api_key=93dbf5d44f179fcb7fba2f7cb38832be&start_date=${current_date}&end_date=${current_date}&lat=${latitude}&lon=${longitude}&radius=100"`)  // Make sure this endpoint is correct
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const fireRisk = data[0].fire_risk;  // Displaying fire risk from first data point for now
                document.getElementById('fire-risk').innerHTML = `🔥 Fire Risk Level: ${fireRisk}`;
            } else {
                document.getElementById('fire-risk').innerHTML = "No fire risk data available.";
            }
        })
        .catch(error => {
            console.error("Error fetching fire risk data:", error);
            document.getElementById('fire-risk').textContent = "⚠️ Failed to fetch fire risk.";
        });
}

function cycleFireRiskLevels() {
    document.getElementById('fire-risk').innerHTML = `Fire Risk Level: ${fireRiskLevels[currentRiskIndex]}`;
    currentRiskIndex = (currentRiskIndex + 1) % fireRiskLevels.length;
}

// Start cycling fire risk levels every 2 seconds
setInterval(cycleFireRiskLevels, 2000);

// Initialize the display with the first risk level
cycleFireRiskLevels();


window.initMap = initMap;
