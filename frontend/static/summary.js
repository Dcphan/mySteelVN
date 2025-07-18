
    let tomSelectInstance = null;

    async function loadFilterOptions() {
    const res = await fetch('http://127.0.0.1:8000/api/country-options'); // Make this to be a variable that will change 
    const options = await res.json();

    const datalist = document.getElementById("filterOptions");
    datalist.innerHTML = ''; // clear previous options

    options.forEach(opt => {
      const option = document.createElement("option");
      option.value = opt;
      datalist.appendChild(option);
    });
    }

    
    async function loadRowOptions() {
      const res = await fetch('http://127.0.0.1:8000/api/commodity-options'); // Make this to be a variable that will change 
      const options = await res.json();
      const select = document.getElementById("rowSelect");
      select.innerHTML = '';

      options.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = opt;
        select.appendChild(option);
      });

      if (tomSelectInstance) tomSelectInstance.destroy();
      tomSelectInstance = new TomSelect("#rowSelect", {
        plugins: ['remove_button'],
        persist: false,
        create: false
      });
    }


   function toggleCompanies(value) {
      const rows = document.getElementsByClassName(`child-${value}`);
      const icon = document.getElementById(`toggle-${value}`);
      const isHidden = rows.length > 0 && rows[0].classList.contains('hidden');

      for (let i = 0; i < rows.length; i++) {
        if (isHidden) {
          rows[i].classList.remove('hidden');
        } else {
          rows[i].classList.add('hidden');
        }
      }

      icon.textContent = isHidden ? '-' : '+';
    }

    async function fetchAndRenderTable() {
      const filter = document.getElementById("filterSelect").value;
      const date = document.getElementById("date").value;
      const rows = tomSelectInstance ? tomSelectInstance.getValue() : [];

      if (!filter || !date || rows.length === 0) {
        alert("Please fill in all filters.");
        return;
      }

      const url = new URL("http://127.0.0.1:8000/api/pivot-country");
      url.searchParams.set("country", filter); // Change "..." base on the URL
      url.searchParams.set("date", date);
      rows.forEach(r => url.searchParams.append("commodities", r)); // Change "..." base on the URL
      

      const res = await fetch(url);
      const data = await res.json();
      

      const tableBody = document.getElementById("summary-table");
      tableBody.innerHTML = '';

      const grouped = {};
      
      data.forEach(row => {
        if (!grouped[row.commodity]) grouped[row.commodity] = []; // Commodity is equivalent to the first field in Rows
        grouped[row.commodity].push(row);
      });

      
      
      for (const [rowName, rowsValue] of Object.entries(grouped)) {
        console.log(rowsValue);
        
        const total = rowsValue.find(r => r.company === 'TOTAL');
        
        
        const others = rowsValue.filter(r => r.company !== 'TOTAL');
        const rowsKey = makeSafeKey(rowName);

        // Total row with toggle
        const tr = document.createElement("tr");
        tr.className = "bg-blue-50 font-semibold";
        tr.innerHTML = `
          <td class="px-4 py-2">
            <button id="toggle-${rowsKey}" onclick="toggleCompanies('${rowsKey}')" class="text-lg font-bold">+</button>
            ${rowName}
          </td>
          <td class="px-4 py-2 text-gray-500">TOTAL</td>
          <td class="px-4 py-2 text-right text-blue-600 font-bold">${Number(total.total_quantity).toLocaleString()}</td>
        `;
        tableBody.appendChild(tr);

        others.forEach(companyRow => {
          const row = document.createElement("tr");
          row.className = `child-${rowsKey} hidden`; // keyword HIDDEN are responsible for the hidden
          row.innerHTML = `
            <td class="px-4 py-2">&nbsp;</td>
            <td class="px-4 py-2">${companyRow.company}</td>
            <td class="px-4 py-2 text-right">${Number(companyRow.total_quantity).toLocaleString()}</td>
          `;
          tableBody.appendChild(row);
        });
      }
    }
    function makeSafeKey(input) {
  return input.toLowerCase().replace(/[^a-z0-9]/gi, '-'); // Only letters and digits
}

// drag_and_drop.js

loadRowOptions();
loadFilterOptions();
  
