import { Component } from '../core/Component.js';
import { EVENTS } from '../core/Events.js';

export class TimelineViewer extends Component {
    constructor(dataManager, config = {}) {
        super(dataManager, config);
        
        // Timeline-specific configuration
        this.config = {
            pixelsPerSecond: 50,
            zoomLevel: 1.0,
            minZoom: 0.2,
            maxZoom: 5.0,
            showWordMarkers: true,
            segmentHeight: 35,
            segmentSpacing: 10,
            timeRulerHeight: 30,
            ...config
        };
        
        // Timeline state
        this.totalDuration = 0;
        this.selectedSegmentId = null;
        this.hoveredSegmentId = null;
        this.timelineWidth = 0;
        this.viewportWidth = 0;
        
        // DOM elements cache
        this.elements = {};
        
        // Performance optimization
        this.renderScheduled = false;
        this.lastRenderTime = 0;
    }
    
    async onInitialize() {
        console.log('Initializing TimelineViewer...');
        
        // Load data if not already loaded
        if (!this.data.isDataLoaded()) {
            await this.data.loadData();
        }
        
        // Calculate timeline dimensions
        this.calculateDimensions();
        
        console.log('TimelineViewer initialized');
    }
    
    setupEventListeners() {
        // Listen to data changes
        this.addDataListener(EVENTS.DATA_LOADED, () => {
            this.calculateDimensions();
            this.scheduleRender();
        });
        
        this.addDataListener(EVENTS.SEGMENT_UPDATED, (event) => {
            if (event.data.segmentId === this.selectedSegmentId) {
                this.scheduleRender();
            }
        });
        
        this.addDataListener(EVENTS.SEGMENT_SELECTED, (event) => {
            this.selectSegment(event.data.segmentId);
        });
        
        this.addDataListener(EVENTS.TIMELINE_ZOOM_CHANGED, (event) => {
            this.config.zoomLevel = event.data.zoomLevel;
            this.scheduleRender();
        });
    }
    
    async onRender() {
        if (!this.element) {
            throw new Error('TimelineViewer element not created');
        }
        
        this.element.innerHTML = '';
        this.element.className = 'timeline-viewer';
        
        // Create timeline structure
        this.createTimelineStructure();
        
        // Render time ruler
        this.renderTimeRuler();
        
        // Render segments
        this.renderSegments();
        
        // Render word markers if enabled
        if (this.config.showWordMarkers) {
            this.renderWordMarkers();
        }
        
        // Setup interaction handlers
        this.setupInteractionHandlers();
        
        console.log('TimelineViewer rendered');
    }
    
    createTimelineStructure() {
        // Main timeline container
        this.elements.timeline = this.createElement('div', 'timeline');
        this.elements.timeline.style.width = `${this.timelineWidth}px`;
        this.elements.timeline.style.minWidth = '800px';
        
        // Time ruler
        this.elements.timeRuler = this.createElement('div', 'time-ruler');
        
        // Segments area
        this.elements.segmentsArea = this.createElement('div', 'segments-area');
        this.elements.segmentsArea.style.height = '400px';
        this.elements.segmentsArea.style.position = 'relative';
        
        // Assemble timeline
        this.elements.timeline.appendChild(this.elements.timeRuler);
        this.elements.timeline.appendChild(this.elements.segmentsArea);
        this.element.appendChild(this.elements.timeline);
        
        // Add styles
        this.addStyles();
    }
    
    calculateDimensions() {
        const segments = this.data.getSegments();
        this.totalDuration = Math.max(...segments.map(s => s.end), 0);
        this.timelineWidth = this.totalDuration * this.config.pixelsPerSecond * this.config.zoomLevel;
        
        // Calculate viewport width from container or use default
        if (this.config.container) {
            this.viewportWidth = this.config.container.clientWidth || 800;
        } else {
            this.viewportWidth = 800;
        }
    }
    
    renderTimeRuler() {
        const ruler = this.elements.timeRuler;
        ruler.innerHTML = '';
        
        const interval = this.getTimeInterval();
        const subInterval = this.getSubInterval(interval);
        
        const startMark = Math.floor(0 / interval) * interval - interval;
        const endMark = Math.ceil(this.totalDuration / interval) * interval + interval;
        
        // Render minor ticks
        for (let time = startMark; time <= endMark; time += subInterval) {
            if (time % interval !== 0 && time >= 0 && time <= this.totalDuration) {
                const mark = this.createElement('div', 'time-mark minor');
                mark.style.left = `${time * this.config.pixelsPerSecond * this.config.zoomLevel}px`;
                ruler.appendChild(mark);
                
                if (interval <= 2 && time % 1 === 0) {
                    const label = this.createElement('div', 'time-label minor');
                    label.textContent = this.formatTimeShort(time);
                    label.style.left = `${time * this.config.pixelsPerSecond * this.config.zoomLevel}px`;
                    ruler.appendChild(label);
                }
            }
        }
        
        // Render major ticks
        for (let time = startMark; time <= endMark; time += interval) {
            if (time >= 0 && time <= this.totalDuration) {
                const mark = this.createElement('div', 'time-mark major');
                mark.style.left = `${time * this.config.pixelsPerSecond * this.config.zoomLevel}px`;
                ruler.appendChild(mark);
                
                const label = this.createElement('div', 'time-label');
                label.textContent = this.formatTimeShort(time);
                label.style.left = `${time * this.config.pixelsPerSecond * this.config.zoomLevel}px`;
                ruler.appendChild(label);
            }
        }
    }
    
    renderSegments() {
        const area = this.elements.segmentsArea;
        area.innerHTML = '';
        
        const segments = this.data.getSegments();
        
        segments.forEach((segment, index) => {
            const segmentEl = this.createSegmentElement(segment, index);
            area.appendChild(segmentEl);
        });
    }
    
    createSegmentElement(segment, index) {
        const segmentEl = this.createElement('div', 'timeline-segment');
        
        // Position and size
        const left = segment.start * this.config.pixelsPerSecond * this.config.zoomLevel;
        const width = (segment.end - segment.start) * this.config.pixelsPerSecond * this.config.zoomLevel;
        const top = 20 + (index % 3) * (this.config.segmentHeight + this.config.segmentSpacing);
        
        segmentEl.style.left = `${left}px`;
        segmentEl.style.width = `${width}px`;
        segmentEl.style.top = `${top}px`;
        segmentEl.style.height = `${this.config.segmentHeight}px`;
        
        // Segment ID for identification
        segmentEl.dataset.segmentId = segment.id || segment.segment_id;
        
        // Selection state
        if (this.selectedSegmentId === segment.id || this.selectedSegmentId === segment.segment_id) {
            segmentEl.classList.add('selected');
        }
        
        // Hover state
        if (this.hoveredSegmentId === segment.id || this.hoveredSegmentId === segment.segment_id) {
            segmentEl.classList.add('hovered');
        }
        
        // Segment content
        const textEl = this.createElement('div', 'segment-text');
        textEl.textContent = segment.text;
        textEl.title = segment.text; // Tooltip for full text
        
        const timeEl = this.createElement('div', 'segment-time');
        timeEl.textContent = `${this.formatTimeShort(segment.start)} - ${this.formatTimeShort(segment.end)}`;
        
        segmentEl.appendChild(textEl);
        segmentEl.appendChild(timeEl);
        
        // Event listeners
        segmentEl.addEventListener('click', () => this.onSegmentClick(segment));
        segmentEl.addEventListener('mouseenter', () => this.onSegmentHover(segment.id || segment.segment_id, true));
        segmentEl.addEventListener('mouseleave', () => this.onSegmentHover(segment.id || segment.segment_id, false));
        
        return segmentEl;
    }
    
    renderWordMarkers() {
        const area = this.elements.segmentsArea;
        const segments = this.data.getSegments();
        
        segments.forEach(segment => {
            if (segment.words && segment.words.length > 0) {
                segment.words.forEach(word => {
                    const marker = this.createElement('div', 'word-marker');
                    
                    const left = word.start * this.config.pixelsPerSecond * this.config.zoomLevel;
                    marker.style.left = `${left}px`;
                    marker.style.top = '0px';
                    marker.style.height = '100%';
                    marker.style.width = '1px';
                    marker.title = `${word.text} (${this.formatTimeShort(word.start)} - ${this.formatTimeShort(word.end)})`;
                    
                    marker.addEventListener('click', () => this.onWordClick(word, segment));
                    
                    area.appendChild(marker);
                });
            }
        });
    }
    
    setupInteractionHandlers() {
        // Zoom controls
        this.setupZoomControls();
        
        // Pan functionality
        this.setupPanFunctionality();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    setupZoomControls() {
        // Create zoom controls if not in config
        if (!this.config.disableZoomControls) {
            const zoomControls = this.createElement('div', 'zoom-controls');
            
            const zoomInBtn = this.createElement('button', 'zoom-btn', '+');
            zoomInBtn.addEventListener('click', () => this.zoomIn());
            
            const zoomOutBtn = this.createElement('button', 'zoom-btn', '-');
            zoomOutBtn.addEventListener('click', () => this.zoomOut());
            
            const resetBtn = this.createElement('button', 'zoom-btn', 'Reset');
            resetBtn.addEventListener('click', () => this.resetZoom());
            
            const zoomLevel = this.createElement('div', 'zoom-level');
            zoomLevel.textContent = `${Math.round(this.config.zoomLevel * 100)}%`;
            this.elements.zoomLevelDisplay = zoomLevel;
            
            zoomControls.appendChild(zoomOutBtn);
            zoomControls.appendChild(zoomLevel);
            zoomControls.appendChild(zoomInBtn);
            zoomControls.appendChild(resetBtn);
            
            this.element.appendChild(zoomControls);
        }
    }
    
    setupPanFunctionality() {
        let isPanning = false;
        let startX = 0;
        let scrollLeft = 0;
        
        const timeline = this.elements.timeline;
        
        timeline.addEventListener('mousedown', (e) => {
            if (e.target === timeline || e.target.classList.contains('segments-area')) {
                isPanning = true;
                startX = e.pageX - timeline.offsetLeft;
                scrollLeft = timeline.parentElement.scrollLeft;
                timeline.style.cursor = 'grabbing';
                e.preventDefault();
            }
        });
        
        timeline.addEventListener('mouseleave', () => {
            isPanning = false;
            timeline.style.cursor = 'default';
        });
        
        timeline.addEventListener('mouseup', () => {
            isPanning = false;
            timeline.style.cursor = 'default';
        });
        
        timeline.addEventListener('mousemove', (e) => {
            if (!isPanning) return;
            e.preventDefault();
            const x = e.pageX - timeline.offsetLeft;
            const walk = (x - startX) * 2;
            timeline.parentElement.scrollLeft = scrollLeft - walk;
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.isVisible()) return;
            
            switch (e.key) {
                case '+':
                case '=':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.zoomIn();
                    }
                    break;
                case '-':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.zoomOut();
                    }
                    break;
                case '0':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.resetZoom();
                    }
                    break;
            }
        });
    }
    
    // Event handlers
    onSegmentClick(segment) {
        const segmentId = segment.id || segment.segment_id;
        this.selectSegment(segmentId);
        this.emit(EVENTS.SEGMENT_SELECTED, { segmentId, segment });
    }
    
    onSegmentHover(segmentId, isHovering) {
        this.hoveredSegmentId = isHovering ? segmentId : null;
        
        // Check if element exists
        if (!this.element) {
            return;
        }
        
        // Update visual state
        const segmentEl = this.element.querySelector(`[data-segment-id="${segmentId}"]`);
        if (segmentEl) {
            if (isHovering) {
                segmentEl.classList.add('hovered');
            } else {
                segmentEl.classList.remove('hovered');
            }
        }
    }
    
    onWordClick(word, segment) {
        console.log('Word clicked:', word, 'in segment:', segment);
        // Could emit word selection event for other components
    }
    
    // Public methods
    selectSegment(segmentId) {
        console.log('TimelineViewer.selectSegment called with:', segmentId);
        console.log('TimelineViewer.selectSegment: this.element =', this.element);
        console.log('TimelineViewer.selectSegment: this.isInitialized =', this.isInitialized);
        
        // Check if element exists
        if (!this.element) {
            console.warn('TimelineViewer.selectSegment: element is null, component may not be initialized');
            console.warn('TimelineViewer.selectSegment: isInitialized =', this.isInitialized);
            console.warn('TimelineViewer.selectSegment: config =', this.config);
            this.selectedSegmentId = segmentId;
            return;
        }
        
        // Remove previous selection
        if (this.selectedSegmentId) {
            const prevEl = this.element.querySelector(`[data-segment-id="${this.selectedSegmentId}"]`);
            if (prevEl) {
                prevEl.classList.remove('selected');
            }
        }
        
        // Add new selection
        this.selectedSegmentId = segmentId;
        const newEl = this.element.querySelector(`[data-segment-id="${segmentId}"]`);
        if (newEl) {
            newEl.classList.add('selected');
            // Scroll into view if needed
            newEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    }
    
    zoomIn() {
        this.config.zoomLevel = Math.min(this.config.zoomLevel * 1.5, this.config.maxZoom);
        this.updateZoom();
    }
    
    zoomOut() {
        this.config.zoomLevel = Math.max(this.config.zoomLevel / 1.5, this.config.minZoom);
        this.updateZoom();
    }
    
    resetZoom() {
        this.config.zoomLevel = 1.0;
        this.updateZoom();
    }
    
    updateZoom() {
        this.calculateDimensions();
        this.scheduleRender();
        
        // Update zoom display
        if (this.elements.zoomLevelDisplay) {
            this.elements.zoomLevelDisplay.textContent = `${Math.round(this.config.zoomLevel * 100)}%`;
        }
        
        // Emit zoom changed event
        this.emit(EVENTS.TIMELINE_ZOOM_CHANGED, { 
            zoomLevel: this.config.zoomLevel,
            timelineWidth: this.timelineWidth
        });
    }
    
    // Utility methods
    getTimeInterval() {
        const visibleDuration = this.viewportWidth / (this.config.pixelsPerSecond * this.config.zoomLevel);
        
        if (visibleDuration <= 10) return 1;
        if (visibleDuration <= 20) return 2;
        if (visibleDuration <= 30) return 5;
        if (visibleDuration <= 60) return 10;
        if (visibleDuration <= 120) return 15;
        if (visibleDuration <= 300) return 30;
        if (visibleDuration <= 600) return 60;
        return 120;
    }
    
    getSubInterval(mainInterval) {
        if (mainInterval <= 1) return 0.25;
        if (mainInterval <= 2) return 0.5;
        if (mainInterval <= 5) return 1;
        if (mainInterval <= 10) return 2;
        if (mainInterval <= 15) return 5;
        if (mainInterval <= 30) return 10;
        if (mainInterval <= 60) return 15;
        if (mainInterval <= 120) return 30;
        return 60;
    }
    
    // Performance optimization
    scheduleRender() {
        if (this.renderScheduled) return;
        
        this.renderScheduled = true;
        requestAnimationFrame(() => {
            this.render().catch(error => {
                console.error('TimelineViewer render error:', error);
            });
            this.renderScheduled = false;
        });
    }
    
    // Add component styles
    addStyles() {
        if (document.getElementById('timeline-viewer-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'timeline-viewer-styles';
        style.textContent = `
            .timeline-viewer {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                overflow: auto;
                position: relative;
            }
            
            .timeline {
                position: relative;
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                min-height: 400px;
            }
            
            .time-ruler {
                position: sticky;
                top: 0;
                left: 0;
                right: 0;
                height: 30px;
                background: #f1f5f9;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                font-size: 12px;
                color: #64748b;
                z-index: 10;
            }
            
            .time-mark {
                position: absolute;
                top: 0;
                bottom: 0;
                width: 1px;
                background: #cbd5e1;
            }
            
            .time-mark.major {
                width: 2px;
                background: #94a3b8;
            }
            
            .time-label {
                position: absolute;
                top: 5px;
                transform: translateX(-50%);
                font-size: 11px;
                white-space: nowrap;
                color: #475569;
                font-weight: 500;
            }
            
            .time-label.minor {
                font-size: 9px;
                color: #94a3b8;
                font-weight: 400;
            }
            
            .segments-area {
                position: relative;
                min-height: 350px;
                padding: 10px 0;
            }
            
            .timeline-segment {
                position: absolute;
                background: #dbeafe;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                padding: 8px 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
                font-size: 14px;
                line-height: 1.4;
                z-index: 5;
                user-select: none;
            }
            
            .timeline-segment:hover {
                background: #bfdbfe;
                box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
                z-index: 6;
            }
            
            .timeline-segment.selected {
                background: #d1fae5;
                border-color: #10b981;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                z-index: 7;
            }
            
            .timeline-segment.hovered {
                background: #fef3c7;
                border-color: #f59e0b;
            }
            
            .segment-text {
                color: #1e40af;
                font-weight: 500;
                font-size: 13px;
            }
            
            .segment-time {
                font-size: 10px;
                color: #64748b;
                margin-top: 2px;
            }
            
            .word-marker {
                position: absolute;
                width: 1px;
                background: #f59e0b;
                opacity: 0.6;
                cursor: pointer;
                transition: all 0.2s ease;
                z-index: 3;
            }
            
            .word-marker:hover {
                opacity: 1;
                background: #d97706;
                width: 2px;
                z-index: 8;
            }
            
            .zoom-controls {
                display: flex;
                gap: 10px;
                align-items: center;
                margin-bottom: 15px;
                justify-content: flex-end;
            }
            
            .zoom-btn {
                background: #4f46e5;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s ease;
            }
            
            .zoom-btn:hover {
                background: #4338ca;
            }
            
            .zoom-level {
                background: #e0e7ff;
                color: #4f46e5;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 600;
                min-width: 50px;
                text-align: center;
                font-size: 12px;
            }
        `;
        
        document.head.appendChild(style);
    }
}