const fs = require('fs');
const filePath = 'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx';
const content = fs.readFileSync(filePath, 'utf8');
const lines = content.split('\n');
const headerLine = lines[38]; // Line 39

let openNoindex = 0;
const tagRegex = /<\/?(\w+)[^>]*>/g;
let match;

while ((match = tagRegex.exec(headerLine)) !== null) {
    const tagName = match[1];
    if (match[0].endsWith('/>')) continue;

    if (tagName === 'noindex') {
        const isClosing = match[0].startsWith('</');
        openNoindex += isClosing ? -1 : 1;
    }
}

console.log(`Open Noindex: ${openNoindex}`);
