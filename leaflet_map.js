// Simple Leaflet map - add this to replace the Mapbox code

function initLeafletMap() {
    try {
        // Initialize the map
        const map = L.map('map').setView([37.7749, -122.4194], 11);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Add sample markers
        const markers = [
            { lat: 37.8199, lng: -122.4783, title: "Golden Gate Portrait", location: "Golden Gate Bridge" },
            { lat: 37.7599, lng: -122.4148, title: "Mission Street", location: "Mission District" },
            { lat: 37.8974, lng: -122.5808, title: "Nature Photo", location: "Muir Woods" }
        ];
        
        markers.forEach(marker => {
            L.marker([marker.lat, marker.lng])
                .addTo(map)
                .bindPopup(`<strong>${marker.title}</strong><br>${marker.location}`);
        });
        
        console.log('Leaflet map initialized successfully');
        
    } catch (error) {
        console.error('Map error:', error);
        document.getElementById('map').innerHTML = `
            <div class="flex items-center justify-center h-full text-gray-500">
                <div class="text-center">
                    <p class="text-sm">Map initialization failed</p>
                </div>
            </div>
        `;
    }
}

// Initialize map after page loads
setTimeout(initLeafletMap, 1000);
