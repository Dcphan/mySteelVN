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
        labels: data.labels, // Assumes full date/year strings like "2021", "2022", etc.
        datasets: cleanedDatasets // Ensure each has `label`, `data`, and optionally `borderColor`, etc.
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            title: {
                display: true,
                text: 'Sales Trends Over Time',
                font: {
                    size: 20
                },
                padding: {
                    top: 10,
                    bottom: 30
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.dataset.label || '';
                        const value = context.formattedValue;
                        return `${label}: ${value}`;
                    }
                }
            },
            legend: {
                position: 'top',
                labels: {
                    font: {
                        size: 12
                    },
                    usePointStyle: true
                }
            }
        },
        scales: {
            x: {
                type: 'category', // Can be 'time' if labels are dates (see note below)
                ticks: {
                    autoSkip: true,
                    maxRotation: 45,
                    minRotation: 0
                },
                title: {
                    display: true,
                    text: 'Year',
                    font: {
                        size: 14
                    }
                },
                grid: {
                    display: false
                }
            },
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Value',
                    font: {
                        size: 14
                    }
                },
                grid: {
                    color: '#f0f0f0'
                }
            }
        },
        elements: {
            line: {
                tension: 0.1, // Smooth bezier curve
                borderWidth: 2
            },
            point: {
                radius: 4,
                hoverRadius: 6,
                pointStyle: 'circle'
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

    const checkboxes = document.querySelectorAll('#product-select input[type="checkbox"]:checked');
    if (checkboxes.length === 0) {
        alert("Vui lòng chọn ít nhất một sản phẩm!");
        return;
    }

    const top_n = document.getElementById("top_n").value;
    const top_n_number = parseInt(top_n);

    if (isNaN(top_n_number) || top_n_number <= 0) {
        alert("Số lượng công ty phải là số hợp lệ lớn hơn 0.");
        return;
    }

    // Use only the first product (if single selection) — or loop through later if needed
    const productType = checkboxes[0].value;

    try {
        const response = await fetch(`/api/pie-market-share?top_n=${top_n_number}&product_type=${encodeURIComponent(productType)}&date=${month}`);
        if (!response.ok) throw new Error("Lỗi khi gọi API");

        const pieData = await response.json();

        if (!pieData || !pieData.labels || !pieData.data) {
            throw new Error("Dữ liệu trả về không hợp lệ.");
        }

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
                        "#9966FF", "#FF9F40", "#C9CBCF", "#66CC99",
                        "#C0392B", "#2980B9", "#27AE60", "#8E44AD"
                    ],
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                layout: {
                    padding: 20 // Prevents edge clipping when exporting as image
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Thị phần: ${productType} - ${month}`,
                        font: {
                            size: 20,
                            weight: 'bold'
                        },
                        padding: {
                            top: 10,
                            bottom: 20
                        }
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 14
                            },
                            padding: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.raw ?? 0;
                                const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                const percentage = total ? ((value / total) * 100).toFixed(1) : "0.0";
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        color: "#ffffff",
                        formatter: (value, context) => {
                            const label = context.chart.data.labels[context.dataIndex];
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}\n${value} (${percentage}%)`;
                        },
                        font: {
                            weight: 'bold',
                            size: 12
                        },
                        backgroundColor: "#000000cc",
                        borderRadius: 6,
                        padding: {
                            top: 4,
                            bottom: 4,
                            left: 6,
                            right: 6
                        },
                        display: 'auto',
                        align: 'center',
                        anchor: 'center',
                        clip: false
                    }
                }
            },
            plugins: [ChartDataLabels]
        });


        document.getElementById("text").textContent = "Biểu đồ đã được cập nhật.";
    } catch (error) {
        console.error(error);
        document.getElementById("text").textContent = error.message || "Đã xảy ra lỗi.";
    }
}


window.loadMarketShare = loadMarketShare;
window.loadAndRenderChart = loadAndRenderChart;
