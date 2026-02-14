// JavaScript validation script
const fs = require('fs');
const vm = require('vm');

// Read the HTML file and extract JavaScript
const htmlContent = fs.readFileSync('/home/asabaal/episode3_combined/timeline_timing_editor/timeline_word_timing_editor_complete.html', 'utf8');

// Extract JavaScript content between <script> tags
const scriptMatches = htmlContent.match(/<script[^>]*>([\s\S]*?)<\/script>/g);
if (!scriptMatches) {
    console.log('No script tags found');
    process.exit(0);
}

console.log('Found', scriptMatches.length, 'script tags');

scriptMatches.forEach((scriptTag, index) => {
    // Remove the script tags themselves
    const jsContent = scriptTag.replace(/<\/?script[^>]*>/g, '');
    
    // Skip external script references
    if (jsContent.trim().startsWith('src=')) {
        console.log(`Script ${index + 1}: External script - skipping`);
        return;
    }
    
    if (jsContent.trim() === '') {
        console.log(`Script ${index + 1}: Empty - skipping`);
        return;
    }
    
    try {
        new vm.Script(jsContent);
        console.log(`Script ${index + 1}: ✅ Syntax OK`);
    } catch (error) {
        console.log(`Script ${index + 1}: ❌ Syntax Error:`);
        console.log('Line:', error.lineNumber);
        console.log('Message:', error.message);
        console.log('Content preview:');
        console.log(jsContent.substring(0, 200) + '...');
    }
});

// Also validate the external data file
try {
    const dataContent = fs.readFileSync('/home/asabaal/episode3_combined/timeline_timing_editor/full_transcript_data.js', 'utf8');
    new vm.Script(dataContent);
    console.log('External data file: ✅ Syntax OK');
} catch (error) {
    console.log('External data file: ❌ Syntax Error:');
    console.log('Line:', error.lineNumber);
    console.log('Message:', error.message);
}