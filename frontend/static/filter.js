function selector_function(companyData) {
  console.log(companyData)
  const container = document.getElementById("container");
  const warning = document.getElementById("warning");
  const selectedList = document.getElementById("selectedList");

  let selectedCount = 0;
  const maxSelection = 4;

  function updateSelectedList() {
    const checkboxes = container.querySelectorAll("input[type='checkbox']:checked");
    
    checkboxes.forEach(cb => {
      const li = document.createElement("li");
      li.textContent = cb.value;
      console.log(cb.value)
    });
  }

  console.log("companyData:", companyData);

  for (const [product, companies] of Object.entries(companyData)) {
    const companyDiv = document.createElement("div");

    const header = document.createElement("div");
    header.textContent = "+ " + product;
    header.style.cursor = "pointer";

    const companyList = document.createElement("div");
    companyList.style.display = "none"

    companies.forEach(({ company, id }) => {
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = id;
      
      

      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          if (selectedCount >= maxSelection) {
            checkbox.checked = false;
            warning.style.display = "block";
            setTimeout(() => (warning.style.display = "none"), 2000);
          } else {
            selectedCount++;
            updateSelectedList();
          }
        } else {
          selectedCount--;
          updateSelectedList();
        }
      });

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(" " + company));
      companyList.appendChild(label);
      companyList.appendChild(document.createElement("br"));
    });

    header.addEventListener("click", () => {
      const isVisible = companyList.style.display === "block";
      companyList.style.display = isVisible ? "none" : "block";
      header.textContent = (isVisible ? "+ " : "- ") + product;
    });

    companyDiv.appendChild(header);
    companyDiv.appendChild(companyList);
    container.appendChild(companyDiv);
  }
}

 async function selector() {
      try {
        const res = await fetch("http://localhost:8000/api/product-data");
        if (!res.ok) throw new Error("Failed to fetch");

        const companyData = await res.json();
        selector_function(companyData); // Call your function with the data
      } catch (err) {
        console.error("Error fetching company data:", err);
      }
    }

function pie_selector_function(productData) {
    const product_select = document.getElementById("product-select");
    product_select.className = "grid grid-cols-2 sm:grid-cols-3 gap-4"; // Layout for parent container

    for (const product of productData) {
        // Create wrapper div
        const wrapper = document.createElement("div");
        wrapper.className = "flex items-center space-x-2";

        // Create checkbox input
        const input = document.createElement("input");
        input.type = "checkbox";
        input.id = product.replace(/\s+/g, '-').toLowerCase(); // make id safe
        input.value = product;
        input.className = "w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500";

        // Create label
        const label = document.createElement("label");
        label.textContent = product;
        label.htmlFor = input.id;
        label.className = "text-gray-700 text-sm";

        // Append input and label to wrapper
        wrapper.appendChild(input);
        wrapper.appendChild(label);

        // Append wrapper to container
        product_select.appendChild(wrapper);
    }
}


async function pie_selector() {
      try {
        const res = await fetch("http://localhost:8000/api/product-option");
        if (!res.ok) throw new Error("Failed to fetch");

        const data = await res.json();
        pie_selector_function(data); // Call your function with the data
      } catch (err) {
        console.error("Error fetching company data:", err);
      }
    }



    