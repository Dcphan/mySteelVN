
    let tomSelectInstance = null;

    export async function loadFilterOptions(filter) {
    const url = new URL('http://127.0.0.1:8000/api/filtering-data'); 
    url.searchParams.set("filter", filter);
    const res = await fetch(url);
    const options = await res.json();

    const datalist = document.getElementById("filterOptions");
    datalist.innerHTML = ''; // clear previous options

    options.forEach(opt => {
      const option = document.createElement("option");
      option.value = opt;
      datalist.appendChild(option);
    });
    }

    
    export async function loadRowOptions(filter) {
      const url = new URL('http://127.0.0.1:8000/api/filtering-data'); 
      url.searchParams.set("filter", filter);
      const res = await fetch(url);
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

    export async function fetchAndRenderTable(filter_fields, rows_fields, values_fields) { // With Two Rows

      // Collect Data
      const filter = document.getElementById("filterSelect").value;
      const date = document.getElementById("date").value;
      const rows = tomSelectInstance ? tomSelectInstance.getValue() : [];
      console.log("Filter Fields: ", filter_fields);

      if (!date) {
        alert("Please fill in all filters.");
        return;
      }


      // FETCHING DATA using URL
      const url = new URL("http://127.0.0.1:8000/api/pivot-data");
      url.searchParams.set("filter_field", filter_fields);
      rows_fields.forEach(r =>url.searchParams.append("rows_field", r));
      values_fields.forEach(r =>url.searchParams.append("value_field", r));
      url.searchParams.set("filter_value", filter); // Change "..." base on the URL
      url.searchParams.set("date", date);
      rows.forEach(r => url.searchParams.append("rows_value", r)); // Change "..." base on the URL     


      console.log("Value: ",values_fields);
      const res = await fetch(url);
      const data = await res.json();
      console.log("Data: ", data);
     
      // FIXING THE TABLE BODY
      const tableBody = document.getElementById("summary-table");
      tableBody.innerHTML = '';

      const grouped = {};
      
      // GROUP EVERY FIRST ROW TOGETHER (Easier to deal with data later)
      data.forEach(row => {
        if (!grouped[row[rows_fields[0]]]) grouped[row[rows_fields[0]]] = []; // Commodity is equivalent to the first field in Rows
        grouped[row[rows_fields[0]]].push(row);
      });

      
      for (const [rowName, rowsValue] of Object.entries(grouped)) {
        const total = rowsValue.find(r => r[rows_fields[1]] === 'TOTAL');
        const others = rowsValue.filter(r => r[rows_fields[1]] !== 'TOTAL');
        const rowsKey = makeSafeKey(rowName);
        console.log(others);

        // Total row with toggle
        const tr = document.createElement("tr");
        tr.className = "bg-blue-50 font-semibold";
        tr.innerHTML = `
          <td class="px-4 py-2">
            <button id="toggle-${rowsKey}" onclick="toggleCompanies('${rowsKey}')" class="text-lg font-bold">+</button>
            ${rowName}
          </td>
          <td class="px-4 py-2 text-gray-500">TOTAL</td>
        `;
        for (const element of values_fields){
            const td = document.createElement("td");
            td.className = "px-4 py-2 text-right";
            console.log(element)
            td.textContent = Number(total[element]).toLocaleString();
            tr.appendChild(td);
          }
        tableBody.appendChild(tr);

        others.forEach(companyRow => {
          const row = document.createElement("tr");
          row.className = `child-${rowsKey} hidden`; // keyword HIDDEN are responsible for the hidden
          row.innerHTML = `
            <td class="px-4 py-2">&nbsp</td>
            <td class="px-4 py-2">${companyRow[rows_fields[1]]}</td>
          `;
          for (const element of values_fields){
            const td = document.createElement("td");
            td.className = "px-4 py-2 text-right";
            console.log(element)
            td.textContent = Number(companyRow[element]).toLocaleString();
            row.appendChild(td);
          }
          tableBody.appendChild(row);
        });
      }
    }
    function makeSafeKey(input) {
  return input.toLowerCase().replace(/[^a-z0-9]/gi, '-'); // Only letters and digits
}
window.toggleCompanies = toggleCompanies;


  
