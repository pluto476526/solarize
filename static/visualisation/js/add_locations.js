   let locationCount = 1;

        // Add new location
        document.getElementById('addLocation').addEventListener('click', function() {
            const container = document.getElementById('locationsContainer');
            const newIndex = locationCount;
            
            const locationHTML = `
                <div class="location-group mb-4 p-3 border rounded" data-location-index="${newIndex}">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mb-0">Location #${newIndex + 1}</h6>
                        <button type="button" class="btn btn-sm btn-outline-danger remove-location">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="row g-3">
                        <div class="col-md-12">
                            <label for="locationName_${newIndex}" class="form-label">Location Name</label>
                            <input type="text" class="form-control location-name" id="locationName_${newIndex}" 
                                   name="locations[${newIndex}][name]" placeholder="e.g., London" value="" required>
                        </div>
                        
                        <div class="col-md-6">
                            <label for="lat_${newIndex}" class="form-label">Latitude</label>
                            <input type="number" class="form-control" id="lat_${newIndex}" 
                                   name="locations[${newIndex}][lat]" step="any" placeholder="Enter latitude" required>
                        </div>
                        
                        <div class="col-md-6">
                            <label for="lon_${newIndex}" class="form-label">Longitude</label>
                            <input type="number" class="form-control" id="lon_${newIndex}" 
                                   name="locations[${newIndex}][lon]" step="any" placeholder="Enter longitude" required>
                        </div>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML('beforeend', locationHTML);
            locationCount++;
            
            // Enable remove buttons for all except first
            document.querySelectorAll('.remove-location').forEach(btn => {
                btn.disabled = false;
            });
        });

        // Remove location
        document.addEventListener('click', function(e) {
            if (e.target.closest('.remove-location')) {
                const locationGroup = e.target.closest('.location-group');
                if (document.querySelectorAll('.location-group').length > 1) {
                    locationGroup.remove();
                    // Re-index remaining locations
                    reindexLocations();
                }
            }
        });

        // Re-index locations after removal
        function reindexLocations() {
            const locations = document.querySelectorAll('.location-group');
            locationCount = locations.length;
            
            locations.forEach((location, index) => {
                location.setAttribute('data-location-index', index);
                location.querySelector('h6').textContent = `Location #${index + 1}`;
                
                // Update input names and IDs
                const inputs = location.querySelectorAll('input');
                inputs.forEach(input => {
                    const oldName = input.name;
                    const newName = oldName.replace(/locations\[\d+\]/, `locations[${index}]`);
                    input.name = newName;
                    input.id = input.id.replace(/_(\d+)_/, `_${index}_`);
                });
            });
            
            // Disable remove button if only one location remains
            if (locations.length === 1) {
                document.querySelector('.remove-location').disabled = true;
            }
        }
