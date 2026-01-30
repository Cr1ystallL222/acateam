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
    console.log(`First </ul> at ${ulClose1}`);

    // Look for the specific sequence
    const seq = '</ul></div></div><div';
    const seqIndex = content.indexOf(seq, ulClose1);

    console.log(`Sequence '${seq}' found at ${seqIndex}`);

    if (seqIndex !== -1) {
        const garbage = content.substring(ulClose1 + 5, seqIndex + 5);
        console.log(`Garbage length: ${garbage.length}`);
        console.log(`Garbage start: ${garbage.substring(0, 50)}...`);
        console.log(`Garbage end: ...${garbage.substring(garbage.length - 50)}`);
    } else {
        // Try weaker sequence
        const seq2 = '</ul></div></div>';
        const seqIndex2 = content.indexOf(seq2, ulClose1);
        console.log(`Sequence '${seq2}' found at ${seqIndex2}`);
    }

} catch (e) { console.error(e); }
