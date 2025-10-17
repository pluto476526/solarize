document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("module-input");
  const datalist = document.getElementById("module-list");
  let timeout = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();

    // Don't search for very short queries
    if (query.length < 3) {
      datalist.innerHTML = "";
      return;
    }

    clearTimeout(timeout);
    timeout = setTimeout(() => {
      fetch(`/analytics/module_search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
          datalist.innerHTML = "";
          data.forEach(item => {
            const option = document.createElement("option");
            option.value = item.name;
            option.textContent = `${item.name} (${item.manufacturer})`;
            datalist.appendChild(option);
          });
        })
        .catch(error => console.error("Autocomplete error:", error));
    }, 300); // Debounce: wait 300ms after typing stops
  });
});


document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("inverter-input");
  const datalist = document.getElementById("inverter-list");
  let timeout = null;

  input.addEventListener("input", () => {
    const query = input.value.trim();

    // Don't search for very short queries
    if (query.length < 3) {
      datalist.innerHTML = "";
      return;
    }

    clearTimeout(timeout);
    timeout = setTimeout(() => {
      fetch(`/analytics/inverter_search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
          datalist.innerHTML = "";
          data.forEach(item => {
            const option = document.createElement("option");
            option.value = item.name;
            option.textContent = `${item.name} (${item.manufacturer})`;
            datalist.appendChild(option);
          });
        })
        .catch(error => console.error("Autocomplete error:", error));
    }, 300); // Debounce: wait 300ms after typing stops
  });
});

