import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "./hermes-edge.mjs";

test("rejects an unknown host and a request without a bearer", async (t) => {
  const upstream = t.mock.method(globalThis, "fetch");
  const unknown = await worker.fetch(new Request("https://unknown.invalid/mcp"));
  const anonymous = await worker.fetch(new Request("https://mcp.hermes.bchbenjamin.in/mcp"));
  assert.equal(unknown.status, 404);
  assert.equal(anonymous.status, 401);
  assert.equal(upstream.mock.callCount(), 0);
});

test("fixes the HTTPS origin and preserves MCP and streaming headers", async (t) => {
  const upstream = t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url.href, "https://hermes-mcp-origin.bchbenjamin.in/mcp?q=1");
    assert.equal(options.method, "POST");
    assert.equal(options.redirect, "manual");
    assert.equal(options.cache, "no-store");
    assert.equal(options.headers.get("authorization"), "Bearer test-token");
    assert.equal(options.headers.get("mcp-protocol-version"), "2025-11-25");
    assert.equal(options.headers.get("cookie"), null);
    assert.equal(await new Response(options.body).text(), "{}");

    let controller;
    const body = new ReadableStream({ start(stream) { controller = stream; } });
    t.after(() => controller.close());
    controller.enqueue(new TextEncoder().encode("data: test\n\n"));
    return new Response(body, {
      headers: { "Content-Type": "text/event-stream", "Mcp-Session-Id": "test-session" },
    });
  });

  const resp = await worker.fetch(new Request("http://mcp.hermes.bchbenjamin.in:8080/mcp?q=1", {
    method: "POST",
    body: "{}",
    headers: {
      Authorization: "Bearer test-token",
      "Mcp-Protocol-Version": "2025-11-25",
      Cookie: "browser-session=test",
    },
  }));
  assert.equal(upstream.mock.callCount(), 1);
  assert.equal(resp.headers.get("mcp-session-id"), "test-session");
  assert.equal(resp.headers.get("content-type"), "text/event-stream");
  assert.equal(resp.headers.get("cache-control"), "no-store");
  const result = await resp.body.getReader().read();
  assert.equal(new TextDecoder().decode(result.value), "data: test\n\n");
});

test("routes the API hostname to its own origin", async (t) => {
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url.href, "https://hermes-api-origin.bchbenjamin.in/v1/capabilities");
    assert.equal(options.method, "GET");
    return Response.json({ object: "hermes.capabilities" });
  });
  const req = new Request("https://api.hermes.bchbenjamin.in/v1/capabilities", {
    headers: { Authorization: "Bearer test-token" },
  });
  assert.equal((await worker.fetch(req)).status, 200);
});
