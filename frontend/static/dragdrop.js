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


function drag_and_drop() {
  const zones = ['fieldZoneList', 'filterZone', 'rowZone', 'columnZone', 'valueZone'];

  zones.forEach(zoneId => {
    const el = document.getElementById(zoneId);
    if (!el) {
      console.warn(`Element with id "${zoneId}" not found.`);
      return;
    }

    Sortable.create(el, {
      group: 'shared', // All zones share the same group
      animation: 150,
      sort: true,
      ghostClass: 'bg-yellow-100',
      onAdd: (evt) => {
        const movedItem = evt.item.textContent.trim();
        const from = evt.from.id;
        const to = evt.to.id;

        console.log(`Moved "${movedItem}" from ${from} to ${to}`);
      }
    });
  });
}

// Initialize drag-and-drop when DOM is ready
document.addEventListener("DOMContentLoaded", drag_and_drop);
