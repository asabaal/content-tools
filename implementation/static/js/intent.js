(function() {
    'use strict';

    function sendIntent(eventType, data) {
        fetch('/intent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                intent_type: eventType,
                segment_id: data.segmentId,
                take_id: data.takeId || null
            })
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Intent error:', error);
        });
    }

    function selectSegment(segmentId) {
        sendIntent('select_segment', { segmentId: segmentId });
    }

    function switchTake(takeId, segmentId) {
        sendIntent('switch_take', { takeId: takeId, segmentId: segmentId });
    }

    function updateSelectionIndicator(segmentRow, isSelected) {
        const selectionCell = segmentRow.querySelector('td:last-child');
        if (selectionCell) {
            selectionCell.textContent = isSelected ? 'Selected' : '';
        }
    }

    function setupIntentHandlers(dom) {
        const doc = dom || document;
        
        const segments = doc.querySelectorAll('[data-segment-id]');
        segments.forEach(segment => {
            segment.addEventListener('click', function(event) {
                const segmentId = this.getAttribute('data-segment-id');
                updateSelectionIndicator(this, true);
                selectSegment(segmentId);
            });
        });

        const takeSwitchers = doc.querySelectorAll('[data-take-switch]');
        takeSwitchers.forEach(switcher => {
            switcher.addEventListener('click', function(event) {
                event.stopPropagation();
                const takeId = this.getAttribute('data-take-switch');
                const segmentId = this.getAttribute('data-segment-id');
                switchTake(takeId, segmentId);
            });
        });
    }

    if (typeof window !== 'undefined' && typeof document !== 'undefined') {
        document.addEventListener('DOMContentLoaded', function() {
            setupIntentHandlers(document);
        });
    }
})();

