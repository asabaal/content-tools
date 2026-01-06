class WorkflowViewer {
    constructor() {
        this.state = null;
    }

    async load() {
        try {
            const response = await fetch('data/workflow_state.json');
            if (!response.ok) {
                throw new Error('Failed to load workflow state');
            }
            this.state = await response.json();
            this.render();
        } catch (error) {
            document.getElementById('loading').textContent = 'Error loading data';
            console.error(error);
        }
    }

    render() {
        if (!this.state) {
            document.getElementById('loading').style.display = 'block';
            return;
        }

        document.getElementById('loading').style.display = 'none';
        document.getElementById('app').style.display = 'block';

        this.renderSegments();
        this.renderGroups();
        this.renderSelections();
    }

    renderSegments() {
        const container = document.getElementById('segments');
        container.innerHTML = '';

        if (this.state.segments.length === 0) {
            container.innerHTML = '<p class="empty">No segments loaded</p>';
            return;
        }

        this.state.segments.forEach(segment => {
            const segmentEl = document.createElement('div');
            segmentEl.className = 'segment';
            segmentEl.innerHTML = `
                <div class="segment-header">
                    <span class="segment-id">${this.escapeHtml(segment.segment_id)}</span>
                    <span class="segment-duration">${segment.duration.toFixed(1)}s</span>
                </div>
                <div class="segment-text">${this.escapeHtml(segment.text)}</div>
            `;
            container.appendChild(segmentEl);
        });
    }

    renderGroups() {
        const container = document.getElementById('groups');
        container.innerHTML = '';

        if (this.state.groups.length === 0) {
            container.innerHTML = '<p class="empty">No groups created</p>';
            return;
        }

        this.state.groups.forEach(group => {
            const groupEl = document.createElement('div');
            groupEl.className = 'group';
            
            const selectedClass = group.selected_segment ? 'selected' : '';
            const selectedBadge = group.selected_segment 
                ? `<span class="selected-badge">Selected: ${this.escapeHtml(group.selected_segment)}</span>`
                : '';

            const segmentsList = group.segment_ids.map(id => 
                `<span class="segment-tag">${this.escapeHtml(id)}</span>`
            ).join('');

            groupEl.innerHTML = `
                <div class="group-header ${selectedClass}">
                    <span class="group-id">${this.escapeHtml(group.group_id)}</span>
                    ${selectedBadge}
                </div>
                <div class="group-segments">
                    <span class="label">Segments (${group.segment_ids.length}):</span>
                    <div class="segment-tags">${segmentsList}</div>
                </div>
                ${group.metadata ? `<div class="group-metadata">Metadata: ${this.escapeHtml(JSON.stringify(group.metadata))}</div>` : ''}
            `;
            container.appendChild(groupEl);
        });
    }

    renderSelections() {
        const container = document.getElementById('selections');
        container.innerHTML = '';

        if (Object.keys(this.state.selections).length === 0) {
            container.innerHTML = '<p class="empty">No segments selected</p>';
            return;
        }

        Object.entries(this.state.selections).forEach(([groupId, segmentId]) => {
            const selectionEl = document.createElement('div');
            selectionEl.className = 'selection';
            selectionEl.innerHTML = `
                <div class="selection-group">Group: <strong>${this.escapeHtml(groupId)}</strong></div>
                <div class="selection-segment">Selected segment: <strong>${this.escapeHtml(segmentId)}</strong></div>
            `;
            container.appendChild(selectionEl);
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

const viewer = new WorkflowViewer();

document.addEventListener('DOMContentLoaded', () => {
    viewer.load();
});
