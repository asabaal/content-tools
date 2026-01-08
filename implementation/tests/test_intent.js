const assert = require('assert');
const path = require('path');

var actualCalls = [];

global.window = {
    location: {
        reload: function() {}
    },
    document: {
        querySelectorAll: function(selector) {
            return [
                {
                    getAttribute: function(attr) {
                        if (attr === 'data-segment-id') return 's1';
                        return null;
                    },
                    querySelector: function(sel) {
                        return this;
                    },
                    addEventListener: function(event, handler) {
                    }
                }
            ];
        },
        addEventListener: function(event, handler) {
        }
    }
};

global.fetch = function(url, options) {
    actualCalls.push({
        url: url,
        method: options.method,
        body: JSON.parse(options.body)
    });
    return Promise.resolve({ ok: true });
}

const { selectSegment, switchTake, sendIntent } = require(path.join(__dirname, '..', 'static', 'js', 'intent.js'));

function resetCalls() {
    actualCalls = [];
}

function test_select_segment_intent() {
    resetCalls();
    selectSegment('s1');
    
    assert.strictEqual(actualCalls.length, 1, 'selectSegment should make one fetch call');
    assert.strictEqual(actualCalls[0].url, '/intent', 'should call /intent endpoint');
    assert.strictEqual(actualCalls[0].method, 'POST', 'should use POST method');
    assert.strictEqual(actualCalls[0].body.intent_type, 'select_segment', 'should set correct intent type');
    assert.strictEqual(actualCalls[0].body.segment_id, 's1', 'should pass correct segment ID');
    
    console.log('✓ test_select_segment_intent passed');
}

function test_switch_take_intent() {
    resetCalls();
    switchTake('t2', 's1_alt');
    
    assert.strictEqual(actualCalls.length, 1, 'switchTake should make one fetch call');
    assert.strictEqual(actualCalls[0].url, '/intent', 'should call /intent endpoint');
    assert.strictEqual(actualCalls[0].method, 'POST', 'should use POST method');
    assert.strictEqual(actualCalls[0].body.intent_type, 'switch_take', 'should set correct intent type');
    assert.strictEqual(actualCalls[0].body.take_id, 't2', 'should pass correct take ID');
    assert.strictEqual(actualCalls[0].body.segment_id, 's1_alt', 'should pass correct segment ID');
    
    console.log('✓ test_switch_take_intent passed');
}

function test_payload_structure() {
    resetCalls();
    selectSegment('s1');
    
    var payload = actualCalls[0].body;
    assert.strictEqual(typeof payload, 'object', 'payload should be an object');
    assert.strictEqual(typeof payload.intent_type, 'string', 'intent_type should be a string');
    assert.strictEqual(typeof payload.segment_id, 'string', 'segment_id should be a string');
    
    console.log('✓ test_payload_structure passed');
}

function test_multiple_intents() {
    resetCalls();
    selectSegment('s1');
    switchTake('t2', 's1_alt');
    
    assert.strictEqual(actualCalls.length, 2, 'multiple intents should make multiple fetch calls');
    assert.strictEqual(actualCalls[0].body.intent_type, 'select_segment', 'first call should be select_segment');
    assert.strictEqual(actualCalls[1].body.intent_type, 'switch_take', 'second call should be switch_take');
    
    console.log('✓ test_multiple_intents passed');
}

console.log('Running JavaScript intent tests...\n');

try {
    test_select_segment_intent();
    test_switch_take_intent();
    test_payload_structure();
    test_multiple_intents();
    
    console.log('\n✓ All JavaScript tests passed!');
    process.exit(0);
} catch (e) {
    console.error('\n✗ Test failed:', e.message);
    process.exit(1);
}
