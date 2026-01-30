const fs = require('fs');
const path = require('path');

const filePath = path.join('web', 'app', '(landing)', 'page.tsx');

try {
    let content = fs.readFileSync(filePath, 'utf8');

    // Replace <noindex>...</noindex> with <>...</> or just <div>
    // <noindex> is not valid JSX intrinsic element in default TS.
    content = content.replace(/<noindex>/g, '<div data-noindex="">');
    content = content.replace(/<\/noindex>/g, '</div>');

    // Clean [object Object] trash
    content = content.replace(/data-autoplay-settings="\[object Object\]"/g, 'data-autoplay-settings=""');

    // Ensure imports are not broken
    // (My previous script might have left some whitespace issues, but likely fine)

    fs.writeFileSync(filePath, content, 'utf8');
    console.log('Final cleanup page.tsx');

} catch (err) {
    console.error(err);
}
