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

document.addEventListener('DOMContentLoaded', function() {
    const segments = document.querySelectorAll('[data-segment-id]');
    segments.forEach(segment => {
        segment.addEventListener('click', function() {
            const segmentId = this.getAttribute('data-segment-id');
            selectSegment(segmentId);
        });
    });

    const takeSwitchers = document.querySelectorAll('[data-take-switch]');
    takeSwitchers.forEach(switcher => {
        switcher.addEventListener('click', function(event) {
            event.stopPropagation();
            const takeId = this.getAttribute('data-take-switch');
            const segmentId = this.getAttribute('data-segment-id');
            switchTake(takeId, segmentId);
        });
    });
});
