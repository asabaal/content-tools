import { EVENTS, validateEventData } from './Events.js';

export class Component {
    constructor(dataManager, config = {}) {
        if (!dataManager) {
            throw new Error('Component requires DataManager instance');
        }
        
        this.data = dataManager;
        this.config = {
            container: null,
            autoRender: true,
            ...config
        };
        
        this.element = null;
        this.isInitialized = false;
        this.eventListeners = new Map();
        this.childComponents = new Set();
        
        // Bind methods to maintain context
        this.handleDataChange = this.handleDataChange.bind(this);
        this.render = this.render.bind(this);
        this.destroy = this.destroy.bind(this);
    }
    
    // Required methods for all components
    async initialize(container) {
        if (this.isInitialized) {
            console.warn(`${this.constructor.name} already initialized`);
            return;
        }
        
        if (container) {
            this.config.container = container;
        }
        
        if (!this.config.container) {
            throw new Error(`${this.constructor.name} requires container`);
        }
        
        try {
            await this.onInitialize();
            this.setupEventListeners();
            this.createElement();
            
            if (this.config.autoRender) {
                await this.render();
            }
            
            this.isInitialized = true;
            console.log(`${this.constructor.name} initialized successfully`);
        } catch (error) {
            console.error(`Failed to initialize ${this.constructor.name}:`, error);
            throw error;
        }
    }
    
    // Override in subclasses for specific initialization logic
    async onInitialize() {
        // Subclass-specific initialization
    }
    
    // Create the main DOM element for this component
    createElement() {
        if (this.element) {
            return this.element;
        }
        
        this.element = document.createElement('div');
        this.element.className = `component ${this.constructor.name.toLowerCase()}`;
        this.element.dataset.componentId = this.constructor.name;
        
        if (this.config.container) {
            this.config.container.appendChild(this.element);
        }
        
        return this.element;
    }
    
    // Main render method - override in subclasses
    async render() {
        if (!this.isInitialized) {
            throw new Error(`${this.constructor.name} not initialized`);
        }
        
        await this.onRender();
    }
    
    // Override in subclasses for specific rendering logic
    async onRender() {
        // Subclass-specific rendering
    }
    
    // Setup event listeners for DataManager events
    setupEventListeners() {
        // Override in subclasses to listen to specific events
    }
    
    // Add event listener for DataManager events
    addDataListener(eventType, callback) {
        if (!this.data || typeof this.data.on !== 'function') {
            throw new Error('DataManager does not support event listening');
        }
        
        this.data.on(eventType, callback);
        this.eventListeners.set(eventType, callback);
    }
    
    // Remove event listener
    removeDataListener(eventType) {
        if (this.eventListeners.has(eventType)) {
            this.data.off(eventType, this.eventListeners.get(eventType));
            this.eventListeners.delete(eventType);
        }
    }
    
    // Handle data changes - override in subclasses
    handleDataChange(event, data) {
        // Default implementation - subclasses should override
        console.log(`${this.constructor.name} received data change:`, event, data);
    }
    
    // Emit event through DataManager
    emit(eventType, data) {
        if (this.data && typeof this.data.emit === 'function') {
            this.data.emit(eventType, data);
        }
    }
    
    // Add child component
    addChildComponent(childComponent) {
        if (!(childComponent instanceof Component)) {
            throw new Error('Child component must be instance of Component');
        }
        
        this.childComponents.add(childComponent);
    }
    
    // Remove child component
    removeChildComponent(childComponent) {
        this.childComponents.delete(childComponent);
    }
    
    // Get component configuration
    getConfig(key = null) {
        if (key) {
            return this.config[key];
        }
        return { ...this.config };
    }
    
    // Update component configuration
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.onConfigUpdated();
    }
    
    // Called when configuration is updated
    onConfigUpdated() {
        // Override in subclasses if needed
    }
    
    // Show component
    show() {
        if (this.element) {
            this.element.style.display = '';
        }
        this.onVisibilityChanged(true);
    }
    
    // Hide component
    hide() {
        if (this.element) {
            this.element.style.display = 'none';
        }
        this.onVisibilityChanged(false);
    }
    
    // Called when visibility changes
    onVisibilityChanged(isVisible) {
        // Override in subclasses if needed
    }
    
    // Check if component is visible
    isVisible() {
        return this.element && this.element.style.display !== 'none';
    }
    
    // Destroy component and cleanup
    async destroy() {
        if (!this.isInitialized) {
            return;
        }
        
        try {
            // Destroy child components first
            for (const child of this.childComponents) {
                await child.destroy();
            }
            this.childComponents.clear();
            
            // Remove event listeners
            for (const [eventType, callback] of this.eventListeners) {
                this.removeDataListener(eventType);
            }
            this.eventListeners.clear();
            
            // Cleanup DOM element
            if (this.element && this.element.parentNode) {
                this.element.parentNode.removeChild(this.element);
            }
            
            // Call subclass cleanup
            await this.onDestroy();
            
            this.isInitialized = false;
            console.log(`${this.constructor.name} destroyed successfully`);
        } catch (error) {
            console.error(`Error destroying ${this.constructor.name}:`, error);
            throw error;
        }
    }
    
    // Override in subclasses for specific cleanup
    async onDestroy() {
        // Subclass-specific cleanup
    }
    
    // Utility method to create DOM elements with classes
    createElement(tag, className = '', textContent = '') {
        const element = document.createElement(tag);
        if (className) {
            element.className = className;
        }
        if (textContent) {
            element.textContent = textContent;
        }
        return element;
    }
    
    // Utility method to format time
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }
    
    // Utility method to format time short
    formatTimeShort(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Get component status for debugging
    getStatus() {
        return {
            name: this.constructor.name,
            initialized: this.isInitialized,
            visible: this.isVisible(),
            hasElement: !!this.element,
            childComponents: this.childComponents.size,
            eventListeners: this.eventListeners.size
        };
    }
}