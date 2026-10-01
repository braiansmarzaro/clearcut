const dropZone = document.querySelector("#dropZone");
const fileInput = document.querySelector("#fileInput");
const resultPanel = document.querySelector("#resultPanel");
const resultImage = document.querySelector("#resultImage");
const processing = document.querySelector("#processing");
const fileName = document.querySelector("#fileName");
const errorMessage = document.querySelector("#errorMessage");
const downloadButton = document.querySelector("#downloadButton");
const resetButton = document.querySelector("#resetButton");

const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
const maxFileSize = 20 * 1024 * 1024;
let resultUrl = null;

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function reset() {
  if (resultUrl) URL.revokeObjectURL(resultUrl);
  resultUrl = null;
  fileInput.value = "";
  resultImage.removeAttribute("src");
  resultPanel.hidden = true;
  dropZone.hidden = false;
  errorMessage.hidden = true;
}

async function processImage(file) {
  errorMessage.hidden = true;

  if (!allowedTypes.includes(file.type)) {
    showError("Please choose a JPG, PNG, or WebP image.");
    return;
  }
  if (file.size > maxFileSize) {
    showError("Please choose an image smaller than 20 MB.");
    return;
  }

  dropZone.hidden = true;
  resultPanel.hidden = false;
  processing.hidden = false;
  downloadButton.setAttribute("aria-disabled", "true");
  fileName.textContent = file.name;

  try {
    const response = await fetch("/api/remove-background", {
      method: "POST",
      headers: { "Content-Type": file.type },
      body: file,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new Error(error?.detail || "Background removal failed.");
    }

    resultUrl = URL.createObjectURL(await response.blob());
    resultImage.src = resultUrl;
    downloadButton.href = resultUrl;
    downloadButton.removeAttribute("aria-disabled");
  } catch (error) {
    reset();
    showError(error.message);
  } finally {
    processing.hidden = true;
  }
}

dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    fileInput.click();
  }
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) processImage(fileInput.files[0]);
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file) processImage(file);
});

resetButton.addEventListener("click", reset);