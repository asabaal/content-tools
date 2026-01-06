// Simple test to check module loading
console.log('Testing module imports...');

// Test Events first
import('./core/Events.js')
  .then(events => {
    console.log('✅ Events loaded:', Object.keys(events.EVENTS));
    return import('./core/DataManager.js');
  })
  .then(dataManager => {
    console.log('✅ DataManager loaded');
    const { DataManager } = dataManager;
    const dm = new DataManager();
    console.log('✅ DataManager instance created');
    return import('./TimelineViewer/TimelineViewer.js');
  })
  .then(timelineViewer => {
    console.log('✅ TimelineViewer loaded');
    const { TimelineViewer } = timelineViewer;
    console.log('🎉 All modules loaded successfully!');
  })
  .catch(error => {
    console.error('❌ Error:', error);
  });