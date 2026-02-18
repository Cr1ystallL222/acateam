const fs = require('fs');
const path = require('path');

async function copyAssets() {
    console.log('Starting asset copy...');

    // Define source directories relative to project root
    // Assuming script is run from project root: node scripts/copy_assets.js
    const projectRoot = process.cwd();
    const copySiteRoot = path.join(projectRoot, '..', 'CopySite');
    const publicRoot = path.join(projectRoot, 'public');

    // Mappings: Source Dir Name -> Target Dir Name in public
    const mappings = [
        { src: 'Грозовой перевал_files', dest: 'movies_files' },
        { src: 'Новинки кино и фильмы в прокате в Москве - Мираж Синема_files', dest: 'main_files' },
        { src: 'Афиша кино в Москве в кинотеатрах Мираж Синема_files', dest: 'main_files' } // Copy here too just in case
    ];

    for (const mapping of mappings) {
        const sourceDir = path.join(copySiteRoot, mapping.src);
        const destDir = path.join(publicRoot, mapping.dest);

        if (!fs.existsSync(sourceDir)) {
            console.warn(`Source directory not found: ${sourceDir}`);
            continue;
        }

        if (!fs.existsSync(destDir)) {
            fs.mkdirSync(destDir, { recursive: true });
            console.log(`Created directory: ${destDir}`);
        }

        const files = fs.readdirSync(sourceDir);
        for (const file of files) {
            // Filter for images
            if (file.endsWith('.jpg') || file.endsWith('.png') || file.endsWith('.svg')) {
                const srcFile = path.join(sourceDir, file);
                const destFile = path.join(destDir, file);

                try {
                    fs.copyFileSync(srcFile, destFile);
                    // console.log(`Copied: ${file}`);
                } catch (err) {
                    console.error(`Failed to copy ${file}:`, err);
                }
            }
        }
        console.log(`Finished copying from ${mapping.src} to ${mapping.dest}`);
    }
    console.log('All assets copied.');
}

copyAssets();
