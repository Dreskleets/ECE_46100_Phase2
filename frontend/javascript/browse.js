async function loadModels() {
  try {
    const res = await fetch("https://sm90vexhij.execute-api.us-east-2.amazonaws.com/Initial/models");
    const models = await res.json();

    const container = document.getElementById("modelList");
    container.innerHTML = "";

    if (models.length === 0) {
      container.innerHTML = "<p>No models found.</p>";
      return;
    }

    models.forEach((model) => {
      const card = document.createElement("div");
      card.className = "col-md-4 mb-3";
      card.innerHTML = `
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5>${model.name}</h5>
            <h6 class="text-muted">${model.category}</h6>
            <p>${model.description}</p>
            <p class="text-warning mb-0">⭐ ${model.avg_rating}</p>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load models:", err);
    document.getElementById("modelList").innerHTML =
      "<p>Error loading models.</p>";
  }
}

loadModels();
