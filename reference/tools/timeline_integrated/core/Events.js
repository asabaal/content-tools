// Standardized events all components must handle
export const EVENTS = {
    SEGMENT_UPDATED: 'segmentUpdated',
    SEGMENT_SELECTED: 'segmentSelected',
    WORD_TIMING_CHANGED: 'wordTimingChanged',
    TIMELINE_ZOOM_CHANGED: 'timelineZoomChanged',
    PLAYBACK_POSITION_CHANGED: 'playbackPositionChanged',
    DATA_LOADED: 'dataLoaded',
    DATA_EXPORTED: 'dataExported',
    DATA_IMPORTED: 'dataImported',
    TRANSCRIPT_CHANGED: 'transcriptChanged',
    BOUNDARY_DRAGGED: 'boundaryDragged',
    SEGMENT_CREATED: 'segmentCreated',
    SEGMENT_DELETED: 'segmentDeleted'
};

// Event utility functions
export function createEvent(type, data = null) {
    return {
        type,
        data,
        timestamp: Date.now()
    };
}

export function validateEventData(event, expectedData) {
    if (!event || !event.type) {
        throw new Error('Invalid event: missing type');
    }
    
    if (expectedData && !event.data) {
        throw new Error(`Invalid event: ${event.type} requires data`);
    }
    
    return true;
}