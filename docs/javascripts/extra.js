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

    Fancybox.bind("[data-fancybox]", {
        Carousel: {
            Toolbar: {
                display: {
                    left: [
                        "counter",
                    ],
                    middle: [
                        "zoomIn",
                        "zoomOut",
                        "toggle1to1",
                        "rotateCCW",
                        "rotateCW",
                    ],
                    right: [
                        "thumbs",
                        "download",
                        "close",
                    ],
                }
            }
        }
    });

    Fancybox.getDefaults().zoomEffect = false;
});