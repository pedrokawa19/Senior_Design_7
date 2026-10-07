// Run with: node --test dashboard/tests/history_ui.test.cjs
// Exercise the actual template script against a minimal DOM and synthetic API.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname, '../../templates/history.html'), 'utf8')
  .match(/<script>([\s\S]*?)<\/script>/)[1];
const settle = () => new Promise(resolve => setImmediate(resolve));

function setup(inventory = false) {
  const pageSize = inventory ? 50 : 100;
  const nodes = new Map();
  const node = selector => {
    if (!nodes.has(selector)) nodes.set(selector, {
      innerHTML: '', textContent: '', disabled: false, fields: {}, handlers: {},
      setAttribute() {}, addEventListener(event, fn) { this.handlers[event] = fn; },
    });
    return nodes.get(selector);
  };
  const requests = [], timers = [];
  const state = { fail: false, total: 1000, pending: false };
  const context = {
    document: { querySelector: node }, URLSearchParams, AbortController, Date,
    FormData: class { constructor(form) { return Object.entries(form.fields); } },
    setTimeout(fn, delay) { timers.push({ fn, delay }); return timers.length; },
    clearTimeout() {},
    fetch: async (url, options) => {
      requests.push({ url, options });
      if (state.pending) return new Promise(() => {});
      const query = new URLSearchParams(url.split('?')[1]);
      const page = Math.min(Number(query.get('page')), Math.max(1, Math.ceil(state.total / pageSize)));
      const count = Math.min(pageSize, Math.max(0, state.total - (page - 1) * pageSize));
      return { ok: !state.fail, json: async () => state.fail ? { detail: 'Synthetic failure' } : {
        page, page_count: Math.max(1, Math.ceil(state.total / pageSize)), page_size: pageSize,
        total_rows: state.total, row_count: count, max_rows: 1000,
        columns: ['ID'], rows: Array.from({ length: count }, (_, i) => [i === 0 ? '<script>unsafe</script>' : i]),
        column_labels: inventory ? ['Tag key'] : undefined,
        refreshed_at: new Date().toISOString(),
        expires_at: inventory ? null : new Date(Date.now() + 3600000).toISOString(),
        ...(inventory ? { max_rows: undefined } : {}),
      } };
    },
  };
  vm.runInNewContext(script.replace(
    "{{ page_title|default:'History'|escapejs }}", inventory ? 'Inventory' : 'History',
  ), context);
  return { node, requests, timers, state };
}

test('loading, paging, escaping, timestamp and automatic refresh', async () => {
  const { node, requests, timers } = setup();
  assert.match(node('#history-content').innerHTML, /Loading/);
  assert.equal(node('#next-page').disabled, true);
  await settle();
  assert.match(node('#history-content').innerHTML, /Showing 1–100 of 1000/);
  assert.match(node('#history-content').innerHTML, /&lt;script&gt;/);
  assert.match(node('#last-refreshed').textContent, /Last Refreshed · /);
  assert.equal(node('#previous-page').disabled, true);
  assert.equal(node('#next-page').disabled, false);
  await node('#next-page').onclick();
  assert.match(requests.at(-1).url, /page=2/);
  assert.equal(node('#page-number').value, '2');
  assert.equal(node('#page-status').textContent, 'of 10');
  assert.ok(timers.at(-1).delay > 3599000 && timers.at(-1).delay < 3601000);
  await timers.at(-1).fn();
  assert.match(requests.at(-1).url, /page=2/);
});

test('filter apply resets page, manual refresh preserves filters, clear removes them', async () => {
  const { node, requests } = setup();
  await settle();
  await node('#next-page').onclick();
  node('#history-filters').fields = { item: 'steel & coil', party: 'Synthetic', start_date: '2026-01-01' };
  node('#history-filters').handlers.submit({ preventDefault() {} });
  await settle();
  let query = new URLSearchParams(requests.at(-1).url.split('?')[1]);
  assert.equal(query.get('page'), '1');
  assert.equal(query.get('item'), 'steel & coil');
  await node('#refresh-history').onclick();
  query = new URLSearchParams(requests.at(-1).url.split('?')[1]);
  assert.equal(query.get('refresh'), '1');
  assert.equal(query.get('party'), 'Synthetic');
  node('#history-filters').handlers.reset();
  await settle();
  assert.equal(new URLSearchParams(requests.at(-1).url.split('?')[1]).has('item'), false);
});

test('empty results, final page and recoverable refresh failure', async () => {
  const { node, state } = setup();
  await settle();
  state.total = 101;
  await node('#next-page').onclick();
  assert.match(node('#history-content').innerHTML, /Showing 101–101 of 101/);
  assert.equal(node('#next-page').disabled, true);
  state.total = 0;
  await node('#refresh-history').onclick();
  assert.match(node('#history-content').innerHTML, /No history matches/);
  assert.equal(node('#previous-page').disabled, true);
  state.fail = true;
  await node('#refresh-history').onclick();
  assert.equal(node('#history-error').textContent, 'Synthetic failure');
  assert.equal(node('#refresh-history').disabled, false);
  assert.equal(node('#next-page').disabled, true);
  state.fail = false;
  await node('#refresh-history').onclick();
  assert.equal(node('#history-error').textContent, '');
});


test('first/last arrows and editable page number respect boundaries', async () => {
  const { node, requests } = setup();
  await settle();
  assert.equal(node('#first-page').disabled, true);
  await node('#last-page').onclick();
  assert.match(requests.at(-1).url, /page=10/);
  assert.equal(node('#last-page').disabled, true);
  assert.equal(node('#next-page').disabled, true);
  assert.equal(node('#page-number').value, '10');
  await node('#first-page').onclick();
  assert.equal(node('#page-number').value, '1');
  node('#page-number').value = '5';
  node('#page-number').handlers.keydown({ key: 'Enter', preventDefault() {} });
  await settle();
  assert.match(requests.at(-1).url, /page=5/);
  const count = requests.length;
  for (const invalid of ['0', '11', '1.5', '']) {
    node('#page-number').value = invalid;
    node('#page-number').handlers.change();
    assert.equal(node('#page-number').value, '5');
  }
  assert.equal(requests.length, count);
  node('#page-number').value = '3';
  node('#page-number').handlers.change();
  await settle();
  assert.match(requests.at(-1).url, /page=3/);
});


test('headers cycle ascending, descending, original and retain sorting across pages', async () => {
  const { node, requests } = setup();
  await settle();
  const clickColumn = async column => {
    node('#history-content').handlers.click({ target: {
      closest: () => ({ dataset: { sortColumn: String(column) } }),
    } });
    await settle();
  };
  const query = () => new URLSearchParams(requests.at(-1).url.split('?')[1]);
  await clickColumn(0);
  assert.equal(query().get('sort_direction'), 'asc');
  assert.match(node('#history-content').innerHTML, /aria-sort="ascending"/);
  await node('#next-page').onclick();
  assert.equal(query().get('page'), '2');
  assert.equal(query().get('sort_direction'), 'asc');
  await clickColumn(0);
  assert.equal(query().get('sort_direction'), 'desc');
  assert.equal(query().get('page'), '1');
  assert.match(node('#history-content').innerHTML, /Restore original order/);
  await clickColumn(0);
  assert.equal(query().has('sort_column'), false);
  assert.equal(query().has('sort_direction'), false);
  assert.match(node('#history-content').innerHTML, /aria-sort="none"/);
  await clickColumn(0);
  await clickColumn(1);
  assert.equal(query().get('sort_column'), '1');
  assert.equal(query().get('sort_direction'), 'asc');
});

test('inventory uses readable headings, full pagination and explicit refresh without a snapshot timer', async () => {
  const { node, requests, timers, state } = setup(true);
  assert.match(node('#history-content').innerHTML, /Loading inventory/);
  await settle();
  assert.match(node('#history-content').innerHTML, /Tag key/);
  assert.match(node('#history-content').innerHTML, /Showing 1–50 of 1000/);
  assert.equal(node('#page-status').textContent, 'of 20');
  assert.equal(node('#page-number').max, '20');
  await node('#next-page').onclick();
  assert.match(node('#history-content').innerHTML, /Showing 51–100 of 1000/);
  assert.doesNotMatch(node('#history-content').innerHTML, /limit reached/);
  assert.equal(timers.length, 0);
  state.total = 1201;
  await node('#last-page').onclick();
  await node('#last-page').onclick();
  assert.match(requests.at(-1).url, /page=25/);
  assert.equal(node('#page-status').textContent, 'of 25');
  assert.equal(node('#page-number').max, '25');
  assert.match(node('#history-content').innerHTML, /Showing 1201–1201 of 1201/);
  state.total = 0;
  await node('#refresh-history').onclick();
  assert.match(node('#history-content').innerHTML, /No current inventory records/);
  assert.match(requests.at(-1).url, /refresh=1/);
  state.fail = true;
  await node('#refresh-history').onclick();
  assert.equal(node('#history-error').textContent, 'Synthetic failure');
  assert.equal(node('#refresh-history').disabled, false);
});
