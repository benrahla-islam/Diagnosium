let map;
let service;
let infowindow;
let currentPosition;
let markers = [];

// Replace with your actual Google Maps API Key
const GOOGLE_MAPS_API_KEY = "YOUR_ACTUAL_API_KEY"; 

function initMap() {
    console.log("initMap called");
    const defaultLocation = { lat: 40.7128, lng: -74.0060 }; // Default: NYC
    const statusElement = document.getElementById('status');
    
    if (!statusElement) {
        console.error("Map status element not found!");
        return;
    }

    infowindow = new google.maps.InfoWindow();

    map = new google.maps.Map(document.getElementById("map-container"), {
        center: defaultLocation,
        zoom: 12,
        mapTypeControl: false,
        streetViewControl: false
    });

    statusElement.textContent = "Attempting to get your location...";

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                };
                console.log("Location found:", currentPosition);
                statusElement.textContent = "Location found! Searching...";
                map.setCenter(currentPosition);
                map.setZoom(14);

                // Add marker for user's location
                new google.maps.Marker({
                    position: currentPosition,
                    map: map,
                    title: "Your Location",
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 8,
                        fillColor: "#4285F4",
                        fillOpacity: 1,
                        strokeWeight: 2,
                        strokeColor: "#FFFFFF",
                    },
                    zIndex: 10
                });

                service = new google.maps.places.PlacesService(map);
                findNearbyMedicalFacilities(currentPosition, 5000); // 5km radius
            },
            (error) => {
                handleLocationError(true, error, defaultLocation, statusElement);
                currentPosition = defaultLocation;
                service = new google.maps.places.PlacesService(map);
                findNearbyMedicalFacilities(currentPosition, 5000);
            },
            {
                enableHighAccuracy: true,
                timeout: 8000,
                maximumAge: 0
            }
        );
    } else {
        handleLocationError(false, null, defaultLocation, statusElement);
        currentPosition = defaultLocation;
        service = new google.maps.places.PlacesService(map);
        findNearbyMedicalFacilities(currentPosition, 5000);
    }
}

function handleLocationError(browserHasGeolocation, error, pos, statusElement) {
    let message = "Geolocation error: ";
    if (error) {
        switch(error.code) {
            case error.PERMISSION_DENIED: 
                message += "Permission denied. Please enable location services.";
                break;
            case error.POSITION_UNAVAILABLE: 
                message += "Location unavailable.";
                break;
            case error.TIMEOUT: 
                message += "Request timed out.";
                break;
            default: 
                message += "Unknown error.";
                break;
        }
    } else if (!browserHasGeolocation) {
        message = "Error: Browser doesn't support geolocation.";
    }
    console.error(message);
    statusElement.textContent = message + " Using default location.";
    map.setCenter(pos);
}

async function findNearbyMedicalFacilities(location, radius) {
    const statusElement = document.getElementById('status');
    
    // Clear previous markers
    markers.forEach(marker => marker.setMap(null));
    markers = [];

    try {
        statusElement.textContent = `Searching within ${radius/1000}km...`;
        
        // Search for pharmacies and hospitals separately
        const pharmacyPromise = findPlaces(location, radius, ['pharmacy'], 'pharmacy');
        const hospitalPromise = findPlaces(location, radius, ['hospital', 'doctor', 'health'], 'medical');
        
        const [pharmacies, hospitals] = await Promise.all([pharmacyPromise, hospitalPromise]);
        
        // Process results
        const allPlaces = [...pharmacies, ...hospitals];
        
        if (allPlaces.length === 0) {
            statusElement.textContent = `No medical facilities found within ${radius/1000}km.`;
            return;
        }
        
        // Create markers and fit bounds
        const bounds = new google.maps.LatLngBounds();
        bounds.extend(location); // Include user's location
        
        allPlaces.forEach(place => {
            const isPharmacy = place.types.includes('pharmacy');
            createMarker(place, isPharmacy ? 'pharmacy' : 'hospital');
            if (place.geometry && place.geometry.location) {
                bounds.extend(place.geometry.location);
            }
        });
        
        statusElement.textContent = `Found ${pharmacies.length} pharmacies and ${hospitals.length} hospitals/clinics.`;
        
        map.fitBounds(bounds);
        // Prevent over-zooming
        if (map.getZoom() > 15) map.setZoom(15);
        
    } catch (error) {
        console.error("Error finding medical facilities:", error);
        statusElement.textContent = "Error searching for medical facilities. Please try again.";
    }
}

function findPlaces(location, radius, types, keyword) {
    return new Promise((resolve, reject) => {
        const request = {
            location: location,
            radius: radius,
            types: types,
            keyword: keyword
        };
        
        service.nearbySearch(request, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                resolve(results || []);
            } else {
                console.error(`Places API error for ${keyword}:`, status);
                resolve([]); // Return empty array instead of rejecting
            }
        });
    });
}

function createMarker(place, type) {
    if (!place.geometry || !place.geometry.location) {
        console.warn("Place missing geometry:", place.name);
        return;
    }

    const icon = {
        url: type === 'pharmacy' 
            ? 'https://maps.google.com/mapfiles/ms/icons/green-dot.png'
            : 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
        scaledSize: new google.maps.Size(32, 32)
    };

    const marker = new google.maps.Marker({
        map: map,
        position: place.geometry.location,
        title: place.name,
        icon: icon
    });

    markers.push(marker);

    google.maps.event.addListener(marker, "click", () => {
        const content = createInfoWindowContent(place, type);
        infowindow.setContent(content);
        infowindow.open(map, marker);
    });
}

function createInfoWindowContent(place, type) {
    const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${place.geometry.location.lat()},${place.geometry.location.lng()}`;
    
    return `
        <div style="font-family: 'Poppins', sans-serif; max-width: 250px; font-size: 13px; line-height: 1.5;">
            <strong style="font-size: 1.1em; color: #333;">${place.name}</strong><br>
            ${place.vicinity ? `${place.vicinity}<br>` : ''}
            ${place.rating ? `Rating: ${place.rating} ★ (${place.user_ratings_total || 'N/A'})<br>` : ''}
            ${place.opening_hours ? `Status: ${place.opening_hours.open_now ? '<span style="color: green;">Open Now</span>' : '<span style="color: red;">Closed</span>'}<br>` : ''}
            Type: ${type === 'pharmacy' ? 'Pharmacy' : 'Hospital/Clinic'}<br>
            <a href="${directionsUrl}" target="_blank" style="color: #3a7bd5; text-decoration: none; font-weight: 500; margin-top: 5px; display: inline-block;">
                Get Directions →
            </a>
        </div>
    `;
}

function loadGoogleMapsScript() {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap`;
    script.async = true;
    script.defer = true;
    script.onerror = () => {
        console.error("Failed to load Google Maps script.");
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = "Error loading Google Maps. Please check your API key.";
        }
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            mapContainer.innerHTML = '<p style="text-align: center; padding: 20px; color: red;">Could not load map. Please check your Google Maps API key.</p>';
        }
    };
    document.head.appendChild(script);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', loadGoogleMapsScript);