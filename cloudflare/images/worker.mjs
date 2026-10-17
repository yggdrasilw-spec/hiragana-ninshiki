// Public, read-only delivery. Source sheets and review evidence have no public route.
export default {
  async fetch(request, env) {
    const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Expose-Headers': 'ETag, X-Content-SHA256', 'X-Content-Type-Options': 'nosniff' };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: { ...cors, 'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS' } });
    if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', { status: 405, headers: { ...cors, Allow: 'GET, HEAD, OPTIONS' } });
    let key;
    try { key = decodeURIComponent(new URL(request.url).pathname).slice(1); } catch { return new Response('Bad path', { status: 400, headers: cors }); }
    if (!(key === 'shiritori_title.png' || /^assets\/shiritori\/[a-zA-Z0-9_-]+\.(png|jpe?g|webp|svg|gif|avif)$/i.test(key))) return new Response('Not found', { status: 404, headers: cors });
    try {
      const etag = request.headers.get('If-None-Match');
      const metadata = (etag || request.method === 'HEAD') ? await env.ASSETS.head(key) : null;
      if (metadata && etag && (etag === '*' || etag.split(',').some(value => value.trim().replace(/^W\//, '') === metadata.httpEtag))) {
        return new Response(null, { status: 304, headers: { ...cors, ETag: metadata.httpEtag, 'Cache-Control': 'public, max-age=300, must-revalidate' } });
      }
      const object = request.method === 'HEAD' ? metadata : await env.ASSETS.get(key);
      if (!object) return new Response('Not found', { status: 404, headers: cors });
      const headers = new Headers(cors);
      object.writeHttpMetadata(headers);
      headers.set('ETag', object.httpEtag);
      headers.set('Cache-Control', 'public, max-age=300, must-revalidate');
      headers.set('X-Content-SHA256', object.customMetadata?.sha256 || '');
      headers.set('Content-Length', String(object.size));
      return new Response(request.method === 'HEAD' ? null : object.body, { headers });
    } catch (error) {
      console.error(JSON.stringify({ event: 'image_read_failed', key, message: String(error) }));
      return new Response('Image temporarily unavailable', { status: 503, headers: cors });
    }
  }
};
