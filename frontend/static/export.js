const exportFileNameInput = document.getElementById('exportFileName');
const downloadXLSXBtn = document.getElementById('downloadXLSXBtn');
const messageBox = document.getElementById('messageBox');
const loadingSpinner = document.getElementById('loadingSpinner');
const loadPreviewBtn = document.getElementById('loadPreviewBtn');
const previewLoadingSpinner = document.getElementById('previewLoadingSpinner');
const dataPreviewContent = document.getElementById('dataPreviewContent');

const BACKEND_EXCEL_URL = 'https://mysteelvn.onrender.com/export-excel';
const BACKEND_PREVIEW_URL = 'https://mysteelvn.onrender.com/get-all-pivot-data';

function showMessage(message, type = 'info') {
    messageBox.textContent = message;
    messageBox.className = '';
    messageBox.classList.add('block', 'rounded', 'mt-4', 'px-4', 'py-3');

    if (type === 'success') {
        messageBox.classList.add('bg-green-100', 'text-green-800');
    } else if (type === 'error') {
        messageBox.classList.add('bg-red-100', 'text-red-800');
    } else {
        messageBox.classList.add('bg-blue-100', 'text-blue-800');
    }

    setTimeout(() => {
        messageBox.classList.add('hidden');
    }, 5000);
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function renderTable(title, data) {
    if (!data || data.length === 0) {
        return `<div class="data-table-section"><h3 class="text-red-600">${title} (No data available)</h3></div>`;
    }

    const headers = Object.keys(data[0]);
    let html = `<div class="data-table-section"><h3>${title}</h3><div class="data-table-container"><table><thead><tr>`;
    headers.forEach(header => {
        html += `<th>${escapeHtml(header)}</th>`;
    });
    html += `</tr></thead><tbody>`;

    data.forEach(row => {
        html += `<tr>`;
        headers.forEach(header => {
            const value = row[header] !== null && row[header] !== undefined ? row[header].toString() : '';
            html += `<td>${escapeHtml(value)}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table></div></div>`;
    return html;
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

downloadXLSXBtn.addEventListener('click', async () => {
    let filename = exportFileNameInput.value.trim();
    if (!filename) filename = 'san_luong_report.xlsx';
    else if (!filename.endsWith('.xlsx')) filename += '.xlsx';

    loadingSpinner.classList.remove('hidden');
    downloadXLSXBtn.disabled = true;
    showMessage('Generating report... Please wait.');

    try {
        const res = await fetch(`${BACKEND_EXCEL_URL}?filename=${encodeURIComponent(filename)}`);
        if (res.ok) {
            const blob = await res.blob();
            downloadFile(blob, filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
            showMessage(`Excel report "${filename}" downloaded successfully!`, 'success');
        } else {
            const errorText = await res.text();
            showMessage(`Failed: ${res.statusText || errorText}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    } finally {
        loadingSpinner.classList.add('hidden');
        downloadXLSXBtn.disabled = false;
    }
});

loadPreviewBtn.addEventListener('click', async () => {
    dataPreviewContent.innerHTML = '';
    previewLoadingSpinner.classList.remove('hidden');
    loadPreviewBtn.disabled = true;
    showMessage('Fetching preview data...');

    try {
        const res = await fetch(BACKEND_PREVIEW_URL);
        if (res.ok) {
            const data = await res.json();
            let html = '';
            if (data.Inventory) html += renderTable('Inventory Data', data.Inventory);
            if (data.Production) html += renderTable('Production Data', data.Production);
            if (data.Export) html += renderTable('Export Data', data.Export);
            if (data.Domestic) html += renderTable('Domestic Data', data.Domestic);
            dataPreviewContent.innerHTML = html || '<p class="text-gray-600 italic">No data available</p>';
            showMessage('Preview loaded successfully!', 'success');
        } else {
            const err = await res.text();
            showMessage(`Error: ${res.statusText || err}`, 'error');
        }
    } catch (error) {
        showMessage(`Network error: ${error.message}`, 'error');
    } finally {
        previewLoadingSpinner.classList.add('hidden');
        loadPreviewBtn.disabled = false;
    }
});
