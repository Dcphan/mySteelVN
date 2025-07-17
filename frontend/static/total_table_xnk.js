let tomSelectInstance = null;
let barChartInstance = null;
let pieChartInstance = null;

// Step 1: Load commodity options from API
async function loadCommodities() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/commodity-options");
    const items = await res.json();
    console.log(items);
    const select = document.getElementById("itemSelect");
    select.innerHTML = ""; // clear

    items.forEach(item => {
      const opt = document.createElement("option");
      opt.value = item;
      opt.textContent = item;
      select.appendChild(opt);
    });

    if (tomSelectInstance) tomSelectInstance.destroy(); // re-init
    tomSelectInstance = new TomSelect("#itemSelect", {
      plugins: ['remove_button'],
      create: false,
      persist: false,
    });

  } catch (err) {
    console.error("Failed to load commodities:", err);
  }
}

async function fetchAndRenderTable() {
  const selected = Array.from(document.querySelector('#itemSelect').selectedOptions).map(o => o.value);
  if (selected.length === 0) {
    alert("Please select at least one commodity");
    return;
  }

  const date = document.getElementById("month").value;


  const url = new URL("http://127.0.0.1:8000/api/pivot-hscode-summary");
  url.searchParams.set("date", date);
  selected.forEach(item => url.searchParams.append("item", item));

  const res = await fetch(url);
  const data = await res.json();

  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = "";

  const labels = [];
  const amountData = [];
  const pieLabels = [];
  const pieData = [];

  data.forEach(row => {
    const isTotal = row.commodity === 'TOTAL';
    const tr = document.createElement("tr");
    tr.className = isTotal
      ? "bg-gray-500 text-white font-bold"
      : "hover:bg-gray-50";
    tr.innerHTML = `
      <td class="px-4 py-2">${row.commodity}</td>
      <td class="px-4 py-2 text-right">${Number(row.amount).toLocaleString()}</td>
      <td class="px-4 py-2 text-right">${Number(row.quantity).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
    `;
    tableBody.appendChild(tr);

    // For charts, skip TOTAL row
    if (!isTotal) {
      labels.push(row.commodity);
      amountData.push(row.amount);
      pieLabels.push(row.commodity);
      pieData.push(row.amount);
    }
  });

  // Destroy previous charts if exist
  if (barChartInstance) barChartInstance.destroy();
  if (pieChartInstance) pieChartInstance.destroy();

  // Bar Chart
  const barCtx = document.getElementById('barChart').getContext('2d');
  

  // Pie Chart
  const pieCtx = document.getElementById('pieChart').getContext('2d');
  barChartInstance = new Chart(barCtx, {
  type: 'bar',
  data: {
    labels: labels,
    datasets: [{
      label: 'Amount (USD)',
      data: amountData,
      backgroundColor: 'rgba(59, 130, 246, 0.6)', // Tailwind blue-500
      borderColor: 'rgba(37, 99, 235, 1)',         // Tailwind blue-600
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: {
        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString()}`
      }}
    },
    scales: {
      x: {
        ticks: {
          maxRotation: 45,
          minRotation: 0,
          autoSkip: true,
          font: { size: 10 }
        }
      },
      y: {
        beginAtZero: true,
        ticks: {
          font: { size: 10 },
          callback: value => value.toLocaleString()
        }
      }
    }
  }
});

pieChartInstance = new Chart(pieCtx, {
  type: 'pie',
  data: {
    labels: pieLabels,
    datasets: [{
      label: 'Market Share',
      data: pieData,
      backgroundColor: [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899',
        '#6366f1', '#14b8a6', '#f43f5e', '#84cc16'
      ],
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { font: { size: 10 } }
      },
      tooltip: { callbacks: {
        label: (ctx) => `${ctx.label}: ${ctx.raw.toLocaleString()}`
      }}
    }
  }
});


}


// Step 3: Initial load
loadCommodities();
