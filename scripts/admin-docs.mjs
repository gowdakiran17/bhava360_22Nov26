import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
const require = createRequire(import.meta.url);
const assets = dirname(require.resolve('swagger-ui-dist/package.json'));
const files = {
  '/admin.json': [
    'application/json',
    new URL('../openapi/admin.json', import.meta.url),
  ],
  '/swagger-ui.css': ['text/css', join(assets, 'swagger-ui.css')],
  '/swagger-ui-bundle.js': [
    'text/javascript',
    join(assets, 'swagger-ui-bundle.js'),
  ],
};
createServer((req, res) => {
  if (req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(
      '<!doctype html><html lang="en"><title>Bhava360 staff API</title><link rel="stylesheet" href="/swagger-ui.css"><main id="docs"></main><script src="/swagger-ui-bundle.js"></script><script>SwaggerUIBundle({url:"/admin.json",dom_id:"#docs",validatorUrl:null,supportedSubmitMethods:[]})</script></html>',
    );
  } else if (Object.hasOwn(files, req.url)) {
    const [type, file] = files[req.url];
    res.writeHead(200, { 'Content-Type': type });
    res.end(readFileSync(file));
  } else {
    res.writeHead(404);
    res.end();
  }
}).listen(4080, '127.0.0.1', () =>
  console.log('Staff API documentation at http://127.0.0.1:4080/'),
);
