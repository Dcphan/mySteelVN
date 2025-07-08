function renderProductTable(products, tableId) {
  const tableBody = $(`#${tableId} tbody`);
  const tableHead = $(`#${tableId} thead`);

  tableHead.empty();
  const head =  `
            <tr>
                <th>Company</th>
                <th>Product</th>
                <th>Date</th>
                <th>Production</th>
                <th>Inventory</th>
                <th>Northern</th>
                <th>Central</th>
                <th>Southern</th>
                <th>Export</th>
            </tr>
  `
  tableHead.append(head);
  
  tableBody.empty();

  for (const p of products) {
    const row = 
    `<tr>
        <td>${p.Company}</td>
        <td>${p.Product}</td>
        <td>${p.Date}</td>
        <td>${p.Production}</td>
        <td>${p.Inventory}</td>
        <td>${p.Northern}</td>
        <td>${p.Central}</td>
        <td>${p.Southern}</td>
        <td>${p.Export}</td>
      </tr>`;
    tableBody.append(row);
  }


  $(`#${tableId}`).DataTable();
}

function getSelectedProducts() {
  const checkboxes = document.querySelectorAll('.product-select input[type="checkbox"]:checked');
  return Array.from(checkboxes).map(cb => cb.value);
}

function getSelectedMonth() {
  return document.getElementById('month').value;
}

function fetchAndRenderTable() {
  const products = getSelectedProducts();
  const month = getSelectedMonth();

  if (products.length === 0 || !month) {
    alert("Please select at least one product and a month.");
    return;
  }

  const queryString = new URLSearchParams({
    products: products.join(','),
    month: month
  });
  

  fetch(`/api/table-data?${queryString.toString()}`)
    .then(response => {
      if (!response.ok) throw new Error("Failed to fetch data");
      return response.json();
    })
    .then(data => 
        {
            console.log("Chart data received:", data);
            renderProductTable(data, 'productTable');}
        )
    .catch(error => console.error("Error:", error));
}

$(document).ready(function () {
  $('#loadDataBtn').click(fetchAndRenderTable);
});

function renderMonthlyTable(data, tableId) {
  
  const tableBody = $(`#${tableId} tbody`);

  companyName = data.columns;
  companyInfo = data.rows;

  const thead = document.querySelector('#productTable thead');
  const tbody = document.querySelector('#productTable tbody');
  

// Clear any existing header content
thead.innerHTML = '';
tbody.innerHTML = '';

// Create a new header row
const header_row = document.createElement('tr');
const date = document.createElement('th');
date.textContent = "Date";
header_row.appendChild(date);
companyName.forEach(text => {
  const th = document.createElement('th');
  th.textContent = text;
  header_row.appendChild(th);
});


companyInfo.forEach(row => {
  const bodyRow = document.createElement('tr');
  const date_value = document.createElement('td');
  date_value.textContent = row['Month'];
  bodyRow.appendChild(date_value);
  companyName.forEach(company => {
    const company_value = document.createElement('td');
    company_value.textContent = row[company];
    bodyRow.appendChild(company_value);
  })

  tbody.append(bodyRow);
})
console.log(tbody);



// Append the new header row
thead.appendChild(header_row);

  $(`#${tableId}`).DataTable();
}

function fetchMonthlyData() {
  const container = document.getElementById("container"); // Update ID if needed
  const checkboxes = container.querySelectorAll("input[type='checkbox']:checked");
  const table = document.getElementById("table").value;

  const products = Array.from(checkboxes).map(cb => cb.value);
  console.log("Selected products:", products);

  const start = document.getElementById('start-month').value;
  const end = document.getElementById('end-month').value;

  if (products.length === 0 || !start || !end) {
    alert("Please select products and a valid date range.");
    return;
  }

  const queryParams = new URLSearchParams();
  queryParams.append('table', table);
  products.forEach(p => queryParams.append('product', p));
  queryParams.append('start', start);
  queryParams.append('end', end);
  
  fetch(`/api/monthly-summary?${queryParams.toString()}`)
    .then(res => {
      if (!res.ok) throw new Error(`Failed to fetch data: ${res.status}`);
      return res.json();
    })
    .then(data => {
      console.log("Fetched data:", data);
      // Use the data here (e.g., render chart)
      renderMonthlyTable(data, "productTable");

    })
    .catch(err => {
      console.error("Fetch error:", err);
      alert("Failed to fetch data. Please try again later.");
    });
}



$(document).ready(function () {
  $('#loadButton').click(fetchMonthlyData);
});
