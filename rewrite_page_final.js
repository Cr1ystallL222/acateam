const fs = require('fs');
const filePath = 'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx';
try {
    const lines = fs.readFileSync(filePath, 'utf8').split('\n');

    // We want lines up to the one ending in '))}'
    // Let's find that line index to be sure.
    let mapEndIndex = -1;
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].trim() === '))}') {
            mapEndIndex = i;
            break;
        }
    }

    if (mapEndIndex === -1) {
        // Fallback or error
        console.log('Could not find map end line ))}. Using static index 41.');
        mapEndIndex = 41;
    }

    // slice(0, mapEndIndex + 1) includes the map end line.
    const head = lines.slice(0, mapEndIndex + 1).join('\n');

    // Correct tail:
    // </ul> to close list
    // 6 divs (inner)
    // </main>
    // 2 divs (outer)
    const tail = '      </ul></div></div></div></div></div></div></main></div></div>\n  );\n}\n';

    fs.writeFileSync(filePath, head + '\n' + tail);
    console.log('File rewritten FINAL successfully.');
} catch (e) {
    console.error(e);
}
