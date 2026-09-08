const state = {
  originalBytes: null,
  processedBytes: null,
  sourceImage: null,
  outputImage: null,
  outputDataUrl: null,
  fileName: "signature",
  processing: false,
};

const $ = (id) => document.getElementById(id);
const fields = {
  name: $("name"),
  title: $("title"),
  phone: $("phone"),
  linkedin: $("linkedin"),
  photo: $("photo-input"),
  removeBackground: $("remove-bg"),
  zoom: $("zoom"),
  xOffset: $("x-offset"),
  yOffset: $("y-offset"),
  sharpness: $("sharpness"),
};

const htmlEscape = (value) => String(value).replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[character]));

function linkedinValue() {
  const value = fields.linkedin.value.trim();
  if (!value) return "https://www.linkedin.com/company/orbrick";
  return /^https?:\/\//i.test(value) ? value : `https://${value}`;
}

function signatureHtml(photoSource) {
  return `<table style="font-family:Tahoma, sans-serif; background: transparent !important; margin: 0; padding: 0;" width="360" cellpadding="0" cellspacing="0">
<tbody><tr>
<td style="width:140px; padding:0; text-align:center; vertical-align:middle;" valign="middle" width="140">
<img width="150" height="150" border="0" style="width:150px; height:150px; border:0; display:block; border-radius:0px;" src="${photoSource}">
</td>
<td style="padding:0; padding-left:20px; vertical-align:top;" valign="top">
<table style="font-family:Tahoma, sans-serif; background: transparent !important;" cellpadding="0" cellspacing="0" width="200">
<tbody><tr><td style="font-family:Tahoma, sans-serif; color:#ed5a24; padding-bottom:6px; vertical-align:top;" valign="top"><strong><span style="font-family:Tahoma, sans-serif; color:#5A2B86; font-size:14pt;">${htmlEscape(fields.name.value)}</span></strong><br><span style="font-family:Tahoma, sans-serif; color:#f08519; font-size:10pt; line-height:18px;">${htmlEscape(fields.title.value)}</span></td></tr>
<tr><td style="font-family:Tahoma, sans-serif; color:#5A2B86; padding-bottom:6px; line-height:18px; vertical-align:top;" valign="top"><span style="font-family:Tahoma, sans-serif; color:#5A2B86; font-size:10pt;"><b>M:</b> ${htmlEscape(fields.phone.value)}</span><br /></td></tr>
<tr><td style="font-family:Tahoma, sans-serif; color:#5A2B86; padding-bottom:6px; line-height:18px; vertical-align:top;" valign="top">
<a href="http://www.orbrick.com" target="_blank" rel="noopener" style="text-decoration:none;"><img src="https://orbrick.com/wp-content/uploads/2024/08/Main-logoTransparent.png" width="180" /></a><br /><br />
<span><a href="${htmlEscape(linkedinValue())}" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://orbrick.com/wp-content/uploads/2024/08/LinkedIn_logo_initials.png"></a></span>
<span><a href="https://www.orbrick.com/blog" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://orbrick.com/wp-content/uploads/2024/08/rss-round-color-icon-2.png"></a></span>
<span><a href="http://www.youtube.com/@TheOrbrickRoad" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://cdn1.iconfinder.com/data/icons/social-media-circle-6/1024/youtube-256.png"></a></span>
<span><a href="https://instagram.com" target="_blank" rel="noopener"><img border="0" width="26" style="border:0; height:26px; width:26px" src="https://cdn1.iconfinder.com/data/icons/social-media-circle-6/1024/instagram-256.png"></a></span><br />
</td></tr></tbody></table></td></tr></tbody></table>`;
}

function dataUrl(bytes) {
  let binary = "";
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  return `data:image/png;base64,${btoa(binary)}`;
}

function loadImage(bytes) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("The selected file is not a valid image."));
    image.src = URL.createObjectURL(new Blob([bytes]));
  });
}

async function removeBackground(bytes) {
  const response = await fetch("/remove-background", { method: "POST", body: (() => { const form = new FormData(); form.append("file", new Blob([bytes], { type: "image/png" }), "photo.png"); return form; })() });
  if (!response.ok) throw new Error((await response.text()) || `Background removal failed (${response.status}).`);
  return new Uint8Array(await response.arrayBuffer());
}

function showError(message) { $("error-message").textContent = message; $("error-message").hidden = !message; }
function setBusy(isBusy) {
  state.processing = isBusy;
  $("upload-title").textContent = isBusy ? "Removing background..." : (state.sourceImage ? "Photo ready" : "Upload a photo");
  $("upload-copy").textContent = isBusy ? "This may take a moment" : (state.sourceImage ? "Choose another image to replace it" : "PNG, JPG or JPEG up to 15 MB");
}

function updateRangeLabels() {
  $("zoom-value").textContent = `${Number(fields.zoom.value).toFixed(1)}x`;
  $("x-value").textContent = fields.xOffset.value;
  $("y-value").textContent = fields.yOffset.value;
  $("sharp-value").textContent = `${fields.sharpness.value}%`;
}

function applySharpen(canvas, percent) {
  if (percent <= 0) return;
  const context = canvas.getContext("2d");
  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  const source = imageData.data;
  const copy = new Uint8ClampedArray(source);
  const amount = percent / 100;
  const threshold = 3;
  const indexAt = (x, y, channel) => (y * canvas.width + x) * 4 + channel;
  for (let y = 1; y < canvas.height - 1; y += 1) for (let x = 1; x < canvas.width - 1; x += 1) {
    for (let channel = 0; channel < 3; channel += 1) {
      const center = copy[indexAt(x, y, channel)];
      const blurred = (copy[indexAt(x - 1, y, channel)] + copy[indexAt(x + 1, y, channel)] + copy[indexAt(x, y - 1, channel)] + copy[indexAt(x, y + 1, channel)] + center) / 5;
      const difference = center - blurred;
      if (Math.abs(difference) >= threshold) source[indexAt(x, y, channel)] = Math.max(0, Math.min(255, center + difference * amount));
    }
  }
  context.putImageData(imageData, 0, 0);
}

function renderOutput() {
  if (!state.processedBytes) return;
  const image = state.sourceImage;
  const width = image.naturalWidth;
  const height = image.naturalHeight;
  const alphaCanvas = document.createElement("canvas");
  alphaCanvas.width = width; alphaCanvas.height = height;
  const alphaContext = alphaCanvas.getContext("2d");
  alphaContext.drawImage(image, 0, 0);
  const pixels = alphaContext.getImageData(0, 0, width, height).data;
  let left = width, top = height, right = 0, bottom = 0;
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    if (pixels[(y * width + x) * 4 + 3] > 0) { left = Math.min(left, x); top = Math.min(top, y); right = Math.max(right, x + 1); bottom = Math.max(bottom, y + 1); }
  }
  if (right === 0) { left = 0; top = 0; right = width; bottom = height; }
  const foregroundWidth = right - left;
  const foregroundHeight = bottom - top;
  const foregroundSize = Math.max(foregroundWidth, foregroundHeight);
  const zoom = Number(fields.zoom.value);
  const cropSize = (foregroundSize * 1.15) / zoom;
  const centerX = (left + right) / 2 - Number(fields.xOffset.value);
  const centerY = (top + bottom) / 2 - Number(fields.yOffset.value);
  const output = document.createElement("canvas"); output.width = 300; output.height = 300;
  const context = output.getContext("2d");
  const sourceLeft = centerX - cropSize / 2;
  const sourceTop = centerY - cropSize / 2;
  context.imageSmoothingEnabled = true; context.imageSmoothingQuality = "high";
  context.drawImage(image, sourceLeft, sourceTop, cropSize, cropSize, 0, 0, 300, 300);
  applySharpen(output, Number(fields.sharpness.value));
  state.outputDataUrl = output.toDataURL("image/png");
  const signature = signatureHtml(state.outputDataUrl);
  $("signature-preview").innerHTML = signature;
  $("signature-preview").hidden = false;
  $("empty-preview").hidden = true;
  $("download-html").disabled = false;
  $("download-photo").disabled = false;
  $("copy-signature").disabled = false;
  state.outputImage = output;
}

async function handlePhoto(file) {
  if (!file) return;
  if (file.size > 15 * 1024 * 1024) { showError("Please choose an image smaller than 15 MB."); return; }
  showError(""); setBusy(true);
  try {
    state.fileName = (file.name || "signature").replace(/\.[^.]+$/, "").replace(/[^a-z0-9]+/gi, "_").toLowerCase();
    state.originalBytes = new Uint8Array(await file.arrayBuffer());
    const bytes = fields.removeBackground.checked ? await removeBackground(state.originalBytes) : state.originalBytes;
    state.processedBytes = bytes;
    state.sourceImage = await loadImage(bytes);
    const limit = Math.max(state.sourceImage.naturalWidth, state.sourceImage.naturalHeight) / 2;
    fields.xOffset.max = Math.floor(state.sourceImage.naturalWidth / 2); fields.xOffset.min = -fields.xOffset.max;
    fields.yOffset.max = Math.floor(state.sourceImage.naturalHeight / 2); fields.yOffset.min = -fields.yOffset.max;
    $("upload-zone").classList.add("has-file"); updateRangeLabels(); renderOutput();
  } catch (error) { showError(error.message || "Could not process this image."); }
  finally { setBusy(false); }
}

function download(content, name, type) {
  const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([content], { type })); link.download = name; link.click(); URL.revokeObjectURL(link.href);
}

function downloadDataUrl(dataUrl, name) {
  const link = document.createElement("a"); link.href = dataUrl; link.download = name; link.click();
}

fields.photo.addEventListener("change", () => handlePhoto(fields.photo.files[0]));
fields.removeBackground.addEventListener("change", () => { if (fields.photo.files[0]) handlePhoto(fields.photo.files[0]); });
[fields.name, fields.title, fields.phone, fields.linkedin].forEach((field) => field.addEventListener("input", () => { if (state.outputDataUrl) renderOutput(); }));
[fields.zoom, fields.xOffset, fields.yOffset, fields.sharpness].forEach((field) => field.addEventListener("input", () => { updateRangeLabels(); if (state.outputDataUrl) renderOutput(); }));
$("advanced-toggle").addEventListener("click", () => {
  const button = $("advanced-toggle");
  const panel = $("adjustments");
  const expanded = button.getAttribute("aria-expanded") === "true";
  button.setAttribute("aria-expanded", String(!expanded));
  panel.setAttribute("aria-hidden", String(expanded));
  panel.classList.toggle("is-open", !expanded);
  button.querySelector(".chevron").textContent = expanded ? "+" : "−";
});
$("download-photo").addEventListener("click", () => { if (state.outputDataUrl) downloadDataUrl(state.outputDataUrl, `photo_300x300_${state.fileName}.png`); });
$("download-html").addEventListener("click", () => { if (!state.outputDataUrl) return; const body = `<!DOCTYPE HTML><html><head><meta charset="utf-8"><title>Orbrick Email Signature</title></head><body style="font-size:10pt;font-family:Tahoma,sans-serif;margin:0;padding:0;">${signatureHtml(state.outputDataUrl)}</body></html>`; download(body, `orbrick_signature_${state.fileName}.html`, "text/html"); });
$("copy-signature").addEventListener("click", async () => {
  if (!state.outputDataUrl) return;
  const html = signatureHtml(state.outputDataUrl);
  try {
    if (navigator.clipboard && window.ClipboardItem) {
      await navigator.clipboard.write([new ClipboardItem({ "text/html": new Blob([html], { type: "text/html" }), "text/plain": new Blob([$("signature-preview").innerText], { type: "text/plain" }) })]);
    } else {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents($("signature-preview"));
      selection.removeAllRanges(); selection.addRange(range);
      document.execCommand("copy"); selection.removeAllRanges();
    }
    const button = $("copy-signature");
    button.querySelector("span").textContent = "Copied";
    setTimeout(() => { button.querySelector("span").textContent = "Copy signature"; }, 1600);
  } catch (error) {
    showError("Copy was blocked by the browser. Select the preview and press Ctrl+C.");
  }
});

updateRangeLabels();
$("signature-preview").hidden = true;
