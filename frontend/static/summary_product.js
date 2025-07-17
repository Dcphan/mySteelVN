
    let tomSelectInstance = null;  

    async function loadCommodityOptions() {
    const res = await fetch('http://127.0.0.1:8000/api/commodity-options');
    const options = await res.json();

    const datalist = document.getElementById("commodityOptions");
    datalist.innerHTML = ''; // clear previous options

    options.forEach(opt => {
      const option = document.createElement("option");
      option.value = opt;
      datalist.appendChild(option);
    });
  }




    async function loadCountryOptions() {
      const res = await fetch('http://127.0.0.1:8000/api/country-options');
      const options = await res.json();
      const select = document.getElementById("countrySelect");
      select.innerHTML = '';

      options.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = opt;
        select.appendChild(option);
      });

      if (tomSelectInstance) tomSelectInstance.destroy();
      tomSelectInstance = new TomSelect("#countrySelect", {
        plugins: ['remove_button'],
        persist: false,
        create: false
      });
    }



       function toggleCompanies(commodity) {
        const rows = document.getElementsByClassName(`child-${commodity}`);
        const icon = document.getElementById(`toggle-${commodity}`);
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
      const country = document.getElementById("commoditySelect").value;
      const date = document.getElementById("date").value;
      const commodities = tomSelectInstance ? tomSelectInstance.getValue() : [];

      if (!country || !date || commodities.length === 0) {
        alert("Please fill in all filters.");
        return;
      }

      const url = new URL("http://127.0.0.1:8000/api/pivot-commodity");
      url.searchParams.set("commodity", country);
      url.searchParams.set("date", date);
      commodities.forEach(c => url.searchParams.append("countries", c));

      const res = await fetch(url);
      const data = await res.json();

      const tableBody = document.getElementById("summary-table");
      tableBody.innerHTML = '';

      const grouped = {};
      data.forEach(row => {
        if (!grouped[row.country]) grouped[row.country] = [];
        grouped[row.country].push(row);
      });

      for (const [country, rows] of Object.entries(grouped)) {
        const total = rows.find(r => r.company === 'TOTAL');
        const others = rows.filter(r => r.company !== 'TOTAL');
        const countriesKey = country.replace(/\s+/g, '-');;

        // Total row with toggle
        const tr = document.createElement("tr");
        tr.className = "bg-blue-50 font-semibold";
        tr.innerHTML = `
          <td class="px-4 py-2">
            <button id="toggle-${countriesKey}" onclick="toggleCompanies('${countriesKey}')" class="text-lg font-bold">+</button>
            ${country}
          </td>
          <td class="px-4 py-2 text-gray-500">TOTAL</td>
          <td class="px-4 py-2 text-right text-blue-600 font-bold">${Number(total.total_quantity).toLocaleString()}</td>
        `;
        tableBody.appendChild(tr);
        console.log(countriesKey);

        others.forEach(companyRow => {
          const row = document.createElement("tr");
          row.className = `child-${countriesKey} hidden`;
          row.innerHTML = `
            <td class="px-4 py-2">&nbsp;</td>
            <td class="px-4 py-2">${companyRow.company}</td>
            <td class="px-4 py-2 text-right">${Number(companyRow.total_quantity).toLocaleString()}</td>
          `;
          tableBody.appendChild(row);
        });
      }
    }

    loadCountryOptions();
    loadCommodityOptions();
  