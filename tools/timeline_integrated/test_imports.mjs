// Test module imports
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('Testing module imports...');

try {
    // Test Events
    const eventsPath = join(__dirname, 'core', 'Events.js');
    console.log('Events path:', eventsPath);
    const { EVENTS } = await import(eventsPath);
    console.log('✅ Events loaded:', Object.keys(EVENTS).length, 'events');
    
    // Test DataManager
    const dataManagerPath = join(__dirname, 'core', 'DataManager.js');
    console.log('DataManager path:', dataManagerPath);
    const { DataManager } = await import(dataManagerPath);
    console.log('✅ DataManager loaded');
    
    // Test Component
    const componentPath = join(__dirname, 'core', 'Component.js');
    console.log('Component path:', componentPath);
    const { Component } = await import(componentPath);
    console.log('✅ Component loaded');
    
    // Test TimelineViewer
    const timelineViewerPath = join(__dirname, 'TimelineViewer', 'TimelineViewer.js');
    console.log('TimelineViewer path:', timelineViewerPath);
    const { TimelineViewer } = await import(timelineViewerPath);
    console.log('✅ TimelineViewer loaded');
    
    console.log('🎉 All modules loaded successfully!');
    
} catch (error) {
    console.error('❌ Error:', error.message);
    console.error('Stack:', error.stack);
}