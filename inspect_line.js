const fs = require('fs');
const path = require('path');

const filePath = path.join('d:', 'Codes', '4', '112', 'nehuy', '3', 'web', 'app', '(landing)', 'page.tsx');

try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    // lines are 0-indexed, so line 43 is at index 42.
    const line43 = lines[42];

    console.log(`Line 43 length: ${line43.length}`);

    // Check for common issues
    const issues = [];
    if (line43.includes('class=')) issues.push('Found "class="');
    if (line43.includes('style="')) issues.push('Found "style="" string');
    if (line43.match(/<br[^>]*[^/]>/)) issues.push('Found unclosed <br>');
    if (line43.match(/<img[^>]*[^/]>/)) issues.push('Found unclosed <img>');
    if (line43.match(/<input[^>]*[^/]>/)) issues.push('Found unclosed <input>');
    if (line43.match(/<hr[^>]*[^/]>/)) issues.push('Found unclosed <hr>');

    // Check for "Unknown regular expression flags" triggers
    // Often caused by unescaped / in text or bad comments.

    console.log('Issues found:', issues);

    // Save the line to a file so we can read it if needed (optional)
    fs.writeFileSync('d:/Codes/4/112/nehuy/3/line43_dump.txt', line43);

} catch (e) { console.error(e); }
