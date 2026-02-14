import { Component } from '../core/Component.js';
import { EVENTS } from '../core/Events.js';

export class InteractiveBoundaries extends Component {
    constructor(dataManager, config = {}) {
        super(dataManager, config);
        
        // Interactive boundaries configuration
        this.config = {
            handleWidth: 12,
            minSegmentDuration: 0.5,
            snapToWords: true,
            snapThreshold: 0.5,
            collisionDetection: true,
            boundaryGap: 0.1,
            ...config
        };
        
        // Interaction state
        this.isDragging = false;
        this.isResizing = false;
        this.dragTarget = null;
        this.resizeDirection = null;
        this.dragStartX = 0;
        this.dragStartValue = 0;
        this.selectedSegmentId = null;
        
        // DOM elements
        this.elements = {};
        
        // Performance tracking
        this.lastUpdate = 0;
        this.updateScheduled = false;
    }
    
    async onInitialize() {
        console.log('Initializing InteractiveBoundaries...');
        
        // Ensure data is loaded
        if (!this.data.isDataLoaded()) {
            await this.data.loadData();
        }
        
        console.log('InteractiveBoundaries initialized');
    }
    
    setupEventListeners() {
        // Listen to segment selection
        this.addDataListener(EVENTS.SEGMENT_SELECTED, (event) => {
            this.selectSegment(event.data.segmentId);
        });
        
        // Listen to timeline zoom changes
        this.addDataListener(EVENTS.TIMELINE_ZOOM_CHANGED, (event) => {
            this.config.pixelsPerSecond = event.data.pixelsPerSecond || 50;
            this.config.zoomLevel = event.data.zoomLevel || 1.0;
            this.scheduleUpdate();
        });
        
        // Listen to segment updates
        this.addDataListener(EVENTS.SEGMENT_UPDATED, (event) => {
            if (event.data.segmentId === this.selectedSegmentId) {
                this.scheduleUpdate();
            }
        });
    }
    
    async onRender() {
        if (!this.element) {
            throw new Error('InteractiveBoundaries element not created');
        }
        
        this.element.innerHTML = '';
        this.element.className = 'interactive-boundaries';
        
        // Create boundary controls overlay
        this.createBoundaryOverlay();
        
        // Setup interaction handlers
        this.setupInteractionHandlers();
        
        console.log('InteractiveBoundaries rendered');
    }
    
    createBoundaryOverlay() {
        // Create overlay container
        this.elements.overlay = this.createElement('div', 'boundaries-overlay');
        this.elements.overlay.style.position = 'absolute';
        this.elements.overlay.style.top = '0';
        this.elements.overlay.style.left = '0';
        this.elements.overlay.style.right = '0';
        this.elements.overlay.style.bottom = '0';
        this.elements.overlay.style.pointerEvents = 'none';
        this.elements.overlay.style.zIndex = '15';
        
        this.element.appendChild(this.elements.overlay);
    }
    
    setupInteractionHandlers() {
        // Global mouse event listeners
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
    
    // Public method to add boundaries to a segment
    addBoundariesToSegment(segmentElement, segment) {
        if (!segmentElement || !segment) return;
        
        const segmentId = segment.id || segment.segment_id;
        
        // Remove existing boundaries
        this.removeBoundariesFromSegment(segmentElement);
        
        // Create left handle
        const leftHandle = this.createElement('div', 'boundary-handle left');
        leftHandle.style.position = 'absolute';
        leftHandle.style.left = '-6px';
        leftHandle.style.top = '0';
        leftHandle.style.bottom = '0';
        leftHandle.style.width = `${this.config.handleWidth}px`;
        leftHandle.style.cursor = 'ew-resize';
        leftHandle.style.pointerEvents = 'auto';
        leftHandle.style.zIndex = '20';
        leftHandle.dataset.segmentId = segmentId;
        leftHandle.dataset.direction = 'left';
        
        // Create right handle
        const rightHandle = this.createElement('div', 'boundary-handle right');
        rightHandle.style.position = 'absolute';
        rightHandle.style.right = '-6px';
        rightHandle.style.top = '0';
        rightHandle.style.bottom = '0';
        rightHandle.style.width = `${this.config.handleWidth}px`;
        rightHandle.style.cursor = 'ew-resize';
        rightHandle.style.pointerEvents = 'auto';
        rightHandle.style.zIndex = '20';
        rightHandle.dataset.segmentId = segmentId;
        rightHandle.dataset.direction = 'right';
        
        // Add event listeners
        leftHandle.addEventListener('mousedown', this.handleResizeMouseDown.bind(this));
        rightHandle.addEventListener('mousedown', this.handleResizeMouseDown.bind(this));
        
        // Add handles to segment
        segmentElement.appendChild(leftHandle);
        segmentElement.appendChild(rightHandle);
        
        // Store reference
        segmentElement.classList.add('has-boundaries');
    }
    
    // Public method to remove boundaries from a segment
    removeBoundariesFromSegment(segmentElement) {
        if (!segmentElement) return;
        
        const handles = segmentElement.querySelectorAll('.boundary-handle');
        handles.forEach(handle => handle.remove());
        
        segmentElement.classList.remove('has-boundaries');
    }
    
    // Select segment and add boundaries
    selectSegment(segmentId) {
        // Remove boundaries from previous selection
        if (this.selectedSegmentId) {
            const prevSegment = document.querySelector(`[data-segment-id="${this.selectedSegmentId}"]`);
            if (prevSegment) {
                this.removeBoundariesFromSegment(prevSegment);
            }
        }
        
        // Add boundaries to new selection
        this.selectedSegmentId = segmentId;
        const segment = this.data.getSegment(segmentId);
        const segmentElement = document.querySelector(`[data-segment-id="${segmentId}"]`);
        
        if (segment && segmentElement) {
            this.addBoundariesToSegment(segmentElement, segment);
        }
    }
    
    // Mouse event handlers
    handleResizeMouseDown(e) {
        e.preventDefault();
        e.stopPropagation();
        
        this.isResizing = true;
        this.dragTarget = e.target;
        this.resizeDirection = e.target.dataset.direction;
        this.dragStartX = e.clientX;
        
        const segmentId = e.target.dataset.segmentId;
        const segment = this.data.getSegment(segmentId);
        
        if (segment) {
            this.dragStartValue = this.resizeDirection === 'left' ? segment.start : segment.end;
            
            // Add visual feedback
            e.target.parentElement.classList.add('resizing');
            
            // Create resize indicator
            this.createResizeIndicator(e.clientX, e.clientY);
        }
    }
    
    handleMouseMove(e) {
        if (!this.isResizing || !this.dragTarget) return;
        
        try {
            const deltaX = e.clientX - this.dragStartX;
            const pixelsPerSecond = this.config.pixelsPerSecond || 50;
            const zoomLevel = this.config.zoomLevel || 1.0;
            const deltaTime = deltaX / (pixelsPerSecond * zoomLevel);
            
            const segmentId = this.dragTarget.dataset.segmentId;
            const segment = this.data.getSegment(segmentId);
            
            if (!segment) return;
            
            let newTime = this.dragStartValue + deltaTime;
            
            // Apply snap to words if enabled
            if (this.config.snapToWords && segment.words && segment.words.length > 0) {
                newTime = this.snapToNearestWord(newTime, segment, this.resizeDirection);
            }
            
            // Apply collision detection if enabled
            if (this.config.collisionDetection) {
                newTime = this.applyCollisionDetection(segment, newTime, this.resizeDirection);
            }
            
            // Apply minimum duration constraint
            newTime = this.applyMinimumDuration(segment, newTime, this.resizeDirection);
            
            // Update segment
            let updates = {};
            if (this.resizeDirection === 'left') {
                updates.start = newTime;
            } else {
                updates.end = newTime;
            }
            
            // Update the segment
            const updatedSegment = this.data.updateSegment(segmentId, updates);
            
            // Update resize indicator
            this.updateResizeIndicator(e.clientX, e.clientY, newTime);
            
            // Emit boundary dragged event
            this.emit(EVENTS.BOUNDARY_DRAGGED, {
                segmentId,
                direction: this.resizeDirection,
                oldTime: this.dragStartValue,
                newTime,
                segment: updatedSegment
            });
            
        } catch (error) {
            console.error('Error in handleMouseMove:', error);
        }
    }
    
    handleMouseUp(e) {
        if (!this.isResizing || !this.dragTarget) return;
        
        try {
            // Remove visual feedback
            if (this.dragTarget.parentElement) {
                this.dragTarget.parentElement.classList.remove('resizing');
            }
            
            // Remove resize indicator
            this.removeResizeIndicator();
            
            const segmentId = this.dragTarget.dataset.segmentId;
            console.log(`Boundary resize completed for segment ${segmentId}, direction: ${this.resizeDirection}`);
            
        } catch (error) {
            console.error('Error in handleMouseUp:', error);
        } finally {
            // Reset state
            this.isResizing = false;
            this.dragTarget = null;
            this.resizeDirection = null;
            this.dragStartX = 0;
            this.dragStartValue = 0;
        }
    }
    
    handleKeyDown(e) {
        if (!this.selectedSegmentId) return;
        
        const segment = this.data.getSegment(this.selectedSegmentId);
        if (!segment) return;
        
        let updates = {};
        let handled = false;
        
        switch (e.key) {
            case 'ArrowLeft':
                if (e.shiftKey) {
                    // Shift + Left Arrow: Move start time left
                    updates.start = Math.max(0, segment.start - 0.1);
                    handled = true;
                }
                break;
            case 'ArrowRight':
                if (e.shiftKey) {
                    // Shift + Right Arrow: Move end time right
                    updates.end = segment.end + 0.1;
                    handled = true;
                }
                break;
        }
        
        if (handled) {
            e.preventDefault();
            this.data.updateSegment(this.selectedSegmentId, updates);
        }
    }
    
    // Utility methods
    snapToNearestWord(time, segment, direction) {
        if (!segment.words || segment.words.length === 0) {
            return time;
        }
        
        let nearestTime = time;
        let minDistance = Infinity;
        
        segment.words.forEach(word => {
            const wordTime = direction === 'left' ? word.start : word.end;
            const distance = Math.abs(time - wordTime);
            
            if (distance < minDistance && distance < this.config.snapThreshold) {
                minDistance = distance;
                nearestTime = wordTime;
            }
        });
        
        return nearestTime;
    }
    
    applyCollisionDetection(segment, newTime, direction) {
        const segments = this.data.getSegments();
        const segmentIndex = segments.findIndex(s => 
            (s.id === segment.id || s.segment_id === segment.id)
        );
        
        if (segmentIndex === -1) return newTime;
        
        if (direction === 'left') {
            // Check collision with previous segment
            if (segmentIndex > 0) {
                const prevSegment = segments[segmentIndex - 1];
                if (newTime < prevSegment.end + this.config.boundaryGap) {
                    return prevSegment.end + this.config.boundaryGap;
                }
            }
            // Ensure start is not after end
            if (newTime >= segment.end - this.config.minSegmentDuration) {
                return segment.end - this.config.minSegmentDuration;
            }
        } else {
            // Check collision with next segment
            if (segmentIndex < segments.length - 1) {
                const nextSegment = segments[segmentIndex + 1];
                if (newTime > nextSegment.start - this.config.boundaryGap) {
                    return nextSegment.start - this.config.boundaryGap;
                }
            }
            // Ensure end is not before start
            if (newTime <= segment.start + this.config.minSegmentDuration) {
                return segment.start + this.config.minSegmentDuration;
            }
        }
        
        return newTime;
    }
    
    applyMinimumDuration(segment, newTime, direction) {
        if (direction === 'left') {
            // Ensure minimum duration
            if (segment.end - newTime < this.config.minSegmentDuration) {
                return segment.end - this.config.minSegmentDuration;
            }
        } else {
            // Ensure minimum duration
            if (newTime - segment.start < this.config.minSegmentDuration) {
                return segment.start + this.config.minSegmentDuration;
            }
        }
        
        return newTime;
    }
    
    createResizeIndicator(x, y) {
        this.removeResizeIndicator(); // Remove any existing indicator
        
        this.elements.resizeIndicator = this.createElement('div', 'resize-indicator');
        this.elements.resizeIndicator.style.position = 'fixed';
        this.elements.resizeIndicator.style.left = `${x}px`;
        this.elements.resizeIndicator.style.top = `${y - 40}px`;
        this.elements.resizeIndicator.style.background = '#1f2937';
        this.elements.resizeIndicator.style.color = 'white';
        this.elements.resizeIndicator.style.padding = '4px 8px';
        this.elements.resizeIndicator.style.borderRadius = '4px';
        this.elements.resizeIndicator.style.fontSize = '11px';
        this.elements.resizeIndicator.style.fontWeight = '600';
        this.elements.resizeIndicator.style.whiteSpace = 'nowrap';
        this.elements.resizeIndicator.style.zIndex = '1000';
        this.elements.resizeIndicator.style.pointerEvents = 'none';
        
        document.body.appendChild(this.elements.resizeIndicator);
    }
    
    updateResizeIndicator(x, y, time) {
        if (this.elements.resizeIndicator) {
            this.elements.resizeIndicator.style.left = `${x}px`;
            this.elements.resizeIndicator.style.top = `${y - 40}px`;
            this.elements.resizeIndicator.textContent = this.formatTime(time);
        }
    }
    
    removeResizeIndicator() {
        if (this.elements.resizeIndicator && this.elements.resizeIndicator.parentNode) {
            this.elements.resizeIndicator.parentNode.removeChild(this.elements.resizeIndicator);
            this.elements.resizeIndicator = null;
        }
    }
    
    // Performance optimization
    scheduleUpdate() {
        if (this.updateScheduled) return;
        
        this.updateScheduled = true;
        requestAnimationFrame(() => {
            this.updateScheduled = false;
        });
    }
    
    // Add component styles
    addStyles() {
        if (document.getElementById('interactive-boundaries-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'interactive-boundaries-styles';
        style.textContent = `
            .interactive-boundaries {
                position: relative;
                pointer-events: none;
            }
            
            .boundary-handle {
                background: rgba(59, 130, 246, 0.3);
                border: 2px solid #3b82f6;
                transition: all 0.2s ease;
                border-radius: 3px;
            }
            
            .boundary-handle:hover {
                background: rgba(59, 130, 246, 0.6);
                border-color: #1e40af;
                width: 16px !important;
            }
            
            .boundary-handle.left {
                border-radius: 3px 0 0 3px;
            }
            
            .boundary-handle.right {
                border-radius: 0 3px 3px 0;
            }
            
            .boundary-handle::before {
                content: '⋮';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #3b82f6;
                font-size: 12px;
                font-weight: bold;
                opacity: 0.7;
            }
            
            .boundary-handle:hover::before {
                opacity: 1;
            }
            
            .timeline-segment.resizing {
                background: #a78bfa !important;
                border-color: #8b5cf6 !important;
                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3) !important;
            }
            
            .resize-indicator {
                position: fixed;
                background: #1f2937;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
            }
            
            .resize-indicator::after {
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border: 4px solid transparent;
                border-top-color: #1f2937;
            }
            
            .timeline-segment.has-boundaries {
                position: relative;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    async onDestroy() {
        // Remove resize indicator
        this.removeResizeIndicator();
        
        // Remove event listeners
        document.removeEventListener('mousemove', this.handleMouseMove.bind(this));
        document.removeEventListener('mouseup', this.handleMouseUp.bind(this));
        document.removeEventListener('keydown', this.handleKeyDown.bind(this));
        
        // Remove boundaries from all segments
        const segmentsWithBoundaries = document.querySelectorAll('.has-boundaries');
        segmentsWithBoundaries.forEach(segment => {
            this.removeBoundariesFromSegment(segment);
        });
    }
}