let tomSelectInstance = null;

function selectAllItems() {
  if (tomSelectInstance) {
    // Get all option values
    const allValues = Object.values(tomSelectInstance.options).map(option => option.value);
    tomSelectInstance.setValue(allValues); // Set all values
  }
  console.log("Click Select");
}

function deselectAllItems() {
  if (tomSelectInstance) {
    tomSelectInstance.clear(true); // Clear all selected values
  }
  console.log("Click Deselect");
}

function sortData(data, sortValue) {
  const totalRow = data.find(row => row.commodity === "TOTAL");
  const filteredData = data.filter(row => row.commodity !== "TOTAL");

  switch (sortValue) {
    case "amount-desc":
      filteredData.sort((a, b) => b.amount - a.amount);
      break;
    case "amount-asc":
      filteredData.sort((a, b) => a.amount - b.amount);
      break;
    case "quantity-desc":
      filteredData.sort((a, b) => b.quantity - a.quantity);
      break;
    case "quantity-asc":
      filteredData.sort((a, b) => a.quantity - b.quantity);
      break;
  }

  if (totalRow) filteredData.unshift(totalRow);
  return filteredData;
}