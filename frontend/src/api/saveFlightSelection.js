export async function saveFlightSelection(payload) {
  const response = await fetch("http://127.0.0.1:8000/itineraries/save-flight", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok || data.status !== "success") {
    const message = data?.detail || data?.error || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}
