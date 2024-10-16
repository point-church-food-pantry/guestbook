// Fetch guest data from prior years
function fetchGuestData() {
    // 1) Retrieve the value from the input field with ID "old_guest"
    const guestID = document.getElementById("id_guest_ID").value;

    // 2) Call the API, replace guest_ID with the retrieved value
    fetch(`/guestbook_sign_in/lookup_guest/${guestID}`)
    .then(response => response.json())  // Convert response to JSON
    .then(data => {
        // 3) Unpack the JSON and assign values to variables
        const first_name = data.guests.first_name;
        const last_name = data.guests.last_name;
        const address = data.guests.address;
        const city = data.guests.city;
        const county = data.guests.county;
        const number_in_household = data.guests.number_in_household;

        document.getElementById('id_first_name').value = first_name;
        document.getElementById('id_last_name').value = last_name;
        document.getElementById('id_address').value = address;
        document.getElementById('id_city').value = city;
        document.getElementById('id_county').value = county;
        document.getElementById('id_number_in_household').value = number_in_household;
    })
    .catch(error => {
        console.error('Error fetching guest data:', error);
        alert('Warning: Lookup unsuccessful.')
        document.getElementById('id_first_name').value = 'NULL';
        document.getElementById('id_last_name').value = 'NULL';
        document.getElementById('id_address').value = 'NULL';
        document.getElementById('id_city').value = 'NULL';
        document.getElementById('id_county').value = 'NULL';
        document.getElementById('id_number_in_household').value = 0;
    });
}