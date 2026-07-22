const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT ?? 3747;
const EVENTS_FILE = process.env.EVENTS_FILE ?? path.join(process.env.USERPROFILE, '.claude', 'events.jsonl');
const DASHBOARD_FILE = path.join(__dirname, 'dashboard.html');
const GRAPH_FILE = process.env.GRAPH_PATH ?? path.join(__dirname, 'graphify-out', 'graph.json');
const PROJECT_NAME = process.env.PROJECT_NAME ?? path.basename(__dirname);
// Base dir where all projects live — used to resolve a project's graph on demand
// (/graph.json?project=X → PROJECTS_ROOT/X/graphify-out/graph.json).
const PROJECTS_ROOT = process.env.PROJECTS_ROOT ?? path.dirname(__dirname);

// Resolve the graph file for a given project name (falls back to central GRAPH_FILE).
function graphPathFor(project) {
  if (!project || project === PROJECT_NAME) return GRAPH_FILE;
  return path.join(PROJECTS_ROOT, project, 'graphify-out', 'graph.json');
}

// Ensure events file exists
if (!fs.existsSync(EVENTS_FILE)) fs.writeFileSync(EVENTS_FILE, '', 'utf8');

// ─── HTTP SERVER ──────────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/dashboard.html' || req.url.startsWith('/dashboard.html?')) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    fs.createReadStream(DASHBOARD_FILE).pipe(res);
  } else if (req.url === '/graph.json' || req.url.startsWith('/graph.json?')) {
    const project = new URL(req.url, 'http://localhost').searchParams.get('project');
    const file = graphPathFor(project);
    if (!fs.existsSync(file)) {
      res.writeHead(404); res.end('graph.json not found'); return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    fs.createReadStream(file).pipe(res);
  } else if (req.url.startsWith('/imagens/') && req.url.endsWith('.png')) {
    const name = path.basename(req.url); // strips any ../ — only files directly in imagens/
    const file = path.join(__dirname, 'imagens', name);
    if (!fs.existsSync(file)) {
      res.writeHead(404); res.end('image not found'); return;
    }
    res.writeHead(200, { 'Content-Type': 'image/png', 'Cache-Control': 'max-age=3600' });
    fs.createReadStream(file).pipe(res);
  } else if (req.url === '/project-name') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ name: PROJECT_NAME }));
  } else if (req.method === 'POST' && req.url === '/events') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const projectName = req.headers['x-project-name'] || PROJECT_NAME;
        const event = JSON.parse(body);
        event.projectName = projectName;
        event.timestamp = event.timestamp || new Date().toISOString();
        const line = JSON.stringify(event) + '\n';
        fs.appendFileSync(EVENTS_FILE, line, 'utf8');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
  } else if (req.method === 'POST' && req.url === '/restart') {
    res.writeHead(200); res.end('ok');
    setTimeout(() => process.exit(0), 80);
  } else {
    res.writeHead(404); res.end('Not found');
  }
});

// ─── WEBSOCKET SERVER ─────────────────────────────────────────────────────────
const wss = new WebSocketServer({ server });
const clients = new Set();
const clientState = new Map(); // ws → { isFirst: true, project: 'nome-do-projeto' }

wss.on('connection', ws => {
  clients.add(ws);
  const urlParams = new URL(`http://localhost${ws.upgradeReq?.url || '/'}`).searchParams;
  const project = urlParams.get('project') || PROJECT_NAME;
  clientState.set(ws, { isFirst: true, project });

  ws.on('message', raw => {
    try {
      const msg = JSON.parse(raw);
      if (msg.type === 'subscribe') {
        const state = clientState.get(ws) || {};
        state.project = msg.project || PROJECT_NAME;
        clientState.set(ws, state);
        return;
      }
      if (msg.type !== 'chat' || !msg.prompt) return;

      const state = clientState.get(ws) || { isFirst: true };
      const args = ['-p'];
      if (!state.isFirst) args.push('--continue');
      if (msg.model) args.push('--model', msg.model);
      state.isFirst = false;
      clientState.set(ws, state);

      const proc = spawn('claude', args, { shell: true });
      proc.stdin.write(msg.prompt + '\n');
      proc.stdin.end();
      proc.stdout.on('data', chunk => {
        if (ws.readyState === 1)
          ws.send(JSON.stringify({ type: 'chat_token', content: chunk.toString() }));
      });
      // Line-buffered stderr: chunks can split a message mid-line, so we accumulate
      // and only decide per complete line. Hook lifecycle noise from -p mode
      // (SessionEnd/serena-hooks cleanup) is dropped; real errors still surface.
      let errBuf = '';
      const HOOK_NOISE = /hook|serena-hooks|Hook cancelled/i;
      const flushErr = (line) => {
        if (!line.trim() || HOOK_NOISE.test(line)) return;
        if (ws.readyState === 1)
          ws.send(JSON.stringify({ type: 'chat_token', content: `[erro] ${line}\n` }));
      };
      proc.stderr.on('data', chunk => {
        errBuf += chunk.toString();
        const lines = errBuf.split('\n');
        errBuf = lines.pop();           // keep incomplete trailing line for next chunk
        lines.forEach(flushErr);
      });
      proc.on('close', code => {
        if (errBuf) { flushErr(errBuf); errBuf = ''; }   // flush trailing line
        if (ws.readyState === 1)
          ws.send(JSON.stringify({ type: 'chat_done' }));
      });
    } catch {}
  });

  ws.on('close', () => { clients.delete(ws); clientState.delete(ws); });
  ws.on('error', () => { clients.delete(ws); clientState.delete(ws); });
});

function broadcast(data) {
  const msg = JSON.stringify(data);
  for (const ws of clients) {
    if (ws.readyState === 1) {
      const state = clientState.get(ws) || {};
      const wsProject = state.project || PROJECT_NAME;
      const eventProject = data.projectName || PROJECT_NAME;
      if (wsProject === eventProject) ws.send(msg);
    }
  }
}

// ─── TAIL events.jsonl ────────────────────────────────────────────────────────
let lastSize = fs.statSync(EVENTS_FILE).size;

function readNewLines() {
  try {
    const stat = fs.statSync(EVENTS_FILE);
    if (stat.size <= lastSize) return;
    const buf = fs.readFileSync(EVENTS_FILE).slice(lastSize);
    lastSize = stat.size;
    buf.toString('utf8').split('\n').filter(l => l.trim()).forEach(line => {
      try { broadcast(JSON.parse(line)); } catch {}
    });
  } catch {}
}

// fs.watch for instant detection + polling fallback for Windows reliability
try { fs.watch(EVENTS_FILE, () => setTimeout(readNewLines, 30)); } catch {}
setInterval(readNewLines, 400);

// ─── START ────────────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`\n  Claude Dashboard  →  http://localhost:${PORT}\n`);
});
