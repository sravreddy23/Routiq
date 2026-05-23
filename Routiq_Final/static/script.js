async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function fitCanvas(canvas) {
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = Math.max(600, Math.floor(rect.width));
  canvas.height = Math.floor(canvas.offsetHeight) || 540;
}

function clearCanvas(ctx, canvas) {
  ctx.fillStyle = '#0b1120';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawGraphOnCanvas(ctx, canvas, data, opts = {}) {
  const nodes = data.nodes || {};
  const edges = data.edges || [];
  const path = new Set((data.path || []).map(String));
  const visitedSet = new Set((opts.visited || []).map(String));

  const names = Object.keys(nodes);
  if (!names.length) return;

  let xs = [], ys = [];
  for (const n of names) { xs.push(nodes[n][0]); ys.push(nodes[n][1]); }
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);

  const padding = 48;
  const cx = canvas.width / 2, cy = canvas.height / 2;
  const xSpan = Math.max(1, maxX - minX);
  const ySpan = Math.max(1, maxY - minY);
  const scaleX = (canvas.width - 2 * padding) / xSpan;
  const scaleY = (canvas.height - 2 * padding) / ySpan;
  const baseScale = Math.min(scaleX, scaleY);
  const zoom = parseFloat(opts.zoom || 1.6);
  const scale = baseScale * zoom;

  let panX = opts.panX ?? (minX + maxX) / 2;
  let panY = opts.panY ?? (minY + maxY) / 2;

  const toCanvas = (x, y) => [(x - panX) * scale + cx, (y - panY) * scale + cy];

  clearCanvas(ctx, canvas);

  // Draw regular edges
  ctx.lineWidth = 1.2;
  ctx.strokeStyle = 'rgba(71,85,105,0.45)';
  for (const e of edges) {
    if (!nodes[e.u] || !nodes[e.v]) continue;
    const [x1, y1] = toCanvas(nodes[e.u][0], nodes[e.u][1]);
    const [x2, y2] = toCanvas(nodes[e.v][0], nodes[e.v][1]);
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }

  // Draw path edges
  if (opts.pathArray && opts.pathArray.length > 1) {
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = '#ef4444';
    ctx.shadowColor = '#ef4444';
    ctx.shadowBlur = 6;
    for (let i = 0; i < opts.pathArray.length - 1; i++) {
      const a = opts.pathArray[i], b = opts.pathArray[i + 1];
      if (!nodes[a] || !nodes[b]) continue;
      const [x1, y1] = toCanvas(nodes[a][0], nodes[a][1]);
      const [x2, y2] = toCanvas(nodes[b][0], nodes[b][1]);
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    }
    ctx.shadowBlur = 0;
  }

  const nodeR = 7;

  // Draw nodes
  for (const n of names) {
    const [x, y] = toCanvas(nodes[n][0], nodes[n][1]);
    let fill = '#334155';
    let glow = null;
    if (opts.currentNode === n) { fill = '#22c55e'; glow = '#22c55e'; }
    else if (path.has(n)) { fill = '#ef4444'; glow = '#ef4444'; }
    else if (visitedSet.has(n)) { fill = '#f59e0b'; }

    if (glow) { ctx.shadowColor = glow; ctx.shadowBlur = 10; }
    ctx.beginPath();
    ctx.arc(x, y, nodeR, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#0b1120';
    ctx.stroke();
    if (glow) ctx.shadowBlur = 0;
  }

  // Draw labels for path/current nodes
  ctx.font = 'bold 11px Segoe UI, Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (const n of names) {
    if (path.has(n) || opts.currentNode === n) {
      const [x, y] = toCanvas(nodes[n][0], nodes[n][1]);
      ctx.lineWidth = 3.5;
      ctx.strokeStyle = '#0b1120';
      ctx.strokeText(n, x, y - nodeR - 8);
      ctx.fillStyle = 'white';
      ctx.fillText(n, x, y - nodeR - 8);
    }
  }
}

function setStatus(text, type) {
  const badge = document.getElementById('statusBadge');
  badge.textContent = text;
  badge.className = 'badge badge-' + type;
}

function showResults(data) {
  const placeholder = document.getElementById('resultPlaceholder');
  const content = document.getElementById('resultContent');
  const stepCard = document.getElementById('stepCard');

  placeholder.style.display = 'none';
  content.style.display = 'block';

  const path = data.path || [];
  const visited = data.visited || [];

  document.getElementById('statCost').textContent =
    data.total_cost != null ? Math.round(data.total_cost) + ' km' : path.length + ' hops';
  document.getElementById('statStops').textContent = Math.max(0, path.length - 1);
  document.getElementById('statVisited').textContent = visited.length;

  // Build path list
  const pathList = document.getElementById('pathList');
  pathList.innerHTML = '';
  path.forEach((city, i) => {
    const div = document.createElement('div');
    div.className = 'path-step' + (i === 0 ? ' start' : i === path.length - 1 ? ' end' : '');
    div.innerHTML = `<span class="path-num">${i + 1}</span><span class="path-city">${city}</span>`;
    if (i < path.length - 1) {
      const arr = document.createElement('span');
      arr.className = 'path-arrow';
      arr.textContent = '↓';
      div.appendChild(arr);
    }
    pathList.appendChild(div);
  });

  // Build traversal list
  if (visited.length) {
    stepCard.style.display = 'block';
    const travList = document.getElementById('traversalList');
    travList.innerHTML = '';
    visited.forEach((city, i) => {
      const div = document.createElement('div');
      div.className = 'trav-step' + (path.includes(city) ? ' active' : '');
      div.innerHTML = `<span class="trav-idx">${i + 1}</span><span>${city}</span>`;
      travList.appendChild(div);
    });
  }
}

function resetResults() {
  document.getElementById('resultPlaceholder').style.display = '';
  document.getElementById('resultContent').style.display = 'none';
  document.getElementById('stepCard').style.display = 'none';
  setStatus('Idle', 'idle');
}

async function init() {
  const cities = await fetchJSON('/cities');
  const s = document.getElementById('source');
  const d = document.getElementById('destination');
  cities.forEach(c => {
    s.add(new Option(c, c));
    d.add(new Option(c, c));
  });
  s.selectedIndex = 0;
  d.selectedIndex = cities.length - 1;

  const canvas = document.getElementById('graphCanvas');
  fitCanvas(canvas);
  const ctx = canvas.getContext('2d');
  let currentGraph = null;
  let pan = { x: null, y: null };

  window.addEventListener('resize', () => {
    fitCanvas(canvas);
    if (currentGraph) drawGraphOnCanvas(ctx, canvas, currentGraph, {
      zoom: zoomEl.value, panX: pan.x, panY: pan.y, pathArray: currentGraph.path
    });
  });

  const zoomEl = document.getElementById('zoom');
  const zoomVal = document.getElementById('zoomVal');
  zoomEl.addEventListener('input', () => {
    zoomVal.textContent = parseFloat(zoomEl.value).toFixed(1) + '×';
    if (currentGraph) drawGraphOnCanvas(ctx, canvas, currentGraph, {
      zoom: zoomEl.value, panX: pan.x, panY: pan.y, pathArray: currentGraph.path
    });
  });

  async function loadAndRender(source, destination) {
    const q = new URLSearchParams();
    if (source) q.set('source', source);
    if (destination) q.set('destination', destination);
    const data = await fetchJSON('/graph_data?' + q.toString());
    currentGraph = data;
    const xs = Object.values(data.nodes).map(p => p[0]);
    const ys = Object.values(data.nodes).map(p => p[1]);
    pan.x = (Math.min(...xs) + Math.max(...xs)) / 2;
    pan.y = (Math.min(...ys) + Math.max(...ys)) / 2;
    drawGraphOnCanvas(ctx, canvas, data, {
      zoom: zoomEl.value, panX: pan.x, panY: pan.y, pathArray: data.path
    });
    return data;
  }

  document.getElementById('find').addEventListener('click', async () => {
    const source = s.value, destination = d.value;
    if (source === destination) {
      setStatus('Same city', 'error');
      return;
    }
    setStatus('Searching…', 'running');
    try {
      const data = await loadAndRender(source, destination);
      if (!data.path || !data.path.length) {
        setStatus('No path found', 'error');
        return;
      }

      showResults(data);
      setStatus('Animating…', 'running');

      // Animate traversal
      const visited = data.visited || [];
      let i = 0;
      if (window._animInterval) clearInterval(window._animInterval);

      function frame() {
        const vis = visited.slice(0, i + 1);
        const current = vis.length ? vis[vis.length - 1] : null;
        drawGraphOnCanvas(ctx, canvas, data, {
          zoom: zoomEl.value, panX: pan.x, panY: pan.y,
          pathArray: data.path, visited: vis, currentNode: current
        });

        // Highlight current traversal step
        const items = document.querySelectorAll('.trav-step');
        items.forEach((el, idx) => {
          el.style.opacity = idx <= i ? '1' : '0.35';
        });

        i++;
        if (i > visited.length) {
          clearInterval(window._animInterval);
          window._animInterval = null;
          setStatus('Done', 'done');
        }
      }
      frame();
      window._animInterval = setInterval(frame, 400);
    } catch (e) {
      setStatus('Error', 'error');
      console.error(e);
    }
  });

  document.getElementById('reset').addEventListener('click', () => {
    if (window._animInterval) { clearInterval(window._animInterval); window._animInterval = null; }
    zoomEl.value = 1.6;
    zoomVal.textContent = '1.6×';
    resetResults();
    loadAndRender(s.value, d.value);
  });

  // Click to zoom (pointer-anchored)
  canvas.addEventListener('click', ev => {
    if (!currentGraph) return;
    const rect = canvas.getBoundingClientRect();
    const cx = canvas.width / 2, cy = canvas.height / 2;
    const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
    const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

    const xs = Object.values(currentGraph.nodes).map(p => p[0]);
    const ys = Object.values(currentGraph.nodes).map(p => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const padding = 48;
    const scaleX = (canvas.width - 2 * padding) / Math.max(1, maxX - minX);
    const scaleY = (canvas.height - 2 * padding) / Math.max(1, maxY - minY);
    const baseScale = Math.min(scaleX, scaleY);
    const currentZoom = parseFloat(zoomEl.value);
    const scale = baseScale * currentZoom;
    const dataX = (x - cx) / scale + pan.x;
    const dataY = (y - cy) / scale + pan.y;
    const newZoom = Math.min(parseFloat(zoomEl.max), currentZoom * 1.2);
    const newScale = baseScale * newZoom;
    pan.x = dataX - (x - cx) / newScale;
    pan.y = dataY - (y - cy) / newScale;
    zoomEl.value = newZoom;
    zoomVal.textContent = parseFloat(newZoom).toFixed(1) + '×';
    drawGraphOnCanvas(ctx, canvas, currentGraph, {
      zoom: zoomEl.value, panX: pan.x, panY: pan.y, pathArray: currentGraph.path
    });
  });

  await loadAndRender(s.value, d.value);
}

init().catch(err => {
  console.error('Init error:', err);
  setStatus('Init error', 'error');
});
