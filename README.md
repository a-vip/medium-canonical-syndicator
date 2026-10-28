# Medium Canonical Syndicator & SEO Authority Booster

Autonomous content syndicator for **[aviperera.com](https://aviperera.com)** that cross-publishes research dossiers and essays to Medium via the Medium REST API v1.

Every post published through this engine embeds an official **`canonicalUrl` pointing back to the origin publication on `aviperera.com`**. This instructs Google, Bing, and Medium to channel **100% of the SEO domain authority and backlink equity straight to your personal website**, while tapping into Medium’s algorithm and readership.

---

## 🚀 Key Capabilities

1. **Strict Canonical Attribution**:
   - Every syndicated story sets `canonicalUrl: https://aviperera.com/<post-slug>/`.
   - Prevents duplicate content penalties and guarantees search engines credit your domain as the primary source.
2. **Full HTML Formatting**:
   - Ingests full article bodies directly from `https://aviperera.com/feed/` (WAF-immune).
   - Preserves headings, images, blockquotes, and lists.
   - Automatically appends a prominent editorial citation note linking back to the origin dossier.
3. **Smart Tag Extraction**:
   - Maps article categories into clean, compliant Medium tags (max 5 tags per story).
4. **Zero Duplicate Syndication**:
   - Tracks syndicated posts in `state/medium_history.json`.
   - Automatically commits updated state on each run.
5. **Algorithmic Cadence & Dry-Run Preview**:
   - Paces publication to 1 article per scheduled run to ensure maximum reader visibility and avoid platform rate limits.
   - Safely executes in Preview/Dry-Run mode when credentials are not yet configured.

---

## 🛠️ Configuration & Secrets

Add the following repository secrets under:  
**Settings** ➔ **Secrets and variables** ➔ **Actions** ➔ **New repository secret**:

| Secret Name | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `MEDIUM_INTEGRATION_TOKEN` | **Yes** | — | Your personal Medium integration token. |
| `MEDIUM_PUBLISH_STATUS` | *Optional* | `public` | Can be set to `public`, `draft`, or `unlisted`. |

---

## 📌 How to Obtain a Medium Integration Token

1. Log in to your account at [medium.com](https://medium.com).
2. Go to **Settings** ➔ **Security and apps**.
3. Scroll down to **Integration tokens**.
4. Enter a description (e.g. `Avi Canonical Syndicator`) and click **Get token**.
5. Copy the generated token and save it as `MEDIUM_INTEGRATION_TOKEN` in your repository secrets.

---

## 🧪 Local Testing

```bash
python -m unittest discover tests
python medium_engine.py --dry-run
```
