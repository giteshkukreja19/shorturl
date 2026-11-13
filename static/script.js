async function shortenURL() {
    const input = document.getElementById("urlInput");
    const button = document.getElementById("shortenBtn");
    const error = document.getElementById("errorMessage");
    const result = document.getElementById("result");
    const url = input.value.trim();

    error.textContent = "";
    result.classList.add("hidden");

    if (!url) {
        error.textContent = "Please enter a URL.";
        return;
    }

    button.disabled = true;
    button.textContent = "Creating...";

    try {
        const response = await fetch("/shorten", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        const shortURL = document.getElementById("shortURL");
        const qrImage = document.getElementById("qrImage");
        const downloadQR = document.getElementById("downloadQR");

        shortURL.textContent = data.short_url;
        shortURL.href = data.short_url;

        qrImage.src = data.qr_url;
        downloadQR.href = data.qr_url;

        result.classList.remove("hidden");
        loadDashboard();
    } catch (err) {
        error.textContent = err.message;
    } finally {
        button.disabled = false;
        button.textContent = "Shorten URL";
    }
}

async function copyURL() {
    const url = document.getElementById("shortURL").textContent;
    try {
        await navigator.clipboard.writeText(url);
        alert("Short URL copied successfully!");
    } catch {
        alert("Unable to copy. Please copy the link manually.");
    }
}

async function loadDashboard() {
    try {
        const response = await fetch("/api/links");
        if (!response.ok) throw new Error("Could not load dashboard.");

        const data = await response.json();
        document.getElementById("totalLinks").textContent = data.total_links;
        document.getElementById("totalClicks").textContent = data.total_clicks;

        const table = document.getElementById("linksTable");
        table.replaceChildren();

        if (data.links.length === 0) {
            const row = table.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 3;
            cell.textContent = "No links created yet.";
            return;
        }

        data.links.forEach(link => {
            const shortURL = link.short_url;
            const row = table.insertRow();

            const originalCell = row.insertCell();
            const shortCell = row.insertCell();
            const clicksCell = row.insertCell();

            const originalLink = document.createElement("a");
            originalLink.href = link.original_url;
            originalLink.textContent = link.original_url.length > 40
                ? link.original_url.substring(0, 40) + "..."
                : link.original_url;
            originalLink.target = "_blank";
            originalLink.rel = "noopener noreferrer";

            const shortLink = document.createElement("a");
            shortLink.href = shortURL;
            shortLink.textContent = shortURL;
            shortLink.target = "_blank";
            shortLink.rel = "noopener noreferrer";

            originalCell.appendChild(originalLink);
            shortCell.appendChild(shortLink);
            clicksCell.textContent = link.clicks;
        });
    } catch (error) {
        console.error("Dashboard error:", error);
    }
}

document.addEventListener("DOMContentLoaded", loadDashboard);
