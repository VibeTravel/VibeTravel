// =======================================
// Calls the backend POST /phase1/search
// =======================================
export async function searchLocations(payload) {
  const response = await fetch("http://127.0.0.1:8000/phase1/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return response.json(); // convert backend JSON → JS object
}
