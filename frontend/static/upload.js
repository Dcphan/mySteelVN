 const input = document.getElementById('fileInput');
const list = document.getElementById('fileNames');

input.addEventListener('change', () => {
    list.innerHTML = '';  // Clear previous list
    const files = input.files;

    if (files.length === 0) {
        list.innerHTML = '<li>No files selected.</li>';
        return;
        }

        for (let i = 0; i < files.length; i++) {
            const name = files[i].name;
            const type = files[i].type || "Unknown format";
            const listItem = document.createElement('li');
            listItem.textContent = `${name} (${type})`;
            list.appendChild(listItem);
        }
    });