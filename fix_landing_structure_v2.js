const fs = require('fs');
const path = require('path');

const filePath = path.join('d:', 'Codes', '4', '112', 'nehuy', '3', 'web', 'app', '(landing)', 'page.tsx');

try {
    const content = fs.readFileSync(filePath, 'utf8');
    const mapIndex = content.indexOf('movies.map');

    if (mapIndex === -1) {
        console.log('movies.map not found');
        process.exit(1);
    }

    const ulClose1 = content.indexOf('</ul>', mapIndex);
    if (ulClose1 === -1) process.exit(1);

    const seq = '</ul></div></div><div';
    const seqIndex = content.indexOf(seq, ulClose1);

    if (seqIndex !== -1) {
        // We delete from ulClose1 + 5  UP TO seqIndex + 5
        // ulClose1 + 5 is where the garbage starts.
        // seqIndex is start of </ul></div>...
        // seqIndex + 5 is after </ul>.

        console.log(`Patching file... Removing content from ${ulClose1 + 5} to ${seqIndex + 5}`);

        const newContent = content.substring(0, ulClose1 + 5) + content.substring(seqIndex + 5);
        fs.writeFileSync(filePath, newContent, 'utf8');
        console.log('File patched successfully.');
    } else {
        console.log('Target sequence not found.');
    }

} catch (e) { console.error(e); }
