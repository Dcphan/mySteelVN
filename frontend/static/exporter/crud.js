let offset = 0;
const limit = 100;
let selectedDate = null;
let currentEditId = null;

function openModal() {
  document.getElementById('modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
  currentEditId = null;
}

// ✅ NEW: Called on form submit
async function update_row() {
  const id = currentEditId;
  const quantity = document.getElementById('quantity').value;
  const amount = document.getElementById('amount').value;

  if (!id) {
    alert("Missing ID for update");
    return;
  }

  const success = await updateRecord(id, quantity, amount);
  if (success) {
    alert("Updated!");
    closeModal();
  }
}

async function editRow(id, importer, importer_address, exporter, exporter_address, commodity, unit_price, quantity, amount) {
  document.getElementById('modalTitle').textContent = 'Edit Company';

  currentEditId = id;

  document.getElementById('importer').value = importer;
  document.getElementById('importer_address').value = importer_address;
  document.getElementById('exporter').value = exporter;
  document.getElementById('exporter_address').value = exporter_address;
  document.getElementById('commodity').value = commodity;
  document.getElementById('unit_price').value = unit_price;
  document.getElementById('quantity').value = quantity;
  document.getElementById('amount').value = amount;

  openModal();
}

async function deleteRow(id) {
  if (!confirm("Are you sure to delete this company?")) return;

  try {
    const response = await fetch(`/exporter/api/delete?id=${id}`, {
      method: "DELETE",
    });

    if (!response.ok) throw new Error("Failed to delete");

    document.getElementById(`row-${id}`)?.remove();
    alert("Deleted!");
  } catch (error) {
    console.error("Error deleting row:", error);
    alert("Failed to delete record.");
  }
}

async function fetchData(date, limit, offset) {
  if (limit < 1 || limit > 1000) throw new Error("Limit must be between 1 and 1000");
  if (offset < 0) throw new Error("Offset cannot be negative");

  const url = new URL("https://mysteelvn.onrender.com/exporter/api/data");
  url.searchParams.set("date", date);
  url.searchParams.set("offset", offset);
  url.searchParams.set("limit", limit);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Server responded with ${response.status}`);
    const data = await response.json();
    return data;
  } catch (err) {
    console.error("Failed to fetch data:", err);
    return [];
  }
}

async function loadMore() {
  if (!selectedDate) {
    console.warn("Month not selected yet");
    return;
  }

  const data = await fetchData(selectedDate, limit, offset);
  const tableBody = document.getElementById("data-table");

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.className = "border-t hover:bg-gray-50";
    tr.id = `row-${row.id}`;
    tr.innerHTML = `
      <td class="px-6 py-4">${row.id}</td>
      <td class="px-6 py-4">${row.date}</td>
      <td class="px-6 py-4">${row.tax_code}</td>
      <td class="sticky left-0 w-[200px] bg-white z-10 px-6 py-4">${row.importer}</td>
      <td class="px-6 py-4">${row.importer_address}</td>
      <td class="sticky left-[200px] w-[200px] bg-white z-10 px-6 py-4">${row.country}</td>
      <td class="px-6 py-4">${row.exporter}</td>
      <td class="px-6 py-4">${row.exporter_address}</td>
      <td class="px-6 py-4">${row.hs_code}</td>
      <td class="px-6 py-4">${row.commodity}</td>
      <td class="px-6 py-4">${row.exchange_rate}</td>
      <td class="px-6 py-4">${row.unit_price}</td>
      <td class="px-6 py-4">${row.quantity}</td>
      <td class="px-6 py-4">${row.amount}</td>
      <td class="px-6 py-4">${row.place_of_r}</td>
      <td class="px-6 py-4">${row.place_of_l}</td>
      <td class="px-6 py-4">${row.product_description}</td>
      <td class="px-6 py-4 space-x-2">
        <button 
          class="text-blue-600 hover:underline" 
          onclick="editRow(
            '${row.id}', 
            '${row.importer}', 
            '${row.importer_address}', 
            '${row.exporter}', 
            '${row.exporter_address}', 
            '${row.commodity}', 
            '${row.unit_price}', 
            '${row.quantity}', 
            '${row.amount}'
          )"
        >Edit</button>
        <button class="text-red-600 hover:underline" onclick="deleteRow(${row.id})">Delete</button>
      </td>
    `;
    tableBody.appendChild(tr);
  });

  offset += limit;
}

async function updateRecord(id, quantity, amount) {
  try {
    const response = await fetch(`/xnk/api/update?id=${id}&quantity=${quantity}&amount=${amount}`, {
      method: "PUT",
    });

    if (!response.ok) throw new Error("Failed to update");

    const row = document.getElementById(`row-${id}`);
    if (row) {
      row.children[12].textContent = quantity;
      row.children[13].textContent = amount;

      row.classList.add("bg-green-100");
      setTimeout(() => row.classList.remove("bg-green-100"), 800);
    }

    return true;
  } catch (error) {
    console.error("Update error:", error);
    alert("Failed to update record.");
    return false;
  }
}

// ✅ Form submission -> calls update_row()
document.getElementById("companyForm").addEventListener("submit", function(e) {
  e.preventDefault();
  update_row();
});

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 50) {
    loadMore();
  }
});

document.getElementById("monthSelect").addEventListener("change", async (e) => {
  const dateInput = e.target.value;
  if (!dateInput) return;

  selectedDate = dateInput;
  offset = 0;

  document.getElementById("data-table").innerHTML = "";
  await loadMore();
});

document.getElementById("load-more-btn").addEventListener("click", loadMore);

// Initial load
loadMore();
