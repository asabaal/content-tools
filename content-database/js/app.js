const App = {
    entries: [],
    filteredEntries: [],
    selectedEntryId: null,

    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.applyFilters();
        } catch (error) {
            if (error.message === 'file:// protocol detected') {
                this.showProtocolError();
            } else {
                console.error('Failed to initialize app:', error);
                document.getElementById('content-list').innerHTML = 
                    '<div class="no-content">Error loading content data</div>';
            }
        }
    },

    showProtocolError() {
        document.querySelector('header').style.display = 'none';
        document.getElementById('filters').style.display = 'none';
        
        const container = document.getElementById('content');
        container.innerHTML = `
            <div class="protocol-error">
                <h2>⚠️ Local Server Required</h2>
                <p>This app must be run via a local HTTP server.</p>
                <p><strong>file:// is not supported</strong> due to browser security rules.</p>
                <h3>How to run:</h3>
                <ol>
                    <li>Open a terminal in this directory</li>
                    <li>Run: <code>python3 -m http.server</code></li>
                    <li>Open: <code>http://localhost:8000</code></li>
                </ol>
            </div>
        `;
    },

    async loadData() {
        const rawRows = await DataIngestion.loadCSVFiles();
        this.entries = DataNormalization.normalizeRows(rawRows);
        
        const mediaRecords = await DataIngestion.loadMediaJSON();
        DataNormalization.attachMedia(this.entries, mediaRecords);
        
        this.filteredEntries = [...this.entries];
        
        const filterOptions = DataNormalization.extractFilterOptions(this.entries);
        Renderer.renderFilterUI(filterOptions, () => this.applyFilters());
    },

    setupEventListeners() {
        document.getElementById('close-details').addEventListener('click', () => {
            this.selectedEntryId = null;
            Renderer.hideDetailsPanel();
            Renderer.highlightSelectedEntry(null);
        });
    },

    applyFilters() {
        const filters = this.getActiveFilters();
        
        this.filteredEntries = this.entries.filter(entry => {
            return Object.keys(filters).every(key => {
                const filterValue = filters[key];
                if (!filterValue) return true;
                
                const entryValue = entry[key];
                return entryValue === filterValue;
            });
        });

        this.sortEntries();
        Renderer.renderContentList(this.filteredEntries, (entry) => this.selectEntry(entry));
    },

    getActiveFilters() {
        const filters = {};
        document.querySelectorAll('#filter-container select').forEach(select => {
            const key = select.id.replace('filter-', '');
            filters[key] = select.value;
        });
        return filters;
    },

    sortEntries() {
        this.filteredEntries.sort((a, b) => {
            if (a.releaseDate && b.releaseDate) {
                return new Date(a.releaseDate) - new Date(b.releaseDate);
            }
            if (a.releaseDate) return -1;
            if (b.releaseDate) return 1;
            return 0;
        });
    },

    selectEntry(entry) {
        this.selectedEntryId = entry.contentId;
        Renderer.renderDetailsPanel(entry);
        Renderer.highlightSelectedEntry(entry.contentId);
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
