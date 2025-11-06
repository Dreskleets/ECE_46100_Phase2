document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const response = await fetch("https://sm90vexhij.execute-api.us-east-2.amazonaws.com/Initial/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    console.log("Login response:", data);

    if (response.ok) {
      localStorage.setItem("user", JSON.stringify(data));
      window.location.href = "browse.html";
    } else {
      alert("Login failed: " + (data.message || "Unknown error"));
    }
  } catch (err) {
    console.error(err);
    alert("Network error while logging in");
  }
});
