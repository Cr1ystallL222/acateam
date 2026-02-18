const fs = require('fs');
const path = require('path');

const sourceBase = 'd:\\Codes\\4\\112\\nehuy\\3\\CopySite';
const destBase = 'd:\\Codes\\4\\112\\nehuy\\3\\web_cinema\\public';

const tasks = [
    {
        src: 'Афиша кино в Москве в кинотеатрах Мираж Синема_files',
        dest: 'main_files'
    },
    {
        src: 'Новинки кино и фильмы в прокате в Москве - Мираж Синема_files',
        dest: 'movies_files'
    }
];

tasks.forEach(task => {
    const srcPath = path.join(sourceBase, task.src);
    const destPath = path.join(destBase, task.dest);

    console.log(`Copying from "${srcPath}" to "${destPath}"...`);

    if (!fs.existsSync(srcPath)) {
        console.error(`Source directory not found: ${srcPath}`);
        return;
    }

    if (!fs.existsSync(destPath)) {
        try {
            fs.mkdirSync(destPath, { recursive: true });
        } catch (e) {
            console.error(`Error creating directory ${destPath}:`, e);
            return;
        }
    }

    try {
        // recursive copy manually to debug
        copyRecursiveSync(srcPath, destPath);
        console.log(`Successfully copied assets to ${task.dest}`);
    } catch (err) {
        console.error(`Error copying to ${task.dest}:`, err);
    }
});

function copyRecursiveSync(src, dest) {
    const exists = fs.existsSync(src);
    const stats = exists && fs.statSync(src);
    const isDirectory = exists && stats.isDirectory();

    if (isDirectory) {
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest);
        }
        fs.readdirSync(src).forEach(childItemName => {
            copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
        });
    } else {
        fs.copyFileSync(src, dest);
    }
}
