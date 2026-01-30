const fs = require('fs');

const htmlPath = "ClonAfish/Афиша Краснодара 2025-2026 - куда сходить в Краснодаре - мероприятия и события на сегодня, завтра, выходные _ 😋 KASSIR.RU.html";

try {
    let content = fs.readFileSync(htmlPath, 'utf-8');

    // Extract body
    const bodyStart = content.indexOf("<body");
    const bodyEnd = content.indexOf("</body>");
    if (bodyStart === -1 || bodyEnd === -1) {
        console.log("Body not found");
        process.exit(1);
    }

    let bodyContent = content.substring(bodyStart, bodyEnd + 7);

    // Check for "recommendation-item" count
    const cardClass = "recommendation-item";
    const parts = bodyContent.split(cardClass);
    console.log(`Found ${parts.length - 1} occurrences of '${cardClass}'`);

    // Save a "pretty" version of body to inspect structure (simple replace for readability)
    // Be careful not to break text nodes, but for structural analysis >\n< is okayish.
    // Better: just save the segment containing the cards.

    if (parts.length > 1) {
        // Find the wrapper of these items.
        // It's likely a list or div.
        // We will save a chunk around the first occurrence to see the structure.
        const firstIdx = bodyContent.indexOf(cardClass);
        const chunk = bodyContent.substring(Math.max(0, firstIdx - 1000), Math.min(bodyContent.length, firstIdx + 2000));
        fs.writeFileSync("html_chunk.txt", chunk, 'utf-8');
        console.log("Saved html_chunk.txt");
    }

} catch (e) {
    console.error(e);
}
