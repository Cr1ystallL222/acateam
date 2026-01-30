const fs = require('fs');
const path = require('path');

const filePath = path.join('d:', 'Codes', '4', '112', 'nehuy', '3', 'web', 'app', '(landing)', 'page.tsx');

try {
    let content = fs.readFileSync(filePath, 'utf8');

    // Check for movies.map
    const mapIndex = content.indexOf('movies.map');
    if (mapIndex !== -1) {
        // Find the </ul> following the map
        const closeUlIndex = content.indexOf('</ul>', mapIndex);
        if (closeUlIndex !== -1) {
            const startDelete = closeUlIndex + 5; // right after </ul>

            // Now find the end of the garbage.
            // We search for all matches of `data-index="..."` to find the last one.
            const regex = /data-index="(\d+)"/g;
            let match;
            let lastIndex = -1;
            let lastItemStart = -1;

            // scan specifically in the part AFTER the deletion point to rely on the static garbage
            const garbageContent = content.substring(startDelete);

            while ((match = regex.exec(garbageContent)) !== null) {
                lastIndex = parseInt(match[1]);
                lastItemStart = match.index; // relative to startDelete
            }

            if (lastIndex !== -1) {
                console.log(`Max data-index found in garbage: ${lastIndex}`);
                // Find the closing </li> for this last item.
                // We start searching from the start of this last item.
                // But list items might contain nested lists.
                // We should find the </li> that is followed by </ul>.

                // Let's look for `</ul>` appearing after the matching `data-index`.
                // The `</ul>` that closes the *main list* should follow the last item.
                // There might be nested `ul`s inside the last item? 
                // Unlikely for the last item to contain a nested list at the very end structure, but possible.

                // Let's find the FIRST `</ul>` after the start of the last item's `data-index` 
                // that brings the balance of `<ul>` and `</ul>` to -1 (closing the main)?
                // No, we are parsing a fragment.

                // Simpler: The main list closing `</ul>` is likely the one followed by the pagination or "Show more" or footer classes.
                // Let's peek at `</ul>` occurrences after the last item.

                const relativeLastItemStart = lastItemStart;
                const absoluteLastItemStart = startDelete + relativeLastItemStart;

                // Search for </ul> after this.
                // We might match unrelated </ul> if we go too far.
                // But the items are contiguous.

                // Let's assume the first `</ul>` after the last item is the one (unless the last item has nested list).
                // Let's check if there are nested <ul> in the last item.
                // scan from absoluteLastItemStart

                // Actually, I'll just look for the substring `</li></ul>` or `</li> </ul>` etc.
                // It's usually tight.

                const searchRegion = content.substring(absoluteLastItemStart);
                const listEndMatch = searchRegion.match(/<\/li>\s*<\/ul>/);

                if (listEndMatch) {
                    const relativeEnd = listEndMatch.index + listEndMatch[0].length;
                    const absoluteEnd = absoluteLastItemStart + relativeEnd;

                    console.log(`Identified end of list at: ${absoluteEnd}`);

                    // We need to delete from startDelete to absoluteEnd.
                    // IMPORTANT: We must ONLY delete the text.
                    // AND since we already have `</ul>` at `closeUlIndex`, we should INCLUDE the old `</ul>` in the deletion 
                    // (so we don't have double </ul>)
                    // Wait, `listEndMatch` matches `</li></ul>`. 
                    // `absoluteEnd` is matching the `...</ul>`.
                    // So if we delete up to `absoluteEnd`, we define the new content as:
                    // content(0..startDelete) + content(absoluteEnd..)
                    // `content(0..startDelete)` ends with `...</ul>` (my inserted one).
                    // `content(absoluteEnd..)` starts with whatever followed the old list.
                    // This creates `...</ul><div...` (next section).
                    // This seems correct!

                    const newContent = content.substring(0, startDelete) + content.substring(absoluteEnd);
                    console.log("Constructed new content length:", newContent.length);
                    fs.writeFileSync(filePath, newContent, 'utf8');
                    console.log("File patched successfully!");

                } else {
                    console.log("Could not find closing </li></ul> sequence.");
                }

            } else {
                console.log("No data-index found in garbage. Maybe simply cut until first </ul>?");
                // If there are no data-indexes, maybe it's just the tail of item 0?
                // Then finding the first `</ul>` might be correct.

                const nextUl = content.indexOf('</ul>', startDelete);
                if (nextUl !== -1) {
                    const absoluteEnd = nextUl + 5;
                    const newContent = content.substring(0, startDelete) + content.substring(absoluteEnd);
                    fs.writeFileSync(filePath, newContent, 'utf8');
                    console.log("File patched by simple cut to next </ul>.");
                } else {
                    console.log("No </ul> found.");
                }
            }

        } else {
            console.log("Could not find closing </ul> after map");
        }
    } else {
        console.log("movies.map not found");
    }

} catch (err) {
    console.error("Error:", err);
}
