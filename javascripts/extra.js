document.addEventListener("DOMContentLoaded", function () {
    // Select all headers you want to be collapsible
    document.querySelectorAll("h2, h3, h4").forEach(header => {
        // Add a class for CSS styling and to identify them
        header.classList.add("collapsible-header");

        // Create the div that will hold the collapsible content
        const wrapper = document.createElement("div");
        wrapper.classList.add("collapsible-content");

        // Move all sibling elements into the wrapper until the next header of the same or higher level
        let next = header.nextElementSibling;
        while (next && !(next.tagName.match(/^H[1-4]$/) && next.tagName <= header.tagName))
        {
            const temp = next.nextElementSibling;
            wrapper.appendChild(next);
            next = temp;
        }

        // Insert the wrapper right after the header
        header.after(wrapper);

        // Add the click event listener to the header
        header.addEventListener("click", () => {
            // Toggle the 'active' class on the header for styling (e.g., rotating the arrow)
            header.classList.toggle("active");

            // Toggle the display of the content wrapper
            if (wrapper.style.display === "none" || wrapper.style.display === "")
            {
                wrapper.style.display = "block";
            } else
            {
                wrapper.style.display = "none";
            }
        });

        // Start with all content collapsed by default
        wrapper.style.display = "block"; // Changed from "none"
        header.classList.add("active");   // Add "active" class so it's bold initially
    });

    // apply landscape and portrait tags to grid-items
    document.querySelectorAll('.grid-item').forEach(item => {
        const img = item.querySelector('img');
        if (img)
        {
            const checkOrientation = () => {
                if (img.naturalWidth > img.naturalHeight)
                {
                    item.classList.add('landscape');
                } else
                {
                    item.classList.add('portrait');
                }
            };

            // Handle cached images
            if (img.complete)
            {
                checkOrientation();
            } else
            {
                img.onload = checkOrientation;
            }
        }
    });

    // Select all buttons with the class 'copy-link-button'
    const allCopyButtons = document.querySelectorAll('.copy-link-button');

    allCopyButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();

            const currentButton = event.currentTarget;
            let linkToCopy = currentButton.dataset.copyLink;

            if (linkToCopy === 'self') {
                linkToCopy = window.location.href;
            }
            if (!linkToCopy) return;

            try {
                await navigator.clipboard.writeText(linkToCopy);
                // Delegate all tooltip logic to our new function
                showTooltip(currentButton, "Copied link", 1000);

            } catch (err) {
                console.error('Failed to copy text: ', err);
                // You could even show an error tooltip!
                showTooltip(currentButton, "Failed!", 1000);
            }
        });
    });

    Fancybox.bind("[data-fancybox]", {
        Carousel: {
            Thumbs: {
                showOnStart: false,
            },
            Toolbar: {
                display: {
                    left: [
                        "counter",
                    ],
                    middle: [
                    ],
                    right: [
                        "rotateCCW",
                        "toggle1to1",
                        "download",
                        "close",
                    ],
                }
            }
        }
    });

    Fancybox.getDefaults().zoomEffect = false;
});

// A reusable function to show a temporary tooltip on an element
function showTooltip(button, message, duration = 2000) {
    const tooltip = button.querySelector('.tooltiptext');
    if (!tooltip) {
        console.warn("Button does not have a .tooltiptext child", button);
        return;
    }

    // 🔥 Clear any existing timer associated with this specific button
    if (button._tooltipTimer) {
        clearTimeout(button._tooltipTimer);
    }

    // Update tooltip content and show it
    tooltip.textContent = message;
    tooltip.classList.add("show");

    // Start a fresh timer to hide the tooltip
    button._tooltipTimer = setTimeout(() => {
        tooltip.classList.remove("show");
    }, duration);
}