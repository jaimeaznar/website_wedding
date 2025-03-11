// app/static/js/rsvp.js
document.addEventListener('DOMContentLoaded', function () {
    console.log("RSVP form script loaded");

    // Get form elements
    const form = document.getElementById('rsvpForm');
    const attendanceDetails = document.getElementById('attendance_details');
    const transportCheckboxes = document.querySelectorAll('.transport-checkbox');
    const hotelInput = document.getElementById('hotel_name');

    // Get the radio buttons by name (most reliable method)
    const attendingRadios = document.querySelectorAll('input[name="is_attending"]');
    console.log("Found", attendingRadios.length, "attendance radio buttons");

    // Function to toggle attendance details visibility
    function toggleAttendanceDetails() {
        let showDetails = false;

        // Check which radio is selected
        attendingRadios.forEach(radio => {
            if (radio.checked && radio.value === 'yes') {
                showDetails = true;
            }
        });

        // Show/hide based on selection
        attendanceDetails.style.display = showDetails ? 'block' : 'none';
        console.log("Toggled attendance details:", showDetails ? "showing" : "hidden");
    }

    // Add event listeners to radio buttons
    attendingRadios.forEach(radio => {
        console.log("Adding listener to radio:", radio.value);
        radio.addEventListener('change', function () {
            console.log("Radio changed:", this.value);
            toggleAttendanceDetails();
        });
    });

    // Check initial state
    console.log("Setting initial state");
    toggleAttendanceDetails();

    // Handle additional guests
    function createGuestInput(type, index) {
        console.log(`Creating ${type} input for index ${index}`);
        const card = document.createElement('div');
        card.className = 'card mb-3';

        // Get allergen template content and replace placeholder
        const template = document.getElementById('allergen-template');
        const allergenContent = template.innerHTML
            .replaceAll('PLACEHOLDER', `${type}_${index}`);

        card.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${type === 'adult' ? 'Additional Adult' : 'Child'} #${index + 1}</h5>
                <div class="mb-3">
                    <label class="form-label">Name*</label>
                    <input type="text" class="form-control" name="${type}_name_${index}" required>
                </div>
                <div class="mb-3">
                    <h6>Dietary Restrictions</h6>
                    ${allergenContent}
                </div>
            </div>
        `;
        return card;
    }

    // Handle adults count change
    const adultsSelect = document.getElementById('adults_count');
    if (adultsSelect) {
        console.log("Found adults count select");
        const adultsContainer = document.getElementById('additional_adults_container');
        adultsSelect.addEventListener('change', function () {
            console.log("Adults count changed to", this.value);
            adultsContainer.innerHTML = '';
            const count = parseInt(this.value) || 0;
            for (let i = 0; i < count; i++) {
                adultsContainer.appendChild(createGuestInput('adult', i));
            }
        });

        // Trigger once to initialize if needed
        if (parseInt(adultsSelect.value) > 0) {
            console.log("Initializing adults inputs");
            const event = new Event('change');
            adultsSelect.dispatchEvent(event);
        }
    }

    // Handle children count change
    const childrenSelect = document.getElementById('children_count');
    if (childrenSelect) {
        console.log("Found children count select");
        const childrenContainer = document.getElementById('children_container');
        childrenSelect.addEventListener('change', function () {
            console.log("Children count changed to", this.value);
            childrenContainer.innerHTML = '';
            const count = parseInt(this.value) || 0;
            for (let i = 0; i < count; i++) {
                childrenContainer.appendChild(createGuestInput('child', i));
            }
        });

        // Trigger once to initialize if needed
        if (parseInt(childrenSelect.value) > 0) {
            console.log("Initializing children inputs");
            const event = new Event('change');
            childrenSelect.dispatchEvent(event);
        }
    }

    console.log("RSVP form script initialization complete");
});