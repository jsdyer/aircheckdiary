import test from 'node:test';
import assert from 'node:assert/strict';
import {clock, fields, slotAt, titleHits} from '../web/model.mjs';
test('local clock distinguishes midnight and next day', () => {
  assert.equal(clock(72000), '8:00 p.m.');
  assert.equal(clock(86401), '12:00:01 a.m. · next day');
});
test('slot endpoints and source gaps', () => {
  const day = {slots:[{from:100,to:130},{from:130,to:151}]};
  assert.equal(slotAt(day, 130), 1);
  assert.equal(slotAt(day, 151), -1);
});
test('title index searches exact source spellings accent-insensitively', () => {
  assert.equal(titleHits({'Épisode spécial':[['CBHT','2026-09-10',72000]]},'episode')[0].station,'CBHT');
  assert.equal(titleHits({},'x').length,0);
});
