export function clock(seconds) {
  const h = Math.floor(seconds / 3600) % 24;
  const m = Math.floor(seconds / 60) % 60;
  const s = seconds % 60;
  const time = (h % 12 || 12) + ':' + String(m).padStart(2, '0') +
    (s ? ':' + String(s).padStart(2, '0') : '') + (h < 12 ? ' a.m.' : ' p.m.');
  return time + (seconds >= 86400 ? ' · next day' : '');
}
export function fields(line) {
  return {type: line.slice(1, 4), title: line.slice(36, 86).trim(),
    episode: line.slice(86, 136).trim(), start: line.slice(18, 24), end: line.slice(24, 30).trim(),
    duration: line.slice(30, 36)};
}
export function slotAt(day, t) {
  return day.slots.findLastIndex(slot => slot.from <= t && t < slot.to);
}
export function titleHits(index, query) {
  const folded = value => value.normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase('en-CA');
  const term = folded(query.trim());
  if (!term) return [];
  return Object.entries(index).filter(([title]) => folded(title).includes(term))
    .flatMap(([title, rows]) => rows.map(([station, date, t]) => ({title, station, date, t})))
    .sort((a, b) => a.date.localeCompare(b.date) || a.t - b.t || a.station.localeCompare(b.station));
}
