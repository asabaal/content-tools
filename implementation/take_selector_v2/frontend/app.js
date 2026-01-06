class WorkflowViewer {
    constructor() {
        this.state = null;
        this.highlightedSegmentId = null;
        this.highlightedGroupId = null;
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

        this.bindEventHandlers();
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
            const isHighlighted = this.highlightedSegmentId === segment.segment_id;
            const isSelectedInBackend = this.isSegmentSelectedInBackend(segment.segment_id);
            
            segmentEl.className = 'segment';
            if (isHighlighted) {
                segmentEl.classList.add('highlighted');
            }
            if (isSelectedInBackend) {
                segmentEl.classList.add('backend-selected');
            }
            
            segmentEl.dataset.segmentId = segment.segment_id;
            
            segmentEl.innerHTML = `
                <div class="segment-header">
                    <span class="segment-id">${this.escapeHtml(segment.segment_id)}</span>
                    <span class="segment-duration">${segment.duration.toFixed(1)}s</span>
                    ${isSelectedInBackend ? '<span class="backend-selected-indicator">✓ Selected</span>' : ''}
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
            const isHighlighted = this.highlightedGroupId === group.group_id;
            
            groupEl.className = 'group';
            if (isHighlighted) {
                groupEl.classList.add('highlighted');
            }
            
            const selectedClass = group.selected_segment ? 'selected' : '';
            const selectedBadge = group.selected_segment 
                ? `<span class="selected-badge">Selected: ${this.escapeHtml(group.selected_segment)}</span>`
                : '';

            const segmentsList = group.segment_ids.map(id => {
                const isHighlighted = this.highlightedGroupId === group.group_id;
                const isSelectedInBackend = group.selected_segment === id;
                const isCandidate = isHighlighted && isSelectedInBackend;
                
                let classes = 'segment-tag';
                if (isHighlighted) {
                    classes += ' highlighted';
                }
                if (isSelectedInBackend) {
                    classes += ' backend-selected';
                }
                if (isCandidate) {
                    classes += ' candidate';
                }
                
                return `<span class="${classes}" data-segment-id="${this.escapeHtml(id)}">${this.escapeHtml(id)}</span>`;
            }).join('');

            groupEl.dataset.groupId = group.group_id;

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
            const isHighlighted = this.highlightedSegmentId === segmentId;
            
            selectionEl.className = 'selection';
            if (isHighlighted) {
                selectionEl.classList.add('highlighted');
            }
            
            selectionEl.dataset.segmentId = segmentId;
            
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

    bindEventHandlers() {
        const segmentElements = document.querySelectorAll('.segment');
        segmentElements.forEach(segmentEl => {
            const segmentId = segmentEl.dataset.segmentId;
            segmentEl.addEventListener('click', () => this.handleSegmentClick(segmentId));
        });

        const groupElements = document.querySelectorAll('.group');
        groupElements.forEach(groupEl => {
            const groupId = groupEl.dataset.groupId;
            groupEl.addEventListener('click', (e) => {
                if (!e.target.classList.contains('segment-tag')) {
                    this.handleGroupClick(groupId);
                }
            });
        });
    }

    handleSegmentClick(segmentId) {
        if (this.highlightedSegmentId === segmentId) {
            this.highlightedSegmentId = null;
        } else {
            this.highlightedSegmentId = segmentId;
            this.highlightedGroupId = null;
        }
        this.render();
    }

    handleGroupClick(groupId) {
        if (this.highlightedGroupId === groupId) {
            this.highlightedGroupId = null;
            this.highlightedSegmentId = null;
        } else {
            this.highlightedGroupId = groupId;
            this.highlightedSegmentId = null;
        }
        this.render();
    }

    isSegmentSelectedInBackend(segmentId) {
        return Object.values(this.state.selections).includes(segmentId);
    }
}

const viewer = new WorkflowViewer();

document.addEventListener('DOMContentLoaded', () => {
    viewer.load();
});
