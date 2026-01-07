// app/static/js/rsvp.js - IMPROVED VERSION
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
        if (attendanceDetails) {
            attendanceDetails.style.display = showDetails ? 'block' : 'none';
            console.log("Toggled attendance details:", showDetails ? "showing" : "hidden");
        }
    }

    // Check if we have radio buttons (they might not be present for existing RSVPs)
    if (attendingRadios.length > 0) {
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
    } else {
        console.log("No radio buttons found, already RSVP'd");
    }

    // Handle additional guests
    function createGuestInput(type, index) {
        console.log(`Creating ${type} input for index ${index}`);
        const card = document.createElement('div');
        card.className = 'guest-card';

        // Get allergen template content and replace placeholder
        const template = document.getElementById('allergen-template');
        let allergenContent = '';

        if (template) {
            allergenContent = template.innerHTML
                .replaceAll('PLACEHOLDER', `${type}_${index}`);
        } else {
            console.warn("Allergen template not found");
        }

        card.innerHTML = `
            <h5 class="mb-3">${type === 'adult' ? 'Additional Adult' : 'Child'} #${index + 1}</h5>
            <div class="mb-3">
                <label class="form-label">Name*</label>
                <input type="text" class="form-control" name="${type}_name_${index}" required>
            </div>
            <div class="mb-3">
                <h6 class="mb-3">Dietary Restrictions</h6>
                ${allergenContent}
            </div>
        `;
        return card;
    }

    // Function to prefill existing additional guests
    function prefillAdditionalGuests() {
        const existingGuestsData = document.getElementById('existing-guests-data');
        if (!existingGuestsData) return;
        
        try {
            const guests = JSON.parse(existingGuestsData.textContent);
            console.log("Existing additional guests:", guests);
            
            let adultIndex = 0;
            let childIndex = 0;
            
            guests.forEach(guest => {
                if (guest.is_child) {
                    const nameInput = document.querySelector(`input[name="child_name_${childIndex}"]`);
                    if (nameInput) {
                        nameInput.value = guest.name;
                        console.log(`Prefilled child ${childIndex}: ${guest.name}`);
                    }
                    childIndex++;
                } else {
                    const nameInput = document.querySelector(`input[name="adult_name_${adultIndex}"]`);
                    if (nameInput) {
                        nameInput.value = guest.name;
                        console.log(`Prefilled adult ${adultIndex}: ${guest.name}`);
                    }
                    adultIndex++;
                }
            });
        } catch (e) {
            console.error("Error parsing existing guests data:", e);
        }
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
            // Prefill after creating inputs
            setTimeout(prefillAdditionalGuests, 50);
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
            // Prefill after creating inputs
            setTimeout(prefillAdditionalGuests, 50);
        });

        // Trigger once to initialize if needed
        if (parseInt(childrenSelect.value) > 0) {
            console.log("Initializing children inputs");
            const event = new Event('change');
            childrenSelect.dispatchEvent(event);
        }
    }

    // Improved allergen prefilling function
    function prefillAllergens() {
        console.log("Prefilling allergens if available");
        const existingAllergens = document.querySelectorAll('[data-allergen-guest]');
        console.log("Found", existingAllergens.length, "existing allergen records");

        existingAllergens.forEach(element => {
            const guestName = element.getAttribute('data-allergen-guest');
            const allergenId = element.getAttribute('data-allergen-id');
            const customAllergen = element.getAttribute('data-custom-allergen');

            console.log("Processing allergen for guest:", guestName, "allergenId:", allergenId, "custom:", customAllergen);

            // Find the corresponding checkbox or input in the form
            if (guestName && allergenId && allergenId !== 'None') {
                // Try different possible field name formats
                const possibleNames = [
                    `allergens_${guestName.toLowerCase().replace(' ', '_')}`,
                    `allergens_main`,
                ];

                let found = false;
                possibleNames.forEach(name => {
                    if (!found) {
                        const checkbox = document.querySelector(`input[name="${name}"][value="${allergenId}"]`);
                        if (checkbox) {
                            checkbox.checked = true;
                            console.log("Checked allergen checkbox:", name, allergenId);
                            found = true;
                        }
                    }
                });

                if (!found) {
                    console.warn("Could not find checkbox for allergen:", allergenId, "guest:", guestName);
                }
            }

            if (guestName && customAllergen && customAllergen !== 'None') {
                // Try different possible field name formats for custom allergens
                const possibleCustomNames = [
                    `custom_allergen_${guestName.toLowerCase().replace(' ', '_')}`,
                    `custom_allergen_main`                ];

                let found = false;
                possibleCustomNames.forEach(name => {
                    if (!found) {
                        const input = document.querySelector(`input[name="${name}"]`);
                        if (input) {
                            input.value = customAllergen;
                            console.log("Set custom allergen:", name, customAllergen);
                            found = true;
                        }
                    }
                });

                if (!found) {
                    console.warn("Could not find custom allergen input for guest:", guestName);
                }
            }
        });
    }



    // Call prefill function with a slight delay to ensure all elements are rendered
    setTimeout(prefillAllergens, 100);

    // Validate transport and hotel inputs
    function validateTransportHotel() {
        let needsHotel = false;

        transportCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                needsHotel = true;
            }
        });

        if (needsHotel && hotelInput) {
            hotelInput.required = true;
            const hotelFormGroup = hotelInput.closest('.mb-3');
            if (hotelFormGroup) {
                const label = hotelFormGroup.querySelector('label');
                if (label) {
                    if (!label.innerHTML.includes('*')) {
                        label.innerHTML += '*';
                    }
                }
            }
        } else if (hotelInput) {
            hotelInput.required = false;
            const hotelFormGroup = hotelInput.closest('.mb-3');
            if (hotelFormGroup) {
                const label = hotelFormGroup.querySelector('label');
                if (label && label.innerHTML.includes('*')) {
                    label.innerHTML = label.innerHTML.replace('*', '');
                }
            }
        }
    }

    // Add event listeners to transport checkboxes
    transportCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', validateTransportHotel);
    });

    // Initialize validation
    if (transportCheckboxes.length > 0 && hotelInput) {
        validateTransportHotel();
    }

    // Form submission debugging
    if (form) {
        form.addEventListener('submit', function (e) {
            console.log("Form being submitted");

            // Log all form data for debugging
            const formData = new FormData(form);
            console.log("Form data being submitted:");
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }

            // Check for allergen data specifically
            const allergenInputs = form.querySelectorAll('input[name^="allergens_"], input[name^="custom_allergen_"]');
            console.log("Allergen inputs found:", allergenInputs.length);
            allergenInputs.forEach(input => {
                if (input.type === 'checkbox' && input.checked) {
                    console.log(`Checked allergen: ${input.name} = ${input.value}`);
                } else if (input.type === 'text' && input.value.trim()) {
                    console.log(`Custom allergen: ${input.name} = ${input.value}`);
                }
            });
        });
    }

    console.log("RSVP form script initialization complete");
});