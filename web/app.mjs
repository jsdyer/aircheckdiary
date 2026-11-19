import {clock, fields, slotAt, titleHits} from './model.mjs';
const el = id => document.getElementById(id);
const node = (tag, text, cls) => {
  const element = document.createElement(tag);
  if (text != null) element.textContent = text;
  if (cls) element.className = cls;
  return element;
};
const button = (label, cls, act) => {
  const b = node('button', label, cls); b.type = 'button'; b.addEventListener('click', act); return b;
};
const number = n => n.toLocaleString('en-CA');
const dateLabel = day => new Date(day + 'T12:00:00Z').toLocaleDateString('en-CA',
  {weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC'});
const typeNames = {PGR:'Program', PFS:'First segment', SEG:'Segment', PGI:'Paid program', COM:'Commercial',
  PRO:'Promotion', PRC:'Canadian program promotion', NRN:'Non-commercial spot'};
let archive, state, dayA, dayB, titleIndex, version = 0, searchLimit = 20;
const cache = new Map();
async function data(path) {
  if (!cache.has(path)) {
    const pending = (async () => {
      const response = await fetch('./data/' + path);
      if (!response.ok) throw new Error('Could not load ' + path);
      if (!path.endsWith('.gz')) return await response.json();
      // Some hosts automatically decode .gz. Accept either response body.
      const bytes = await response.arrayBuffer();
      if (new Uint8Array(bytes)[0] !== 31) return JSON.parse(new TextDecoder().decode(bytes));
      return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
    })().catch(error => {cache.delete(path); throw error;});
    cache.set(path, pending);
    if (cache.size > 14) cache.delete(cache.keys().next().value);
  }
  return cache.get(path);
}
function currentEdition() { return archive.editions.find(m => m.month === state.date.slice(0, 7)); }
function setUrl() {
  const u = new URL(location.href);
  for (const [key, value] of Object.entries(state)) u.searchParams.set(key, value);
  history.replaceState({}, '', u);
}
function move(t) { state.t = t; setUrl(); draw(); }
function option(select, value, label) {select.add(new Option(label, value));}
function updateMenus() {
  el('date').value = state.date;
  for (const key of ['a','b']) {
    const select = el(key);
    select.value = state[key];
    for (const o of select.options) o.disabled = o.value === state[key === 'a' ? 'b' : 'a'];
  }
}
function sourceRecords(day, indices, station, label) {
  const box = node('details', null, 'detail');
  box.append(node('summary', label + ' (' + number(indices.length) + ')'));
  const list = node('div', null, 'rowlist');
  const file = currentEdition().files[station].split(/[/\\]/).pop();
  box.addEventListener('toggle', () => {
    if (!box.open || list.childElementCount) return;
    list.append(node('p', file, 'timecode'));
    for (const i of indices) {
      const [lineNo, raw] = day.rows[i];
      const f = fields(raw);
      const record = node('details', null, 'rawrow');
      const stamp = f.start.slice(0,2) + ':' + f.start.slice(2,4) + ':' + f.start.slice(4);
      record.append(node('summary', '#' + lineNo + ' · ' + stamp + ' · ' + f.type + ' · ' + f.title),
        node('p', (typeNames[f.type] || 'Source record') + (f.episode ? ' · ' + f.episode : '')), node('pre', raw));
      list.append(record);
    }
  });
  box.append(list); return box;
}
function stationCard(station, day) {
  const info = archive.stations[station];
  const card = node('article', null, 'card');
  const head = node('header', null, 'cardhead');
  head.append(node('span', station, 'stationcode'), node('small', info.network + ' · ' + info.city)); card.append(head);
  const index = slotAt(day, state.t), slot = day.slots[index];
  const content = node('div', null, 'slot');
  if (!slot) {
    content.append(node('h3', 'No matching slot'), node('p', 'This station has no program covering that local time on the selected reporting date.'));
    card.append(content); return card;
  }
  const record = fields(day.rows[slot.i][1]);
  content.append(node('div', clock(slot.from) + ' – ' + clock(slot.to), 'slotlabel'), node('h3', record.title),
    node('p', [record.episode, typeNames[record.type]].filter(Boolean).join(' · '), 'episode'));
  const neighbors = node('div', null, 'neighbors');
  for (const [offset, label] of [[-1, 'Before'], [1, 'After']]) {
    const other = day.slots[index + offset];
    if (!other) continue;
    const b = button('', 'neighbor', () => move(other.from));
    b.append(node('span', label + ' · ' + clock(other.from)), document.createTextNode('  ' + fields(day.rows[other.i][1]).title));
    neighbors.append(b);
  }
  content.append(neighbors); card.append(content, sourceRecords(day, slot.items, station, 'Inspect source rows'));
  return card;
}
function fullSchedule(station, day) {
  const s = node('details', null, 'schedule');
  s.append(node('summary', station + ' · ' + day.slots.length + ' program starts'));
  const box = node('div');
  box.append(node('p', 'Reporting day begins at ' + clock(day.boundary) + ' · ' + archive.stations[station].zone, 'timecode'));
  for (const slot of day.slots) {
    const b = button('', 'listing', () => {move(slot.from); el('comparison').scrollIntoView({block:'start'});});
    b.append(node('span', clock(slot.from), 'timecode'), node('b', fields(day.rows[slot.i][1]).title)); box.append(b);
  }
  if (day.outside.length) box.append(sourceRecords(day, day.outside, station, 'Rows outside program slots'));
  s.append(box); return s;
}
function draw() {
  const times = [...new Set([state.t, ...dayA.slots.map(x => x.from), ...dayB.slots.map(x => x.from)])].sort((a,b) => a-b);
  const select = el('time'); select.replaceChildren();
  for (const t of times) option(select, t, clock(t));
  select.value = String(state.t);
  el('when').textContent = dateLabel(state.date) + ' · ' + clock(state.t) + ' on each station clock';
  el('cards').replaceChildren(stationCard(state.a, dayA), stationCard(state.b, dayB));
  el('schedules').replaceChildren(fullSchedule(state.a, dayA), fullSchedule(state.b, dayB));
}
function search() {
  const query = el('query').value.trim();
  const hits = titleHits(titleIndex || {}, query);
  el('matchCount').textContent = query ? number(hits.length) + (hits.length === 1 ? ' matching airing' : ' matching airings') +
    (hits.length > searchLimit ? ' · showing ' + searchLimit : '') : '';
  const matches = el('matches'); matches.replaceChildren();
  for (const hit of hits.slice(0,searchLimit)) {
    const b = button('', 'hit', async () => {
      const secondary = state.a === hit.station ? state.b : state.a;
      state = {...state, a:hit.station, b:secondary, date:hit.date, t:hit.t};
      await load(); el('comparison').scrollIntoView({block:'start'});
    });
    b.append(node('span', hit.station + ' · ' + dateLabel(hit.date) + ' · ' + clock(hit.t), 'timecode'),
      node('b', hit.title)); matches.append(b);
  }
  el('more').hidden = hits.length <= searchLimit;
}
async function load() {
  const run = ++version, {date, a, b} = state;
  updateMenus(); setUrl();
  el('notice').textContent = 'Opening station logs…';
  const month = date.slice(0,7);
  try {
    const inputs = await Promise.all([data(month + '/' + a + '/' + date + '.json.gz'),
      data(month + '/' + b + '/' + date + '.json.gz'), data(month + '/titles.json.gz')]);
    if (run !== version) return;
    [dayA, dayB, titleIndex] = inputs;
    const m = currentEdition();
    el('zipLink').href = m.url;
    el('coverage').textContent = 'Source period ' + m.first + ' through ' + m.last + '. Retrieved ' + m.retrieved +
      '. Four of ' + m.archiveLogs + ' station files cover ' + number(m.stationDays) + ' station-days, ' +
      number(m.count) + ' program starts and ' + number(m.rows) + ' source rows.';
    el('searchLabel').textContent = 'Search all four stations for ' + new Date(date + 'T12:00:00Z').toLocaleDateString('en-CA',
      {month:'long',year:'numeric',timeZone:'UTC'});
    el('notice').textContent = ''; draw(); search();
  } catch (error) {
    if (run !== version) return;
    el('cards').replaceChildren(); el('schedules').replaceChildren(); el('matches').replaceChildren();
    el('notice').textContent = error.message + '. Reload to try again.';
  }
}
async function init() {
  archive = await data('archive.json');
  const dates = archive.editions.flatMap(m => m.dates);
  const p = new URLSearchParams(location.search);
  const stations = Object.keys(archive.stations);
  const a = stations.includes(p.get('a')) ? p.get('a') : 'CJCH';
  const b = stations.includes(p.get('b')) && p.get('b') !== a ? p.get('b') : (a === 'CIVT' ? 'CJCH' : 'CIVT');
  const t = p.has('t') ? Number(p.get('t')) : 72000;
  state = {a,b,date:dates.includes(p.get('date')) ? p.get('date') : archive.editions.at(-1).first,
    t:Number.isInteger(t) && t >= 0 && t < 172800 ? t : 72000};
  for (const day of dates) option(el('date'), day, dateLabel(day));
  for (const key of ['a','b']) for (const station of stations) option(el(key), station, station + ' · ' + archive.stations[station].city);
  for (const key of ['date','a','b']) el(key).onchange = () => {state[key] = el(key).value; load();};
  el('time').onchange = () => move(Number(el('time').value));
  el('query').oninput = () => {searchLimit = 20; search();};
  el('more').onclick = () => {searchLimit += 20; search();};
  el('share').onclick = async () => {
    try {await navigator.clipboard.writeText(location.href); el('notice').textContent = 'Comparison link copied.';}
    catch {el('notice').replaceChildren(document.createTextNode('Copy this comparison address '));
      const u = node('input'); u.readOnly = true; u.value = location.href; u.setAttribute('aria-label','Comparison link');
      el('notice').append(u); u.select();}
  };
  await load();
}
init().catch(error => {el('notice').textContent = 'Archive could not open. ' + error.message;});
