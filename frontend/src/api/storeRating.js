// frontend/src/api/storeRating.js

export async function storeRating(ratingData) {
  const response = await fetch("http://127.0.0.1:8000/ratings/store", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(ratingData),
  });

  return response.json();
}

export async function getPreferredDestinations() {
  const response = await fetch("http://127.0.0.1:8000/ratings/preferred");
  return response.json();
}

export async function getAllRatings() {
  const response = await fetch("http://127.0.0.1:8000/ratings/all");
  return response.json();
}