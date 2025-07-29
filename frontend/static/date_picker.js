const fp = flatpickr("#monthRange", {
      mode: "range",
      dateFormat: "Y-m",
      plugins: [
        new monthSelectPlugin({
          shorthand: true,
          dateFormat: "Y-m",
          altFormat: "F Y"
        })
      ]
    });

    function displayRange() {
      const rangeValue = document.getElementById("monthRange").value;
      const output = document.getElementById("output");
      output.innerHTML = "";

      if (rangeValue.includes(" to ")) {
        const [startStr, endStr] = rangeValue.split(" to ");
        const start = new Date(startStr + "-01");
        const end = new Date(endStr + "-01");
        const months = [];

        while (start <= end) {
          const y = start.getFullYear();
          const m = (start.getMonth() + 1).toString().padStart(2, '0');
          months.push(`${y}-${m}`);
          start.setMonth(start.getMonth() + 1);
        }

        output.innerHTML = `<strong>You selected:</strong> ${rangeValue}<br><ul>` +
          months.map(m => `<li>${m}</li>`).join("") +
          "</ul>";
      } else {
        output.textContent = `Please select a complete range.`;
      }
    }