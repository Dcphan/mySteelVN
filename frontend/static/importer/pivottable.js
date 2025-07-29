const zones = ['filters', 'columns', 'rows', 'values'];
    zones.forEach(id => new Sortable(document.getElementById(id), {
      group: 'shared', animation: 150,
      onEnd: () => runReport() // auto run when dragging ends
    }));

    const runReport = async () => {
      const getZoneFields = (id) => [...document.getElementById(id).children].map(el => el.textContent.trim());

      const data = {
        filters: getZoneFields('filters'),
        columns: getZoneFields('columns'),
        rows: getZoneFields('rows'),
        values: getZoneFields('values')
      };

      const res = await fetch('/api/run-pivot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      const result = await res.json();
      const container = document.getElementById('pivot-result');
      container.innerHTML = '';

      if (result.length > 0) {
        // Check if it's in detailed format (commodity → company → value)
        if ('commodity' in result[0] && 'company' in result[0]) {
          const grouped = {};
          result.forEach(({ commodity, company, total_quantity }) => {
            if (!grouped[commodity]) grouped[commodity] = [];
            grouped[commodity].push({ company, total_quantity });
          });

          Object.entries(grouped).forEach(([commodity, entries], idx) => {
            const section = document.createElement('div');
            section.className = 'mb-4';

            const toggle = document.createElement('button');
            toggle.textContent = `▼ ${commodity}`;
            toggle.className = 'font-bold text-left text-blue-600 hover:underline';

            const tableWrapper = document.createElement('div');
            tableWrapper.className = 'mt-2';

            const table = document.createElement('table');
            table.className = 'min-w-full border';
            const tbody = document.createElement('tbody');

            entries.forEach(({ company, total_quantity }) => {
              const tr = document.createElement('tr');
              const td1 = document.createElement('td');
              td1.className = 'border px-2 py-1';
              td1.textContent = company;
              const td2 = document.createElement('td');
              td2.className = 'border px-2 py-1 text-right';
              td2.textContent = total_quantity;
              tr.appendChild(td1);
              tr.appendChild(td2);
              tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            tableWrapper.appendChild(table);

            toggle.addEventListener('click', () => {
              tableWrapper.classList.toggle('hidden');
              toggle.textContent = tableWrapper.classList.contains('hidden') ? `► ${commodity}` : `▼ ${commodity}`;
            });

            section.appendChild(toggle);
            section.appendChild(tableWrapper);
            container.appendChild(section);
          });
        } else {
          const table = document.createElement('table');
          table.className = 'min-w-full border';

          const thead = document.createElement('thead');
          const headRow = document.createElement('tr');
          Object.keys(result[0]).forEach(key => {
            const th = document.createElement('th');
            th.className = 'border px-2 py-1 bg-gray-200';
            th.textContent = key;
            headRow.appendChild(th);
          });
          thead.appendChild(headRow);
          table.appendChild(thead);

          const tbody = document.createElement('tbody');
          result.forEach(row => {
            const tr = document.createElement('tr');
            Object.values(row).forEach(val => {
              const td = document.createElement('td');
              td.className = 'border px-2 py-1';
              td.textContent = val;
              tr.appendChild(td);
            });
            tbody.appendChild(tr);
          });
          table.appendChild(tbody);
          container.appendChild(table);
        }
      } else {
        container.innerHTML = '<p class="text-gray-600">No data found.</p>';
      }
    };

    document.getElementById('run-report').addEventListener('click', runReport);

    // Auto-add checkbox values to "Rows" zone
    document.querySelectorAll('.field-checkbox').forEach(cb => {
      cb.addEventListener('change', e => {
        if (e.target.checked) {
          const el = document.createElement('div');
          el.textContent = e.target.value;
          el.className = 'p-1 bg-white border rounded cursor-move text-sm mb-1';
          document.getElementById('rows').appendChild(el);
        } else {
          [...document.querySelectorAll('.zone div')].forEach(el => {
            if (el.textContent === e.target.value) el.remove();
          });
        }
        runReport();
      });
    });