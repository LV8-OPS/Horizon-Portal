import http from 'http';
import { readFileSync, existsSync, mkdirSync } from 'fs';
import { extname, resolve } from 'path';
import { logger } from './app/logger.js';
import { perf } from './app/perf.js';
import { initMonitoring } from './app/monitoring.js';
import { initErrors } from './app/errors.js';

const env = process.env.NODE_ENV || 'development';
const port = Number(process.env.PORT || 8000);
perf.mark('app_start');
if (!existsSync('logs')) mkdirSync('logs', { recursive: true });
initMonitoring();
initErrors(logger);
const mime = { '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8', '.js':'application/javascript; charset=utf-8', '.ico':'image/x-icon', '.png':'image/png' };
const routes = { '/':'templates/index.html', '/creator':'templates/creator.html', '/download':'templates/download.html', '/account':'templates/account.html', '/workshop':'templates/workshop.html', '/health':null };
const server = http.createServer((req, res) => {
  try {
    if (req.url === '/health') { res.writeHead(200, {'Content-Type':'application/json'}); return res.end(JSON.stringify({status:'ok', env})); }
    const url = new URL(req.url, `http://${req.headers.host}`);
    const path = url.pathname;
    if (path.startsWith('/static/')) {
      const file = resolve(path.slice(1));
      if (!existsSync(file)) { logger.warn('Assets', `Missing asset ${path}`); res.writeHead(404); return res.end('Not found'); }
      const data = readFileSync(file); res.writeHead(200, {'Content-Type': mime[extname(file)] || 'application/octet-stream'}); return res.end(data);
    }
    const file = routes[path] || 'templates/index.html';
    const html = readFileSync(resolve(file), 'utf8');
    res.writeHead(200, {'Content-Type': mime['.html']}); res.end(html);
  } catch (e) {
    logger.error('Server', 'Request failed', e); res.writeHead(500, {'Content-Type':'text/plain'}); res.end('Internal Server Error');
  }
});
server.on('error', e => { logger.error('Server', 'Failed to start', e); process.exit(1); });
server.listen(port, () => { perf.mark('server_ready'); logger.success('Server', `Ready in ${perf.measure('app_start')}ms on http://127.0.0.1:${port}`, { env }); });
