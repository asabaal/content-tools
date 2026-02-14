// Simple validation test
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const testFile = join(__dirname, 'TimelineViewer', 'TimelineViewer.test.html');
const content = readFileSync(testFile, 'utf8');

console.log('Checking TimelineViewer test file...');

// Check for module script tag
if (content.includes('<script type="module">')) {
    console.log('✅ Has module script tag');
} else {
    console.log('❌ Missing module script tag');
}

// Check for imports
if (content.includes('import { DataManager }')) {
    console.log('✅ Has DataManager import');
} else {
    console.log('❌ Missing DataManager import');
}

if (content.includes('import { TimelineViewer }')) {
    console.log('✅ Has TimelineViewer import');
} else {
    console.log('❌ Missing TimelineViewer import');
}

if (content.includes('import { EVENTS }')) {
    console.log('✅ Has EVENTS import');
} else {
    console.log('❌ Missing EVENTS import');
}

// Check for key functions
if (content.includes('window.loadData')) {
    console.log('✅ Has loadData function');
} else {
    console.log('❌ Missing loadData function');
}

if (content.includes('window.testRendering')) {
    console.log('✅ Has testRendering function');
} else {
    console.log('❌ Missing testRendering function');
}

console.log('Validation complete');