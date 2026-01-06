import { EVENTS, createEvent, validateEventData } from './Events.js';

export class DataManager {
    constructor() {
        this.segments = [];
        this.metadata = {};
        this.eventListeners = new Map();
        this.isLoaded = false;
        this.dataFilePath = './combined_transcript.json';
        
        // Performance optimization
        this.segmentCache = new Map();
        this.wordCache = new Map();
        this.lastModified = null;
    }
    
    // Load data from JSON file
    async loadData(filePath = null) {
        try {
            const dataPath = filePath || this.dataFilePath;
            console.log(`Loading data from: ${dataPath}`);
            
            const response = await fetch(dataPath);
            if (!response.ok) {
                throw new Error(`Failed to load data: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Validate data structure
            this.validateDataStructure(data);
            
            // Load data into manager
            this.segments = data.segments || [];
            this.metadata = data.metadata || {};
            this.isLoaded = true;
            this.lastModified = new Date();
            
            // Clear caches
            this.clearCaches();
            
            // Emit data loaded event
            this.emit(EVENTS.DATA_LOADED, {
                segments: this.segments.length,
                duration: this.metadata.duration,
                source: dataPath
            });
            
            console.log(`Loaded ${this.segments.length} segments, duration: ${this.metadata.duration}s`);
            return data;
            
        } catch (error) {
            console.error('Failed to load data:', error);
            throw error;
        }
    }
    
    // Validate data structure
    validateDataStructure(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: must be an object');
        }
        
        if (!Array.isArray(data.segments)) {
            throw new Error('Invalid data: segments must be an array');
        }
        
        // Validate each segment
        data.segments.forEach((segment, index) => {
            if (!segment.text || typeof segment.text !== 'string') {
                throw new Error(`Invalid segment ${index}: missing or invalid text`);
            }
            
            if (typeof segment.start !== 'number' || typeof segment.end !== 'number') {
                throw new Error(`Invalid segment ${index}: missing or invalid start/end times`);
            }
            
            if (segment.start >= segment.end) {
                throw new Error(`Invalid segment ${index}: start time must be less than end time`);
            }
            
            // Validate words if present
            if (segment.words && Array.isArray(segment.words)) {
                segment.words.forEach((word, wordIndex) => {
                    if (!word.text || typeof word.text !== 'string') {
                        throw new Error(`Invalid word ${wordIndex} in segment ${index}: missing text`);
                    }
                    
                    if (typeof word.start !== 'number' || typeof word.end !== 'number') {
                        throw new Error(`Invalid word ${wordIndex} in segment ${index}: missing timing`);
                    }
                });
            }
        });
    }
    
    // Clear all caches
    clearCaches() {
        this.segmentCache.clear();
        this.wordCache.clear();
    }
    
    // Get all segments
    getSegments() {
        return [...this.segments];
    }
    
    // Get segment by ID
    getSegment(id) {
        if (this.segmentCache.has(id)) {
            return this.segmentCache.get(id);
        }
        
        const segment = this.segments.find(s => 
            s.id === id || s.segment_id === id || s.id === parseInt(id)
        );
        
        if (segment) {
            this.segmentCache.set(id, { ...segment });
        }
        
        return segment;
    }
    
    // Get segments in time range
    getSegmentsInTimeRange(startTime, endTime) {
        return this.segments.filter(segment => 
            segment.start < endTime && segment.end > startTime
        );
    }
    
    // Get segment at specific time
    getSegmentAtTime(time) {
        return this.segments.find(segment => 
            time >= segment.start && time <= segment.end
        );
    }
    
    // Update segment
    updateSegment(id, changes) {
        const segmentIndex = this.segments.findIndex(s => 
            s.id === id || s.segment_id === id || s.id === parseInt(id)
        );
        
        if (segmentIndex === -1) {
            throw new Error(`Segment ${id} not found`);
        }
        
        const oldSegment = { ...this.segments[segmentIndex] };
        const newSegment = { ...this.segments[segmentIndex], ...changes };
        
        // Validate changes
        this.validateSegmentChanges(newSegment, changes);
        
        // Update segment
        this.segments[segmentIndex] = newSegment;
        
        // Clear cache
        this.segmentCache.delete(id);
        
        // Emit update event
        this.emit(EVENTS.SEGMENT_UPDATED, {
            segmentId: id,
            oldSegment,
            newSegment,
            changes
        });
        
        return newSegment;
    }
    
    // Validate segment changes
    validateSegmentChanges(segment, changes) {
        if (changes.start !== undefined || changes.end !== undefined) {
            if (segment.start >= segment.end) {
                throw new Error('Invalid timing: start must be less than end');
            }
            
            // Check for overlaps with other segments
            const overlappingSegments = this.segments.filter(s => 
                s.id !== segment.id && 
                s.segment_id !== segment.id &&
                s.start < segment.end && 
                s.end > segment.start
            );
            
            if (overlappingSegments.length > 0) {
                console.warn('Segment timing overlaps with other segments:', overlappingSegments);
            }
        }
    }
    
    // Redistribute word timings within a segment
    redistributeWords(segmentId, mode = 'proportional') {
        const segment = this.getSegment(segmentId);
        if (!segment || !segment.words || segment.words.length === 0) {
            return segment;
        }
        
        const duration = segment.end - segment.start;
        const oldWords = [...segment.words];
        
        let newWords;
        
        switch (mode) {
            case 'uniform':
                newWords = this.redistributeUniform(segment.words, segment.start, segment.end);
                break;
            case 'proportional':
                newWords = this.redistributeProportional(segment.words, segment.start, segment.end);
                break;
            case 'preserve-gaps':
                newWords = this.redistributePreserveGaps(segment.words, segment.start, segment.end);
                break;
            default:
                throw new Error(`Unknown redistribution mode: ${mode}`);
        }
        
        // Update segment
        const updatedSegment = this.updateSegment(segmentId, { words: newWords });
        
        // Emit word timing changed event
        this.emit(EVENTS.WORD_TIMING_CHANGED, {
            segmentId,
            oldWords,
            newWords,
            mode,
            duration
        });
        
        return updatedSegment;
    }
    
    // Uniform word redistribution
    redistributeUniform(words, startTime, endTime) {
        const duration = endTime - startTime;
        const wordDuration = duration / words.length;
        
        return words.map((word, index) => ({
            ...word,
            start: startTime + (index * wordDuration),
            end: startTime + ((index + 1) * wordDuration)
        }));
    }
    
    // Proportional word redistribution
    redistributeProportional(words, startTime, endTime) {
        const originalDuration = words[words.length - 1].end - words[0].start;
        const newDuration = endTime - startTime;
        const scaleFactor = newDuration / originalDuration;
        const originalStart = words[0].start;
        
        return words.map(word => ({
            ...word,
            start: startTime + ((word.start - originalStart) * scaleFactor),
            end: startTime + ((word.end - originalStart) * scaleFactor)
        }));
    }
    
    // Preserve gaps word redistribution
    redistributePreserveGaps(words, startTime, endTime) {
        const originalDuration = words[words.length - 1].end - words[0].start;
        const newDuration = endTime - startTime;
        const scaleFactor = newDuration / originalDuration;
        
        // Calculate word durations and gaps
        const wordDurations = words.map(word => word.end - word.start);
        const gaps = [];
        for (let i = 1; i < words.length; i++) {
            gaps.push(words[i].start - words[i-1].end);
        }
        
        // Scale word durations but preserve gap proportions
        const totalWordTime = wordDurations.reduce((sum, duration) => sum + duration, 0);
        const totalGapTime = gaps.reduce((sum, gap) => sum + gap, 0);
        
        const newTotalWordTime = totalWordTime * scaleFactor;
        const newTotalGapTime = totalGapTime * scaleFactor;
        
        const scaledWordDurations = wordDurations.map(duration => 
            (duration / totalWordTime) * newTotalWordTime
        );
        const scaledGaps = gaps.map(gap => 
            (gap / totalGapTime) * newTotalGapTime
        );
        
        // Reconstruct words with new timing
        const redistributedWords = [];
        let currentTime = startTime;
        
        for (let i = 0; i < words.length; i++) {
            const newWordEnd = currentTime + scaledWordDurations[i];
            redistributedWords.push({
                ...words[i],
                start: currentTime,
                end: newWordEnd
            });
            currentTime = newWordEnd;
            
            if (i < scaledGaps.length) {
                currentTime += scaledGaps[i];
            }
        }
        
        return redistributedWords;
    }
    
    // Update transcript text
    updateTranscript(segmentId, newText) {
        const segment = this.getSegment(segmentId);
        if (!segment) {
            throw new Error(`Segment ${segmentId} not found`);
        }
        
        const oldText = segment.text;
        
        // Update segment text
        const updatedSegment = this.updateSegment(segmentId, { text: newText });
        
        // Redistribute word timings if words exist
        if (updatedSegment.words && updatedSegment.words.length > 0) {
            this.redistributeWords(segmentId, 'uniform');
        }
        
        // Emit transcript changed event
        this.emit(EVENTS.TRANSCRIPT_CHANGED, {
            segmentId,
            oldText,
            newText
        });
        
        return updatedSegment;
    }
    
    // Create new segment
    createSegment(segmentData) {
        const newSegment = {
            id: `segment_${Date.now()}`,
            text: '',
            start: 0,
            end: 1,
            words: [],
            ...segmentData
        };
        
        // Validate new segment
        this.validateSegmentChanges(newSegment, segmentData);
        
        // Add to segments array
        this.segments.push(newSegment);
        
        // Clear cache
        this.clearCaches();
        
        // Emit segment created event
        this.emit(EVENTS.SEGMENT_CREATED, {
            segment: newSegment
        });
        
        return newSegment;
    }
    
    // Delete segment
    deleteSegment(segmentId) {
        const segmentIndex = this.segments.findIndex(s => 
            s.id === segmentId || s.segment_id === segmentId || s.id === parseInt(id)
        );
        
        if (segmentIndex === -1) {
            throw new Error(`Segment ${segmentId} not found`);
        }
        
        const deletedSegment = this.segments.splice(segmentIndex, 1)[0];
        
        // Clear cache
        this.clearCaches();
        
        // Emit segment deleted event
        this.emit(EVENTS.SEGMENT_DELETED, {
            segmentId,
            segment: deletedSegment
        });
        
        return deletedSegment;
    }
    
    // Export data
    exportData(format = 'json') {
        const data = {
            segments: this.segments,
            metadata: {
                ...this.metadata,
                exported: new Date().toISOString(),
                segmentCount: this.segments.length
            }
        };
        
        switch (format) {
            case 'json':
                return JSON.stringify(data, null, 2);
            case 'csv':
                return this.exportToCSV(data);
            case 'srt':
                return this.exportToSRT(data);
            case 'vtt':
                return this.exportToVTT(data);
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }
    
    // Export to CSV
    exportToCSV(data) {
        const headers = ['ID', 'Start Time', 'End Time', 'Duration', 'Text', 'Word Count'];
        const rows = data.segments.map(segment => [
            segment.id || segment.segment_id || '',
            segment.start.toFixed(3),
            segment.end.toFixed(3),
            (segment.end - segment.start).toFixed(3),
            `"${segment.text.replace(/"/g, '""')}"`,
            segment.words ? segment.words.length : 0
        ]);
        
        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }
    
    // Export to SRT
    exportToSRT(data) {
        return data.segments.map((segment, index) => {
            const startTime = this.formatSRTTime(segment.start);
            const endTime = this.formatSRTTime(segment.end);
            return `${index + 1}\n${startTime} --> ${endTime}\n${segment.text}\n`;
        }).join('\n');
    }
    
    // Export to VTT
    exportToVTT(data) {
        let vtt = 'WEBVTT\n\n';
        vtt += data.segments.map(segment => {
            const startTime = this.formatVTTTime(segment.start);
            const endTime = this.formatVTTTime(segment.end);
            return `${startTime} --> ${endTime}\n${segment.text}\n`;
        }).join('\n');
        return vtt;
    }
    
    // Format time for SRT
    formatSRTTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
    }
    
    // Format time for VTT
    formatVTTTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }
    
    // Get metadata
    getMetadata() {
        return { ...this.metadata };
    }
    
    // Get statistics
    getStatistics() {
        const totalDuration = Math.max(...this.segments.map(s => s.end), 0);
        const totalWords = this.segments.reduce((sum, s) => 
            sum + (s.words ? s.words.length : s.text.split(' ').length), 0
        );
        const avgSegmentDuration = this.segments.length > 0 
            ? this.segments.reduce((sum, s) => sum + (s.end - s.start), 0) / this.segments.length 
            : 0;
        
        return {
            segmentCount: this.segments.length,
            totalDuration,
            totalWords,
            avgSegmentDuration,
            wordsPerSegment: this.segments.length > 0 ? totalWords / this.segments.length : 0,
            isLoaded: this.isLoaded,
            lastModified: this.lastModified
        };
    }
    
    // Event system methods
    on(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, new Set());
        }
        this.eventListeners.get(eventType).add(callback);
    }
    
    off(eventType, callback) {
        if (this.eventListeners.has(eventType)) {
            this.eventListeners.get(eventType).delete(callback);
        }
    }
    
    emit(eventType, data) {
        const event = createEvent(eventType, data);
        
        if (this.eventListeners.has(eventType)) {
            this.eventListeners.get(eventType).forEach(callback => {
                try {
                    callback(event);
                } catch (error) {
                    console.error(`Error in event listener for ${eventType}:`, error);
                }
            });
        }
    }
    
    // Check if data is loaded
    isDataLoaded() {
        return this.isLoaded;
    }
}