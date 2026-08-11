// Kiosk logic for the gate scanner page.
//
// A USB HID barcode/QR scanner behaves like a keyboard: it "types" the
// decoded token into whichever input is focused, then sends Enter. We
// keep #token-input focused at all times and submit it via fetch() to
// /gate/scan, then show the result and refocus for the next scan.

const form = document.getElementById("scan-form");
const input = document.getElementById("token-input");
const resultBox = document.getElementById("kiosk-result");
const resultText = document.getElementById("kiosk-result-text");

const RESULT_DISPLAY_MS = 3000;
let resetTimer = null;

function refocus() {
  input.value = "";
  input.focus();
}

function showResult(status, text) {
  resultBox.className = "kiosk-result kiosk-" + status;
  resultText.textContent = text;
  clearTimeout(resetTimer);
  resetTimer = setTimeout(() => {
    resultBox.className = "kiosk-result kiosk-idle";
    resultText.textContent = "Redo att scanna";
  }, RESULT_DISPLAY_MS);
}

async function submitToken(token) {
  if (!token) return;
  try {
    const response = await fetch("/gate/scan", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "token=" + encodeURIComponent(token) + "&source=gate-scanner",
    });
    const data = await response.json();
    if (data.status === "checked_in") {
      showResult("in", (data.child_name || "") + " incheckad ✓");
    } else if (data.status === "checked_out") {
      showResult("out", (data.child_name || "") + " utcheckad ✓");
    } else if (data.status === "debounced") {
      showResult("idle", data.message || "Redan registrerad");
    } else {
      showResult("error", data.message || "Okänt kort");
    }
  } catch (err) {
    showResult("error", "Kunde inte nå servern");
  } finally {
    refocus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitToken(input.value.trim());
});

document.addEventListener("click", refocus);
window.addEventListener("load", refocus);
