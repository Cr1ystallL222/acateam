const fs = require('fs');
const path = require('path');

const htmlPath = "ClonAfish/Афиша Краснодара 2025-2026 - куда сходить в Краснодаре - мероприятия и события на сегодня, завтра, выходные _ 😋 KASSIR.RU.html";
const cssDest = "web/app/original.css";

try {
    const content = fs.readFileSync(htmlPath, 'utf-8');
    const startMarker = "<style>@font-face";
    const endMarker = "</style>";
    const startIdx = content.indexOf(startMarker);

    if (startIdx !== -1) {
        const endIdx = content.indexOf(endMarker, startIdx);
        if (endIdx !== -1) {
            // Find ALL content inside this style tag
            const cssContent = content.substring(startIdx + "<style>".length, endIdx);
            fs.writeFileSync(cssDest, cssContent.trim(), 'utf-8');
            console.log(`CSS extracted, size: ${cssContent.length} bytes`);
        } else {
            console.log("End style tag not found");
        }
    } else {
        console.log("Start style tag not found");
    }
} catch (e) {
    console.error("Error:", e);
}

// Check assets
const assetDest = "web/public/original";
try {
    const getAllFiles = function (dirPath, arrayOfFiles) {
        files = fs.readdirSync(dirPath)
        arrayOfFiles = arrayOfFiles || []
        files.forEach(function (file) {
            if (fs.statSync(dirPath + "/" + file).isDirectory()) {
                arrayOfFiles = getAllFiles(dirPath + "/" + file, arrayOfFiles)
            } else {
                arrayOfFiles.push(path.join(dirPath, "/", file))
            }
        })
        return arrayOfFiles
    }
    if (fs.existsSync(assetDest)) {
        const files = getAllFiles(assetDest);
        console.log(`Assets in ${assetDest}: ${files.length} items`);
    } else {
        console.log("Asset dest not found");
    }
} catch (e) {
    console.log("Error checking assets", e);
}
