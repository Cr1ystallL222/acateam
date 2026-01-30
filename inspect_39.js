const fs = require('fs');
const filePath = 'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx';
const content = fs.readFileSync(filePath, 'utf8');
const lines = content.split('\n');
console.log('Line 39:', lines[38].substring(0, 200) + ' ... ' + lines[38].substring(lines[38].length - 200));
