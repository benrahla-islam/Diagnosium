// Map initialization and location services using OpenStreetMap and Leaflet

// Global variables
let map;
let currentPosition;
let markers = [];

// Initialize the map
function initMap() {
    console.log("initMap called");
    const defaultLocation = [40.7128, -74.0060]; // Default: NYC [lat, lng]
    const statusElement = document.getElementById('status');
    if (!statusElement) {
        console.error("Map status element not found!");
        return;
    }

    // Initialize Leaflet map
    map = L.map('map-container').setView(defaultLocation, 13);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    statusElement.textContent = "Attempting to get your location...";

    // Try to get user location with improved error handling
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentPosition = [
                    position.coords.latitude,
                    position.coords.longitude
                ];
                console.log("Location found:", currentPosition);
                statusElement.textContent = "Location found! Searching...";
                
                // Center map on user's location
                map.setView(currentPosition, 15);
                
                // Add marker for user's position
                const userMarker = L.circleMarker(currentPosition, {
                    radius: 8,
                    fillColor: "#4285F4",
                    color: "#FFFFFF",
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 1
                }).addTo(map);
                
                userMarker.bindPopup("<strong>Your Location</strong>").openPopup();
                
                // Find nearby facilities
                findNearbyPlaces(currentPosition, 5000);
            },
            (error) => {
                handleLocationError(true, error, defaultLocation, statusElement);
                currentPosition = defaultLocation; // Use default if error
                findNearbyPlaces(defaultLocation, 5000);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        handleLocationError(false, null, defaultLocation, statusElement);
        currentPosition = defaultLocation;
        findNearbyPlaces(defaultLocation, 5000);
    }
}

// Handle geolocation errors with informative messages
function handleLocationError(browserHasGeolocation, error, defaultPos, statusElement) {
    let message = "Geolocation error: ";
    if (error) {
        switch(error.code) {
            case error.PERMISSION_DENIED: 
                message += "Location permission denied. Please enable location services."; 
                break;
            case error.POSITION_UNAVAILABLE: 
                message += "Location unavailable. Please check your connection."; 
                break;
            case error.TIMEOUT: 
                message += "Location request timed out. Please try again."; 
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
    map.setView(defaultPos, 13);
}

// Search for nearby places using Overpass API
async function searchNearbyFacilities(location, facilityType, radius) {
    try {
        // Convert radius from meters to degrees (approximate)
        const radiusInDegrees = radius / 111000; // ~111km per degree of latitude
        
        // Create the bounding box coordinates
        const south = location[0] - radiusInDegrees;
        const west = location[1] - radiusInDegrees;
        const north = location[0] + radiusInDegrees;
        const east = location[1] + radiusInDegrees;
        
        // Create Overpass query
        let amenityType = facilityType === 'pharmacy' ? 'pharmacy' : 'hospital';
        const overpassQuery = `
            [out:json];
            (
              node["amenity"="${amenityType}"](${south},${west},${north},${east});
              way["amenity"="${amenityType}"](${south},${west},${north},${east});
              relation["amenity"="${amenityType}"](${south},${west},${north},${east});
            );
            out center;
        `;
        
        const response = await fetch('https://overpass-api.de/api/interpreter', {
            method: 'POST',
            body: overpassQuery,
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        return data.elements.map(element => {
            // Get coordinates based on element type
            let lat, lon, tags;
            
            if (element.type === 'node') {
                lat = element.lat;
                lon = element.lon;
                tags = element.tags;
            } else {
                // For ways and relations, use the center point
                lat = element.center.lat;
                lon = element.center.lon;
                tags = element.tags;
            }
            
            return {
                name: tags.name || `${amenityType.charAt(0).toUpperCase() + amenityType.slice(1)}`,
                position: [lat, lon],
                address: tags['addr:street'] ? 
                    `${tags['addr:housenumber'] || ''} ${tags['addr:street'] || ''}, ${tags['addr:city'] || ''}`.trim() : 
                    undefined,
                type: facilityType,
                phone: tags.phone,
                opening_hours: tags.opening_hours
            };
        });
    } catch (error) {
        console.error(`Error fetching ${facilityType}:`, error);
        return [];
    }
}

// Find nearby medical facilities
async function findNearbyPlaces(location, initialRadius) {
    const statusElement = document.getElementById('status');
    let radius = initialRadius;
    const maxRadius = 20000; // 20km
    
    // Clear previous markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    try {
        statusElement.textContent = `Searching within ${radius/1000}km...`;
        
        // Search for pharmacies and hospitals
        const [pharmacies, hospitals] = await Promise.all([
            searchNearbyFacilities(location, 'pharmacy', radius),
            searchNearbyFacilities(location, 'hospital', radius)
        ]);
        
        let allPlaces = [...pharmacies, ...hospitals];
        console.log("Initial search results:", allPlaces.length);
        
        // If few results, expand search radius
        if (allPlaces.length < 5 && radius < maxRadius) {
            console.log("Few results, expanding search radius.");
            radius *= 2;
            statusElement.textContent = `Expanding search to ${radius/1000}km...`;
            
            const [morePharmacies, moreHospitals] = await Promise.all([
                searchNearbyFacilities(location, 'pharmacy', radius),
                searchNearbyFacilities(location, 'hospital', radius)
            ]);
            
            // Add new places, avoiding duplicates
            const existingCoords = new Set(allPlaces.map(place => 
                `${place.position[0].toFixed(6)},${place.position[1].toFixed(6)}`
            ));
            
            [...morePharmacies, ...moreHospitals].forEach(place => {
                const coordKey = `${place.position[0].toFixed(6)},${place.position[1].toFixed(6)}`;
                if (!existingCoords.has(coordKey)) {
                    allPlaces.push(place);
                    existingCoords.add(coordKey);
                }
            });
            
            console.log("Expanded search results:", allPlaces.length);
        }
        
        if (allPlaces.length === 0) {
            statusElement.textContent = `No medical facilities found within ${radius/1000}km.`;
            return;
        }
        
        // Create markers and calculate bounds
        const bounds = L.latLngBounds([location]);
        
        allPlaces.forEach(place => {
            createMarker(place);
            bounds.extend(place.position);
        });
        
        // Count facilities
        const pharmacyCount = allPlaces.filter(p => p.type === 'pharmacy').length;
        const hospitalCount = allPlaces.filter(p => p.type === 'hospital').length;
        
        statusElement.textContent = `Found ${pharmacyCount} pharmacies, ${hospitalCount} hospitals/clinics.`;
        
        // Fit map to bounds
        map.fitBounds(bounds, { padding: [30, 30] });
        
    } catch (error) {
        console.error("Error during place search:", error);
        statusElement.textContent = `Error searching for medical facilities: ${error.message}`;
    }
}

// Create markers for facilities
function createMarker(place) {
    const markerOptions = {
        radius: 8,
        fillColor: place.type === 'pharmacy' ? '#4CAF50' : '#F44336',
        color: '#fff',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    };
    
    const marker = L.circleMarker(place.position, markerOptions).addTo(map);
    markers.push(marker);
    
    // Create popup content
    let content = `<div style="font-family: 'Poppins', sans-serif; max-width: 250px; font-size: 13px; line-height: 1.5;">`;
    content += `<strong style="font-size: 1.1em; color: #333;">${place.name || 'Medical Facility'}</strong><br>`;
    
    if (place.address) {
        content += `${place.address}<br>`;
    }
    
    if (place.phone) {
        content += `Phone: ${place.phone}<br>`;
    }
    
    if (place.opening_hours) {
        content += `Hours: ${place.opening_hours}<br>`;
    }
    
    content += `Type: ${place.type === 'pharmacy' ? 'Pharmacy' : 'Hospital/Clinic'}<br>`;
    
    // Calculate directions URL
    const directionsUrl = `https://www.openstreetmap.org/directions?from=${currentPosition[0]},${currentPosition[1]}&to=${place.position[0]},${place.position[1]}`;
    content += `<a href="${directionsUrl}" target="_blank" style="color: #3a7bd5; text-decoration: none; font-weight: 500; margin-top: 5px; display: inline-block;">Get Directions →</a>`;
    content += `</div>`;
    
    marker.bindPopup(content);
    
    // Add click event
    marker.on('click', function() {
        this.openPopup();
    });
}

// Initialize map when DOM is ready
// Remove this block:
// document.addEventListener('DOMContentLoaded', function() {
//     if (document.getElementById('map-container')) {
//         initMap();
//     }
// });

// Make functions available to window scope for debugging
window.initMap = initMap;
window.findNearbyPlaces = findNearbyPlaces;
