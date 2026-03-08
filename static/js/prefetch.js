const PREFETCH_SIZE = 20;
const prefetchQueue = [];
let pendingFetches = 0;

function randomCodePoint() {
  const range = UNICODE_RANGES[Math.floor(Math.random() * UNICODE_RANGES.length)];
  return range[0] + Math.floor(Math.random() * (range[1] - range[0] + 1));
}

async function prefetchOne() {
  pendingFetches++;
  const cp = randomCodePoint();
  const c = String.fromCodePoint(cp);
  try {
    const res = await fetch(`/api/char?c=${encodeURIComponent(c)}`);
    const data = await res.json();
    if (!data.error) prefetchQueue.push({ char: c, data });
  } catch (e) { /* silently drop failed prefetches */ }
  pendingFetches--;
}

function fillPrefetchQueue() {
  const needed = PREFETCH_SIZE - prefetchQueue.length - pendingFetches;
  for (let i = 0; i < needed; i++) prefetchOne();
}

fillPrefetchQueue();
