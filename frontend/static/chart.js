let myChartInstance = null;
let marketChartInstance = null;
let chartInstance = null;

function renderChart(data) {
    const cleanedDatasets = data.datasets.map(ds => ({
        label: ds.label,
        data: [...ds.data],
        borderColor: ds.borderColor,
        backgroundColor: ds.backgroundColor,
        yAxisID: "y"
    }));

    const ctx = document.getElementById("myChart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: cleanedDatasets
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left'
                }
            }
        }
    });
}

function loadAndRenderChart() {
  const container = document.getElementById("container"); 
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
  fetch(`/api/get_data?${queryParams.toString()}`)
    .then(res => {
      if (!res.ok) throw new Error(`Failed to fetch data: ${res.status}`);
      return res.json();
    })
    .then(data => {
      console.log("Fetched data:", data);
      // Use the data here (e.g., render chart)
      renderChart(data);

    })
    .catch(err => {
      console.error("Fetch error:", err);
      alert("Failed to fetch data. Please try again later.");
    });

}

async function loadMarketShare() {
    const month = document.getElementById("month").value;
    if (!month) {
        alert("Vui lòng chọn tháng!");
        return;
    }

    const checkboxes = document.querySelectorAll('.product-select input[type="checkbox"]:checked');
    if (checkboxes.length === 0) {
        alert("Vui lòng chọn ít nhất một sản phẩm!");
        return;
    }

    const productType = checkboxes[0].value;

    const response = await fetch(`/api/pie-market-share?product_type=${encodeURIComponent(productType)}&date=${month}`);
    if (!response.ok) {
        document.getElementById("text").textContent = "Lỗi khi gọi API";
        return;
    }

    const pieData = await response.json();
    const ctx = document.getElementById("myChart");

    if (marketChartInstance) {
        marketChartInstance.destroy();
    }

    marketChartInstance = new Chart(ctx, {
        type: "pie",
        data: {
            labels: pieData.labels,
            datasets: [{
                data: pieData.data,
                backgroundColor: [
                    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
                    "#9966FF", "#FF9F40", "#C9CBCF", "#66CC99"
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: `Market Share: ${productType} - ${month}`
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((acc, cur) => acc + cur, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });

    document.getElementById("text").textContent = "Chart updated successfully.";
}



window.loadMarketShare = loadMarketShare;
window.loadAndRenderChart = loadAndRenderChart;
