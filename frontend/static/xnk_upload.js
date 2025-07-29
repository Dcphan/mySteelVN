
  const form = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const uploadButton = document.getElementById('uploadButton');
  const buttonText = document.getElementById('buttonText');
  const spinner = document.getElementById('spinner');
  const statusMessage = document.getElementById('statusMessage');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    // Set loading state
    uploadButton.disabled = true;
    spinner.classList.remove("hidden");
    buttonText.textContent = "Uploading...";
    statusMessage.textContent = "";

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/upload_excel_xnk", {
        method: "POST",
        body: formData
      });

      const result = await res.json();

      if (res.ok) {
        statusMessage.textContent = `✅ Upload successful. ${result.rows ?? ""}`;
        statusMessage.className = "text-green-600 text-sm mt-2 text-center font-medium";
      } else {
        throw new Error(result.detail || "Unknown error");
      }
    } catch (err) {
      statusMessage.textContent = `❌ Upload failed: ${err.message}`;
      statusMessage.className = "text-red-600 text-sm mt-2 text-center font-medium";
    } finally {
      // Reset UI
      uploadButton.disabled = false;
      spinner.classList.add("hidden");
      buttonText.textContent = "Upload File";
    }
  });

