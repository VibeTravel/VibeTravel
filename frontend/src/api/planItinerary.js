// =======================================
// Calls the backend POST /phase2/plan
// =======================================
export async function planItinerary(payload) {
  const response = await fetch("http://127.0.0.1:8000/phase2/plan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to plan itinerary: ${response.statusText}`);
  }

  return response.json(); // convert backend JSON → JS object
}
