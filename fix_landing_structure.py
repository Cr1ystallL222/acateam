import re

file_path = r'd:/Codes/4/112/nehuy/3/web/app/(landing)/page.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the list that contains the static items.
# We look for the <ul ...> that immediately precedes the first list item <li data-index="0"
# This might be tricky if attributes are in different order, but let's look for the proximity.

# Search for the start of the first static item
start_marker = '<li data-index="0"'
start_idx = content.find(start_marker)

if start_idx == -1:
    print("Could not find statis list item 0")
    # It's possible I already partially replaced it.
    # Let's search for "movies.map" to see where it is.
    map_idx = content.find('movies.map')
    if map_idx != -1:
        print(f"Found movies.map at {map_idx}")
        # If map is found, we need to find the </ul> that follows it and what's between.
        # The error said: </ul><div ...
        # So we look for </ul> and see if there are <li> tags after it that are orphaned.
        
        # We want to find the closing </ul> for the map.
        # Then we want to see if we have junk after it.
        
        # Assumption: The </ul> closing the map is correct. The junk follows.
        # We need to find the END of the junk.
        # The junk consists of <li data-index="1">, <li data-index="2">... etc.
        # The LAST item in the original list was likely high index.
        # Or we simply look for the next distinct element that is NOT a list item.
        
        # Let's verify what follows the </ul>
        # Find the </ul> after movies.map
        ul_end_idx = content.find('</ul>', map_idx)
        if ul_end_idx != -1:
            print(f"Found </ul> after map at {ul_end_idx}")
            
            # Check what's after
            remainder = content[ul_end_idx+5:]
            # If it starts with <div ...></div></a>...</li> it's the junk.
            # We need to cut from ul_end_idx+5 until the end of the Last matching </li>?
            # Or rather, the list container <ul> closed at ul_end_idx.
            # If there are <li> tags AFTER this, they are the orphans.
            # We should probably delete everything from ul_end_idx+5 up to the start of the next VALID section.
            # What is the next valid section?
            # In the original HTML, after the recommendation list, there might be a "Show more" button or the footer.
            
            # Let's try to find the start of the next major component. 
            # Or better, just regex remove all <li data-index="...">...</li> occurrences that appear AFTER the map.
            
            # Let's locate the 'movies.map' injection site.
            # We want to keep the <ul>...{map}...</ul>
            # And Remove the <li data-index="0">...</li> <li data-index="1">...</li> following it?
            
            # Wait, if I injected movies.map, did I overwrite <li data-index="0">?
            # The error snippet shows:
            # 43 |       </ul><div ... </li><li data-index="1"...
            # This implies <li data-index="0"> might have been replaced (or the map replaces it), 
            # but <li data-index="1"> remains.
            
            pass
    else:
        print("movies.map not found")

# Let's try a different approach.
# We will identify the UL that contains the new dynamic logic.
# Then we will find the point where the static items END.
# And we will remove everything between the end of dynamic logic and end of static items.

# Find the UL opening.
# It likely has class="recommendation-item_features-list" OR the container of the cards.
# Looking at the snippet: <article className="recommendation-item ...">
# The LI wraps the article.
# Container is <ul ...>

# Let's assume the map marks the spot.
map_pattern = r'\{movies\.map\(.*?\)\}\s*</ul>'
match = re.search(map_pattern, content, re.DOTALL)

if match:
    print("Found map pattern")
    end_of_map_ul = match.end()
    print(f"End of map UL: {end_of_map_ul}")
    
    # After this point, we see junk.
    # We want to delete until we find something that ISN'T a list item from the old list.
    # The old list items all look like <li data-index="...">...</li>
    # But they might be nested.
    
    # We can try to finding the last </li> of the junk.
    # Or, finding the Next Element that works.
    
    # Let's look at what usually follows the list.
    # In many listings, it's the pagination or footer or closing divs.
    # <div class="...pagination..."> or just </div></div>
    
    # Let's just strip all text starting from end_of_map_ul that looks like static HTML list items.
    # We can regex replace `<li data-index="\d+".*?</li>` but that is dangerous with nesting.
    
    # Safest bet: proper parsing. But libraries might choke on JSX.
    
    # Heuristic:
    # content[end_of_map_ul:] contains the noise.
    # The noise starts immediately.
    # We can search for the first occurrence of a tag that is NOT part of the list item.
    # But the leftover starts with `<div...`. This div is likely *inside* the old LI 0 that got cut in half?
    # Snippet: `</ul><div className="flex ... ... </div></a>... `
    # This looks like the tail end of an article card.
    
    # Strategy: Find the start of the next valid siblings.
    # If the list was inside a container, maybe `</div></div>` follows.
    # Let's try to remove everything until `</main>` or a recognizable footer start?
    # No, that's too aggressive.
    
    # Let's inspect the `html_chunk.txt` or similar to see what comes AFTER the list.
    # I don't have it loaded.
    
    # Alternatives:
    # 1. Read the file again around the error point to see context.
    # 2. Slice the file.
    pass

