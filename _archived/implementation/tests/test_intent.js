const assert = require('assert');
const path = require('path');
const { JSDOM } = require('jsdom');

var actualCalls = [];

function createMockFetch() {
    return function(url, options) {
        actualCalls.push({
            url: url,
            method: options.method,
            body: JSON.parse(options.body)
        });
    return Promise.resolve({ ok: true });
    };
}

global.fetch = createMockFetch();
global.window = global.window;

const projectRoot = path.resolve(__dirname, '..');
const intentPath = path.join(projectRoot, 'static', 'js', 'intent.js');
const { setupIntentHandlers, selectSegment, switchTake, sendIntent, updateSelectionIndicator } = require(intentPath);
