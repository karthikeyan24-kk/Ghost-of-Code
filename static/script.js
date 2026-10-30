
document.addEventListener("DOMContentLoaded", () => {

    const storyForm = document.getElementById("storyForm");
    const generateBtn = document.getElementById("generateBtn");
    const loading = document.getElementById("loading");

    // Handle story generation
    storyForm.addEventListener("submit", () => {

        // Show loading animation
        loading.classList.add("active");

        // Disable the button to prevent repeated clicks
        generateBtn.disabled = true;

        // Change button text
        generateBtn.textContent = "👻 Summoning the Ghost...";

    });

});
