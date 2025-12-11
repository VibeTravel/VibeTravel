// =======================================
// Calls the backend POST /phase3/create-itinerary
// =======================================
export async function createItinerary(payload) {
  const response = await fetch("http://127.0.0.1:8000/phase3/create-itinerary", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to create itinerary: ${response.statusText}`);
  }

  return response.json();
}
