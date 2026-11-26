// Cloudflare Worker for the two nested public hostnames. Caddy enforces the
// route allowlist, and each application validates its own bearer credential.
const origins = new Map([
  ["api.hermes.bchbenjamin.in", "hermes-api-origin.bchbenjamin.in"],
  ["mcp.hermes.bchbenjamin.in", "hermes-mcp-origin.bchbenjamin.in"],
]);

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = origins.get(url.hostname);
    if (!origin) return new Response(null, { status: 404 });
    const headers = new Headers(request.headers);
    if (!/^Bearer\s+\S+$/.test(headers.get("Authorization") ?? "")) {
      return new Response(null, {
        status: 401,
        headers: { "Cache-Control": "no-store" },
      });
    }

    url.protocol = "https:";
    url.hostname = origin;
    url.port = "";
    headers.delete("Host");
    headers.delete("Cookie");
    const upstream = await fetch(url, {
      method: request.method,
      headers,
      body: request.body,
      redirect: "manual",
      cache: "no-store",
    });
    const resultHeaders = new Headers(upstream.headers);
    resultHeaders.set("Cache-Control", "no-store");
    return new Response(upstream.body, {
      status: upstream.status,
      headers: resultHeaders,
    });
  },
};
