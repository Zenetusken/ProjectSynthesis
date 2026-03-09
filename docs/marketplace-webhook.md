# GitHub Marketplace Webhook — Cloudflare Worker

## Setup Steps

1. Click **Start with Hello World!** in the Cloudflare Workers dashboard
2. Name the worker `project-synthesis-webhook`
3. Replace the default code with the worker code below
4. Click **Deploy**
5. Go to **Settings → Variables → Add variable**: `WEBHOOK_SECRET` = your secret (see below)
6. Set the route to `zenresources.net/marketplace/webhook` under **Settings → Triggers**

---

## Webhook Secret

```
b24e84b79ecd07a95e570c879ef459fd6cbaee797ff1ea25b81f0be6f66b494f
```

Store this in:
- Cloudflare Worker environment variable: `WEBHOOK_SECRET`
- GitHub Marketplace webhook settings: **Secret** field

---

## Worker Code

```js
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const signature = request.headers.get("X-Hub-Signature-256") ?? "";
    const body = await request.text();

    // Verify HMAC-SHA256 signature
    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(env.WEBHOOK_SECRET),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
    const expected = "sha256=" + Array.from(new Uint8Array(mac))
      .map(b => b.toString(16).padStart(2, "0")).join("");

    if (signature !== expected) {
      return new Response("Unauthorized", { status: 401 });
    }

    const event = JSON.parse(body);
    const action = event?.action;
    const account = event?.marketplace_purchase?.account?.login ?? "unknown";

    // Log installs/uninstalls — extend here for analytics
    console.log(`Marketplace event: ${action} — ${account}`);

    return new Response("OK", { status: 200 });
  }
};
```

---

## GitHub Marketplace Settings

| Field | Value |
|---|---|
| Payload URL | `https://zenresources.net/marketplace/webhook` |
| Content type | `application/json` |
| Secret | the secret above |

---

## Events Received

Since the plan is free with no paid tier, the only events this webhook will receive are:

| Action | Meaning |
|---|---|
| `purchased` | Someone installed the app |
| `cancelled` | Someone uninstalled the app |
| `pending_change` | Not applicable (single free plan) |
| `changed` | Not applicable (single free plan) |
