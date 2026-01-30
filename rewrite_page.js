const fs = require('fs');
const filePath = 'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx';
try {
    const lines = fs.readFileSync(filePath, 'utf8').split('\n');
    const head = lines.slice(0, 42).join('\n');
    const tail = '      </ul></div></div></div></div></div></div></main></div></div></div>\n  );\n}\n';
    fs.writeFileSync(filePath, head + '\n' + tail);
    console.log('File rewritten successfully.');
} catch (e) {
    console.error(e);
}
