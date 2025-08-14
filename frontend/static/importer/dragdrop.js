import {fetchAndRenderTable, loadFilterOptions, loadRowOptions} from './summary.js'

let tomSelectInstance = null;

function getSelectedDate() {
    let dateInput = document.getElementById("date");
  
    return dateInput.value
        ? dateInput.value + "-01"
        : null; // null = all dates
}

function getSelectedFilters(){
    let filterSelect = document.getElementById("filterSelect");
    return filterSelect.value;
}

function getCurrentPivotConfig() {
  const getZoneFields = (zoneId) => { 
    const zone = document.getElementById(zoneId);
    return Array.from(zone.children).map(child => child.textContent.trim());
  };
  
  return {
    filters: getZoneFields('filterZone'),
    rows: getZoneFields('rowZone'),
    columns: getZoneFields('columnZone'),
    values: getZoneFields('valueZone')
  };
}

function changeFilterTable(){
    const filters = getCurrentPivotConfig().filters;
    const rows = getCurrentPivotConfig().rows;
    const columns = getCurrentPivotConfig().columns;
    const values = getCurrentPivotConfig().values;
    const filterInput = document.getElementById("filterInputs")
    const filterZoneDiv = document.createElement("div");
    const filterRowDiv = document.createElement("div");
    const tableHeader = document.getElementById("summary-table-header")
      if (!tableHeader) {
    console.error("Summary table elements not found in the DOM.");
    return;
  }


    filterInput.innerHTML = ""
    filterZoneDiv.innerHTML = "";
    filterRowDiv.innerHTML = "";
    tableHeader.innerHTML = "";

    console.log("ROWS: ",rows);
    console.log("FILTERS: ", filters);


    if (filters.length > 0){
        
        filterZoneDiv.className = "w-48"
        const label = document.createElement("label");
        const datalist = document.createElement("datalist");
        label.htmlFor = "filterSelect";
        label.textContent = filters[0];
        label.className = "block text-sm font-medium text-gray-700";
        
        const input = document.createElement("input");
        input.setAttribute("list", "filterOptions");
        input.id = "filterSelect";
        input.type = "text";
        input.className = "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500";
        datalist.id = "filterOptions";

        filterZoneDiv.appendChild(label);
        filterZoneDiv.appendChild(input);
        filterZoneDiv.appendChild(datalist);
    } 

    if (rows.length > 0) {
    filterRowDiv.className = "flex-1 min-w-[250px]";

    const label = document.createElement("label");
    const select = document.createElement("select");

    // Label setup
    label.htmlFor = "rowSelect";
    label.className = "block text-sm font-medium text-gray-700";
    label.textContent = rows[0];

    // Select setup
    select.id = "rowSelect";
    select.multiple = true;
    select.className = "mt-1 w-full";

    // OnChange event
    select.onchange = function () {
        const selectedRows = Array.from(select.selectedOptions).map(opt => opt.value);
        console.log("Selected rows:", selectedRows);
        fetchAndRenderTable(filters, rows, values); // <-- your function to update the table
    };


    // Append to container
    filterRowDiv.appendChild(label);
    filterRowDiv.appendChild(select);

    // DESIGN TABLE HEADER 
    for (const row of rows){
      const th = document.createElement("th");
      th.className = "px-4 py-2";
      th.textContent = row;
      tableHeader.append(th)
    }
    
}

    for (const value of values){
      const th = document.createElement("th");
      th.className = "px-4 py-2";
      th.textContent = value;
      tableHeader.append(th)
    }
    // Date Filter
    const dateDiv = document.createElement("div");
    dateDiv.className = "w-48";

    const dateLabel = document.createElement("label");
    dateLabel.htmlFor = "date";
    dateLabel.className = "block text-sm font-medium text-gray-700";
    dateLabel.textContent = "Date";

    const dateInput = document.createElement("input");
    dateInput.id = "date";
    dateInput.type = "month";
    dateInput.className = "mt-1 block w-full rounded-md border-gray-300 shadow-sm";

    // Append to the DOM
    dateDiv.appendChild(dateLabel);
    dateDiv.appendChild(dateInput);

    // Add all the feature to the filterInput Div

    const rowAndButtonWrapper = document.createElement("div");
    rowAndButtonWrapper.className = "w-full flex gap-4 items-end"; // full line, keeps row+button aligned

    rowAndButtonWrapper.appendChild(filterRowDiv);




    
    filterInput.appendChild(dateDiv);
    filterInput.appendChild(filterZoneDiv);
    filterInput.appendChild(filterRowDiv);

    // Run once when filter table is built
  loadRowOptions(rows[0], getSelectedDate());
  loadFilterOptions(filters[0], getSelectedDate());

  // Listen for date changes
  dateInput.addEventListener("change", () => {
      const selectedDate = getSelectedDate();
      console.log("Selected date:", selectedDate);

      loadFilterOptions(filters[0], selectedDate);
      loadRowOptions(rows[0], selectedDate);
      fetchAndRenderTable(filters, rows, values);
      
      console.log("Function is called");
  });

  filterSelect.addEventListener("change", () => {
      const selectedDate = getSelectedDate();
      const selectedFilters = getSelectedFilters();
      console.log(filters[0])
      console.log(selectedFilters);
      loadRowOptions(rows[0], selectedDate, filters[0],selectedFilters);
      console.log("Filter Input is Call")
  
    }
  );


}


function drag_and_drop() {
  const zones = ['fieldZoneList', 'filterZone', 'rowZone', 'columnZone', 'valueZone'];

  const allowedFields = {

    valueZone: ['amount', 'quantity'],
    fieldZoneList: ['commodity', 'company', 'quantity', 'amount', 'country']
  };

  const dropLimits = {
    filterZone: 1,
    rowZone: 2,
    columnZone: 1,
    valueZone: 2
  };

  // Show temporary error message
  function showError(zoneId, message) {
    const zone = document.getElementById(zoneId);
    if (!zone) return;

    const oldError = zone.querySelector('.drop-error');
    if (oldError) oldError.remove();

    const error = document.createElement('div');
    error.className = 'drop-error text-red-600 text-xs mt-1 animate-fade-in-out';
    error.textContent = message;

    zone.appendChild(error);
    setTimeout(() => error.remove(), 2000);
  }

  zones.forEach(zoneId => {
    const el = document.getElementById(zoneId);
    if (!el) {
      console.warn(`Element with id "${zoneId}" not found.`);
      return;
    }

    Sortable.create(el, {
      group: 'shared',
      animation: 200,
      ghostClass: 'bg-yellow-100',
      fallbackOnBody: true,
      swapThreshold: 0.65,

      onAdd: (evt) => {
        const movedItem = evt.item.textContent.trim();
        const from = evt.from.id;
        const to = evt.to.id;

        // Check limit first
        if (dropLimits[to] !== undefined && el.children.length > dropLimits[to]) {
          // Revert back
          evt.from.appendChild(evt.item);
          showError(to, `❌ Only ${dropLimits[to]} field${dropLimits[to] > 1 ? 's' : ''} allowed here`);
          return;
        }

        // Check allowed field type
        if (to !== 'fieldZoneList' && allowedFields[to] && !allowedFields[to].includes(movedItem)) {
          evt.from.appendChild(evt.item);
          showError(to, `❌ "${movedItem}" not allowed here`);
          return;
        }

        console.log(`Moved "${movedItem}" from ${from} to ${to}`);
      }
    });
  });
}


// Initialize drag-and-drop when DOM is ready
document.addEventListener("DOMContentLoaded", async () => {
  drag_and_drop();
});

 window.changeFilterTable = changeFilterTable;