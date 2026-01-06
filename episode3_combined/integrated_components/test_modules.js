// Test module imports directly
import { DataManager } from './core/DataManager.js';
import { TimelineViewer } from './TimelineViewer/TimelineViewer.js';
import { EVENTS } from './core/Events.js';

console.log('✅ All modules imported successfully');

// Test DataManager
const dataManager = new DataManager();
console.log('✅ DataManager created');

// Test TimelineViewer
const timelineViewer = new TimelineViewer(dataManager);
console.log('✅ TimelineViewer created');

// Test EVENTS
console.log('✅ Events available:', Object.keys(EVENTS));

console.log('🎉 All tests passed!');