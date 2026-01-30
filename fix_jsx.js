const fs = require('fs');
const path = require('path');

const filePath = path.join('web', 'app', '(landing)', 'page.tsx');

try {
    let content = fs.readFileSync(filePath, 'utf8');

    // 1. Separate Imports/Logic from the Return Dump
    // We assume the dumped HTML is inside the return ( ... );
    // But given it's "Ctrl+S", maybe the user just pasted HTML replacing the whole return body?
    // Let's protect the top logic.

    const returnMatch = content.match(/return\s*\(/);
    if (!returnMatch) {
        console.log("No 'return (' found. Assuming full file needs fix or structure is different.");
        // Proceed with caution, maybe just processing the whole file except imports?
    }

    // We will process the whole file for JSX syntax, but be careful with imports/consts.
    // Actually, 'class=' in logic strings is rare, 'style=' in logic is rare.

    // PROTECT IMPORTS AND LOGIC?
    // If we blindly replace 'class=' it might break JS strings like "class='foo'".
    // However, in this specific task, the user pasted a "big HTML".
    // The structure from view_file lines 1-37 looks like manual code (clean).
    // The mess starts at line 37.

    const splitIndex = content.indexOf('return (');
    let header = "";
    let body = content;

    if (splitIndex !== -1) {
        header = content.substring(0, splitIndex + 8); // include "return ("
        body = content.substring(splitIndex + 8);
    }

    // FIXING BODY

    // 1. Comments: <!-- ... -->  =>  {/* ... */}
    // Handle multi-line comments too.
    body = body.replace(/<!--[\s\S]*?-->/g, match => {
        const start = match.indexOf('<!--') + 4;
        const end = match.lastIndexOf('-->');
        const text = match.substring(start, end);
        return `{/* ${text.replace(/\*/g, '')} */}`; // Avoid */ inside comment
    });

    // 2. class -> className
    // Regex looking for class="..." or class='...'
    body = body.replace(/\bclass=(["'])(.*?)\1/g, 'className=$1$2$1');

    // 3. for -> htmlFor
    body = body.replace(/\bfor=(["'])(.*?)\1/g, 'htmlFor=$1$2$1');

    // 4. style -> style={{...}}
    // This is complex. We find style="string".
    // Note: if it's already style={{...}}, we should skip.
    // The regex style=(["']) matches style="...".
    // But we need to ensure it's not style={{...}} (which doesn't start with quote usually, but JSX expression).
    // JSX style={{ is style={ { object } }.
    // HTML style=" is style="string".

    body = body.replace(/\bstyle=(["'])(.*?)\1/g, (match, quote, styleStr) => {
        // styleStr is "color: red; background: blue"
        const rules = styleStr.split(';').filter(r => r.trim());
        const props = rules.map(rule => {
            const [key, ...values] = rule.split(':');
            if (!key || values.length === 0) return '';

            let propKey = key.trim();
            // Convert camelCase
            propKey = propKey.replace(/-([a-z])/g, (g) => g[1].toUpperCase());

            let propVal = values.join(':').trim();
            // Escape quotes in value if needed
            propVal = propVal.replace(/"/g, '\\"');

            // Check if value is a number (px handling?)
            // React prefers strings for most things unless number.
            // Let's keep it string to be safe: "10px"
            return `"${propKey}": "${propVal}"`;
        }).filter(p => p);

        return `style={{ ${props.join(', ')} }}`;
    });

    // 5. Events: onclick -> onClick, etc.
    // User said "remove or adapt".
    // Removing is safest to pass build.
    body = body.replace(/\bon[a-z]+=(["'])(.*?)\1/g, '');

    // 6. Boolean attributes
    // autoplay -> autoPlay
    const boolAttrs = {
        'autoplay': 'autoPlay',
        'controlslist': 'controlsList',
        'crossorigin': 'crossOrigin',
        'playsinline': 'playsInline',
        'allowfullscreen': 'allowFullScreen',
        'frameborder': 'frameBorder',
        'itemprop': 'itemProp', // Microdata
        'itemscope': 'itemScope',
        'itemtype': 'itemType',
        'charset': 'charSet',
        'srcset': 'srcSet',
        'tabindex': 'tabIndex',
        'readonly': 'readOnly',
        'autocomplete': 'autoComplete',
        'autofocus': 'autoFocus',
        'novalidate': 'noValidate',
        'enctype': 'encType',
        'accept-charset': 'acceptCharset',
        'http-equiv': 'httpEquiv'
    };

    Object.keys(boolAttrs).forEach(attr => {
        const regex = new RegExp(`\\b${attr}=`, 'g');
        body = body.replace(regex, `${boolAttrs[attr]}=`);
        // Also handle boolean-only form: <video autoplay> -> <video autoPlay>
        // Regex: <tag ... autoplay ...>
        // This is hard to regex globally.
        // But we can try matching boundary: \sautoplay\s
        const regexBool = new RegExp(`\\s${attr}(\\s|/|>)`, 'g');
        body = body.replace(regexBool, ` ${boolAttrs[attr]}$1`);
    });

    // 7. Self-closing tags
    // List of void elements
    const voidTags = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'];

    // We need to ensure they end with />.
    // Regex: <tag ... > (without / before >)
    voidTags.forEach(tag => {
        // Regex matches <tag space ... > but NOT />
        // We look for <tag (attributes) >
        // [^>] matches any char except >.
        const regex = new RegExp(`<${tag}\\b([^>]*)(?<!/)>`, 'gi');
        body = body.replace(regex, `<${tag}$1 />`);
    });

    // 8. Remove script/style tags completely?
    // User didn't explicitly say remove, but "Parsing ecmascript source code failed" might be due to script tags with content.
    // Also inline styles are bad in React usually.
    // Let's comment them out or remove. Safest: Remove valid HTML scripts unrelated to React.
    // body = body.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '{/* Script removed */}');
    // body = body.replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, '{/* Style removed */}');

    // Actually, let's keep it safe. If there's a script tag, it might be the cause of "token" errors.
    body = body.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gmi, (match) => {
        return `{/* Script removed for safety */}`;
    });
    body = body.replace(/<style\b[^>]*>([\s\S]*?)<\/style>/gmi, (match) => {
        return `{/* Style removed for safety */}`;
    });

    // 9. Fix SVG standard attributes
    body = body.replace(/\bstroke-width=/g, 'strokeWidth=');
    body = body.replace(/\bstroke-linecap=/g, 'strokeLinecap=');
    body = body.replace(/\bstroke-linejoin=/g, 'strokeLinejoin=');
    body = body.replace(/\bfill-rule=/g, 'fillRule=');
    body = body.replace(/\bclip-rule=/g, 'clipRule=');
    body = body.replace(/\bstop-color=/g, 'stopColor=');
    body = body.replace(/\bstop-opacity=/g, 'stopOpacity=');

    // 10. Strange artifacts
    // "autoplay-settings" -> Remove or CamelCase? "autoplaySettings"
    body = body.replace(/\bautoplay-settings=/g, 'data-autoplay-settings=');

    // 11. next/image check
    // User said "NE use next/image".
    // So if there are <Image /> we should convert to <img>?
    // User said: "only ordinary <img>".
    // If we already have <img>, we are good.

    // 12. "Maps": "correctly close )} and add key"
    // This is hard to regex.
    // But usually this error comes from: { items.map(i => <div>...</div> }  (missing paren)
    // or { items.map(i => (<div>...</div> ) } (missing paren)
    // We can search for ".map("
    // But if the user Ctrl+S'd, there shouldn't be maps! 
    // UNLESS the user tried to fix it manually.
    // Let's assume for now we don't assume broken maps unless we see them.

    // 13. Remove <head>, <body>, <html> if they exist (usually bad for components)
    body = body.replace(/<\/?(html|head|body)\b[^>]*>/gi, '');

    // 14. Fix standard HTML entities in text?
    // &nbsp; is fine.

    // 15. Ensure root wrapper?
    // The user asked "One root element".
    // We can wrap the processed body in a Fragment if we aren't sure.
    // But if "layout-wrapper" is the root, we shouldn't wrap it again unnecessarily.
    // Let's check start/end.

    // Reconstruct
    let newContent = header + body;

    // Fix imports relative paths if broken? User didn't ask.

    fs.writeFileSync(filePath, newContent, 'utf8');
    console.log('Fixed page.tsx');

} catch (err) {
    console.error(err);
}
