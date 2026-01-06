import { Component } from '../core/Component.js';
import { EVENTS } from '../core/Events.js';

/**
 * WordRedistribution Component
 * 
 * Handles intelligent redistribution of word timings when segment boundaries change.
 * Ensures words are evenly distributed within segments while maintaining natural speech patterns.
 */
export class WordRedistribution extends Component {
    constructor(dataManager, config = {}) {
        super(dataManager, config);
        
        this.config = {
            minWordDuration: 0.1, // Minimum duration per word in seconds
            maxWordDuration: 2.0, // Maximum duration per word in seconds
            preferEvenDistribution: true,
            preserveNaturalPauses: true,
            pauseThreshold: 0.3, // Seconds to consider as natural pause
            ...config
        };
        
        this.selectedSegmentId = null;
        this.redistributionHistory = [];
    }

    async initialize(container) {
        try {
            this.element = container;
            
            // Set up event listeners
            this.setupEventListeners();
            
            this.isInitialized = true;
            this.log('WordRedistribution component initialized');
            
        } catch (error) {
            this.logError('Failed to initialize WordRedistribution:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Listen for boundary changes
        this.data.on(EVENTS.BOUNDARY_DRAGGED, (event) => {
            this.handleBoundaryChange(event);
        });

        // Listen for segment updates
        this.data.on(EVENTS.SEGMENT_UPDATED, (event) => {
            this.handleSegmentUpdate(event);
        });

        // Listen for segment selection
        this.data.on(EVENTS.SEGMENT_SELECTED, (event) => {
            this.selectedSegmentId = event.data.segmentId;
        });
    }

    /**
     * Handle boundary drag events by redistributing words
     */
    handleBoundaryChange(event) {
        const { segmentId, direction, oldTime, newTime } = event.data;
        
        try {
            const segment = this.data.getSegment(segmentId);
            if (!segment || !segment.words || segment.words.length === 0) {
                return;
            }

            // Redistribute words based on the new timing
            const redistributedWords = this.redistributeWords(
                segment.words, 
                segment.start, 
                segment.end,
                segmentId
            );

            // Update the segment with new word timings
            this.data.updateSegment(segmentId, { 
                words: redistributedWords,
                _redistributed: true,
                _redistributionReason: `boundary_${direction}_change`
            });

            this.log(`Redistributed ${redistributedWords.length} words for segment ${segmentId}`);

        } catch (error) {
            this.logError(`Failed to redistribute words for segment ${segmentId}:`, error);
        }
    }

    /**
     * Handle segment update events
     */
    handleSegmentUpdate(event) {
        const { segmentId, changes } = event.data;
        
        // If timing changed, redistribute words
        if (changes.start !== undefined || changes.end !== undefined) {
            const segment = this.data.getSegment(segmentId);
            if (segment && segment.words && segment.words.length > 0) {
                this.redistributeSegmentWords(segmentId);
            }
        }
    }

    /**
     * Redistribute words within a segment
     */
    redistributeSegmentWords(segmentId) {
        try {
            const segment = this.data.getSegment(segmentId);
            if (!segment || !segment.words || segment.words.length === 0) {
                return;
            }

            const redistributedWords = this.redistributeWords(
                segment.words,
                segment.start,
                segment.end,
                segmentId
            );

            // Store redistribution history
            this.redistributionHistory.push({
                segmentId,
                timestamp: Date.now(),
                oldWords: [...segment.words],
                newWords: [...redistributedWords],
                segmentDuration: segment.end - segment.start
            });

            // Keep history manageable
            if (this.redistributionHistory.length > 100) {
                this.redistributionHistory = this.redistributionHistory.slice(-50);
            }

            this.data.updateSegment(segmentId, { 
                words: redistributedWords,
                _redistributed: true,
                _redistributionReason: 'segment_timing_change'
            });

        } catch (error) {
            this.logError(`Failed to redistribute segment words for ${segmentId}:`, error);
        }
    }

    /**
     * Core word redistribution algorithm
     */
    redistributeWords(words, segmentStart, segmentEnd, segmentId) {
        const segmentDuration = segmentEnd - segmentStart;
        const wordCount = words.length;
        
        if (wordCount === 0) return [];

        // Calculate base duration per word
        let baseDuration = segmentDuration / wordCount;
        
        // Apply constraints
        baseDuration = Math.max(this.config.minWordDuration, baseDuration);
        baseDuration = Math.min(this.config.maxWordDuration, baseDuration);

        const redistributedWords = [];
        let currentTime = segmentStart;

        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            let wordDuration = baseDuration;
            
            // Adjust for natural pauses (punctuation, longer words)
            if (this.config.preserveNaturalPauses) {
                wordDuration = this.adjustWordDuration(word, baseDuration, i, words.length);
            }

            // Ensure we don't exceed segment duration
            if (currentTime + wordDuration > segmentEnd) {
                wordDuration = segmentEnd - currentTime;
            }

            redistributedWords.push({
                ...word,
                start: currentTime,
                end: currentTime + wordDuration,
                duration: wordDuration
            });

            currentTime += wordDuration;
        }

        // If we have remaining time due to constraints, distribute it evenly
        if (currentTime < segmentEnd) {
            const remainingTime = segmentEnd - currentTime;
            const adjustment = remainingTime / wordCount;
            
            redistributedWords.forEach((word, index) => {
                word.start += adjustment * index;
                word.end += adjustment * (index + 1);
                word.duration += adjustment;
            });
        }

        return redistributedWords;
    }

    /**
     * Adjust word duration based on linguistic patterns
     */
    adjustWordDuration(word, baseDuration, index, totalWords) {
        let adjustedDuration = baseDuration;
        
        // Longer words get more time
        if (word.word && word.word.length > 8) {
            adjustedDuration *= 1.2;
        } else if (word.word && word.word.length < 4) {
            adjustedDuration *= 0.8;
        }

        // Add pause after punctuation
        if (word.word && /[.!?]$/.test(word.word)) {
            adjustedDuration += this.config.pauseThreshold;
        }

        // Slightly longer pause at commas
        if (word.word && /,$/.test(word.word)) {
            adjustedDuration += this.config.pauseThreshold * 0.5;
        }

        // First and last words might need slight adjustments
        if (index === 0) {
            adjustedDuration *= 0.9; // Slightly faster start
        } else if (index === totalWords - 1) {
            adjustedDuration *= 1.1; // Slightly slower end
        }

        return adjustedDuration;
    }

    /**
     * Get redistribution statistics
     */
    getRedistributionStats() {
        return {
            totalRedistributions: this.redistributionHistory.length,
            recentRedistributions: this.redistributionHistory.slice(-10),
            averageSegmentDuration: this.calculateAverageSegmentDuration(),
            wordsProcessed: this.redistributionHistory.reduce((sum, r) => sum + r.newWords.length, 0)
        };
    }

    /**
     * Calculate average segment duration from history
     */
    calculateAverageSegmentDuration() {
        if (this.redistributionHistory.length === 0) return 0;
        
        const total = this.redistributionHistory.reduce((sum, r) => sum + r.segmentDuration, 0);
        return total / this.redistributionHistory.length;
    }

    /**
     * Validate word timing consistency
     */
    validateWordTimings(segmentId) {
        const segment = this.data.getSegment(segmentId);
        if (!segment || !segment.words) {
            return { valid: false, errors: ['No segment or words found'] };
        }

        const errors = [];
        const words = segment.words;

        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            
            // Check for negative durations
            if (word.duration <= 0) {
                errors.push(`Word ${i} has invalid duration: ${word.duration}`);
            }

            // Check for gaps
            if (i > 0) {
                const prevWord = words[i - 1];
                if (word.start - prevWord.end > 0.1) {
                    errors.push(`Gap between words ${i-1} and ${i}: ${word.start - prevWord.end}s`);
                }
            }

            // Check if word exceeds segment bounds
            if (word.start < segment.start || word.end > segment.end) {
                errors.push(`Word ${i} exceeds segment bounds`);
            }
        }

        return {
            valid: errors.length === 0,
            errors,
            wordCount: words.length,
            totalDuration: segment.end - segment.start
        };
    }

    /**
     * Export redistribution history for analysis
     */
    exportHistory() {
        return {
            history: this.redistributionHistory,
            config: this.config,
            exportedAt: new Date().toISOString()
        };
    }

    render() {
        // WordRedistribution doesn't render UI - it's a background processor
        return null;
    }

    destroy() {
        this.redistributionHistory = [];
        this.selectedSegmentId = null;
        super.destroy();
    }
}