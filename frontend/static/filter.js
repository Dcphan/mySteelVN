function selector_function(companyData) {
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

  for (const [company, products] of Object.entries(companyData)) {
    const companyDiv = document.createElement("div");

    const header = document.createElement("div");
    header.textContent = "+ " + company;
    header.style.cursor = "pointer";

    const productList = document.createElement("div");
    productList.style.display = "none"

    products.forEach(({ product, id }) => {
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
      label.appendChild(document.createTextNode(" " + product));
      productList.appendChild(label);
      productList.appendChild(document.createElement("br"));
    });

    header.addEventListener("click", () => {
      const isVisible = productList.style.display === "block";
      productList.style.display = isVisible ? "none" : "block";
      header.textContent = (isVisible ? "+ " : "- ") + company;
    });

    companyDiv.appendChild(header);
    companyDiv.appendChild(productList);
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

function pie_selector_function(productData){
    const product_select = document.getElementById("product-select");
    for (const product of productData){
        const input = document.createElement("input");
        const label = document.createElement("label");
        input.type = "checkbox";
        input.id = product;
        input.value = product;
        console.log(input);
        label.textContent = product;
        label.htmlFor = product;
        console.log(label);
        product_select.appendChild(input);
        product_select.appendChild(label);
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



    