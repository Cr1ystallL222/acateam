const fs = require('fs');
const filePath = 'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx';
const content = fs.readFileSync(filePath, 'utf8');
const lines = content.split('\n');
const headerLine = lines[38]; // Line 39

// Simple tag counter
let openDivs = 0;
let openMain = 0;
let openHeader = 0;
let openUl = 0;

// This is a naive regex parser, valid for this specific minified-like line
const tagRegex = /<\/?(\w+)[^>]*>/g;
let match;

while ((match = tagRegex.exec(headerLine)) !== null) {
    const isClosing = match[0].startsWith('</');
    const tagName = match[1];

    // Check for self-closing
    if (match[0].endsWith('/>') || match[0].endsWith(' />')) continue;
    if (['img', 'input', 'br', 'hr', 'source', 'meta', 'link', 'use', 'path', 'circle', 'rect'].includes(tagName)) continue;

    if (tagName === 'div') {
        openDivs += isClosing ? -1 : 1;
    } else if (tagName === 'main') {
        openMain += isClosing ? -1 : 1;
    } else if (tagName === 'header') {
        openHeader += isClosing ? -1 : 1;
    } else if (tagName === 'ul') {
        openUl += isClosing ? -1 : 1;
    }
}

console.log(`Open Divs: ${openDivs}`);
console.log(`Open Main: ${openMain}`);
console.log(`Open Header: ${openHeader}`);
console.log(`Open Ul: ${openUl}`);
