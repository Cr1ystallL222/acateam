const fs = require('fs');
const filePath = 'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx';
try {
    const lines = fs.readFileSync(filePath, 'utf8').split('\n');
    // Keep lines 0-42 (inclusive, so length 43)
    const head = lines.slice(0, 43).join('\n');
    // Line 42 is "        ))}"

    // New tail: Close UL (1), Close Divs (6), Close Main (1).
    // Total Divs closed: 6. (Plus wrapper div from line 38?? We ignore it for now or assume it's one of the 8?)
    // If we need 9, and we close 6, we should get "Missing closing tag for div".
    const tail = '      </ul></div></div></div></div></div></div></main>\n  );\n}\n';

    fs.writeFileSync(filePath, head + '\n' + tail);
    console.log('File rewritten v2 successfully.');
} catch (e) {
    console.error(e);
}
