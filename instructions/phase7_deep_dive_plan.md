# **SocioGraph Rebuild — Phase 7 Deep‑Dive Plan**

> **Objective:** Deliver a fast, offline‑capable **Preact + Tailwind** front‑end that consumes the Phase 6 API, streams answers in real‑time, and lets users manage history, saved PDFs, settings, and file uploads.

---

## 🎯 Outcomes

| ID    | Outcome                                                                                                              | Acceptance Criteria                      |
| ----- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| O‑7.1 | **Four pages** (Home, History, Saved, Settings) reachable via client‑side router.                                    | URL changes without full reload.         |
| O‑7.2 | **Home/Search** page streams answer tokens with live typing effect for both English & Arabic, preserving RTL layout. | Visual demo passes QA.                   |
| O‑7.3 | **Upload** button sends PDF via `/upload`; toast shown via Sonner.                                                   | File appears in server `input/`.         |
| O‑7.4 | **Processing** status bar subscribes to SSE progress and animates.                                                   | Bar fills 0 → 100 %.                     |
| O‑7.5 | **History** page lists latest 15 queries fetched from `/history`; entries re‑query on click.                         | Rerun button returns fresh answer.       |
| O‑7.6 | **Saved** page lists PDFs from `/saved/`; clicking downloads file.                                                   | HTTP 200 + `Content-Disposition` header. |
| O‑7.7 | Full dark/light mode support & RTL for Arabic, using **Tailwind** theme tokens consistent with `pdf_theme.css`.      | Manual QA on phone + desktop.            |
| O‑7.8 | `pnpm build` outputs a static bundle in `ui/dist/` ≤ 200 kB gzipped.                                                 | Bundle size script passes.               |

---

## 🗂️ Front‑End Architecture  fileciteinstructions\ui_overview.md

```
ui/
  src/
    components/
      SearchBar.tsx
      StreamAnswer.tsx
      FileUploader.tsx
      ProgressBar.tsx
      HistoryList.tsx
      SavedGrid.tsx
      SettingsForm.tsx
    hooks/
      useSSE.ts
      useLocalState.ts
    pages/
      Home.tsx
      History.tsx
      Saved.tsx
      Settings.tsx
    lib/
      api.ts          # wraps fetch/EventSource
      i18n.ts         # RTL helpers, font switch
    App.tsx
    main.tsx
  index.html
  tailwind.config.ts
  vite.config.ts
```

*State is kept in a lightweight **Zustand** store (`useLocalState`) with persistence to `localStorage` for theme and slider defaults.*

---

## ⚙️ Prerequisites

```bash
# Node & pnpm
corepack enable
pnpm dlx create-vite@latest ui --template preact-ts
cd ui
pnpm install
pnpm add -D tailwindcss postcss autoprefixer @types/lucide-react            @tailwindcss/typography @tailwindcss/forms
pnpm add zustand sonner clsx axios
```

Initialise Tailwind:

```bash
pnpx tailwindcss init -p
```

Update `tailwind.config.ts` to include `src/**/*.{tsx,ts}` and extend theme with colours from CSS variables in `pdf_theme.css` for brand consistency fileciteinstructions\ui_overview.md.

---

## 🛠️ Step‑by‑Step Implementation

### 1  Global Styles

*Import Inter + Noto Sans Arabic fonts and colour CSS variables from `styles.css` into `src/index.css.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --primary: #1F4B88;
    --secondary: #2C3E50;
    /* …other vars */
  }
  [dir="rtl"] {
    font-family: var(--font-arabic);
  }
}
```

### 2  API Wrapper (`lib/api.ts`)

```ts
const BASE = import.meta.env.VITE_API ?? "http://127.0.0.1:8000";

export async function uploadPDF(file: File) {
  const data = new FormData();
  data.append("file", file);
  return fetch(`${BASE}/upload`, { method: "POST", body: data }).then(r => r.json());
}

export function ask(query: string, opts = {}) {
  const es = new EventSource(`${BASE}/search`, { withCredentials: false });
  es.onerror = console.error;
  return es;          // caller handles 'message' events containing tokens
}

export function getHistory() {
  return fetch(`${BASE}/history`).then(r => r.json());
}

export function resetCorpus() {
  return fetch(`${BASE}/reset`, { method: "POST" }).then(r => r.json());
}
```

### 3  Streaming Hook (`hooks/useSSE.ts`)

```ts
import { useEffect, useState } from "preact/hooks";

export function useSSE(source: EventSource | null) {
  const [text, setText] = useState("");
  useEffect(() => {
    if (!source) return;
    const listener = (e: MessageEvent) => setText(t => t + e.data);
    source.addEventListener("token", listener);
    return () => source.close();
  }, [source]);
  return text;
}
```

### 4  Home/Search Page

```tsx
export default function Home() {
  const [query, setQuery] = useState("");
  const [answerSrc, setAnswerSrc] = useState<EventSource | null>(null);
  const answer = useSSE(answerSrc);

  const onAsk = () => setAnswerSrc(ask(query));

  return (
    <div class="space-y-6">
      <SearchBar value={query} onChange={setQuery} onSubmit={onAsk} />
      <StreamAnswer markdown={answer} />
    </div>
  );
}
```

`StreamAnswer` uses **markdown‑it** and scrolls to bottom on new tokens, ensuring RTL dir when `lang="ar"`.

### 5  File Uploader & Progress

`FileUploader` wraps `<input type="file">` and calls `uploadPDF()`, showing Sonner toast `"Uploaded — processing in background"`.

`ProgressBar` subscribes to `/process` SSE (Phase 3) to animate fill width.

### 6  History & Saved Pages

*History* fetches `/history` on mount; each item has **Rerun** button.

*Saved* fetches directory listing by calling `/saved/index.json` (served by simple FastAPI static file index).

### 7  Settings Page

Allows:

* Change `top_k`, `top_k_r`, `temperature`.
* Toggle dark mode.
* **Reset Corpus** button (calls `/reset`).

Values are stored in Zustand store and sent as JSON body with queries.

### 8  Routing & Theming

Use **`preact-router`** for navigation; top‑level `App.tsx` holds `<ThemeProvider>` controlling `class="dark"`.

RTL support: when answer `lang === "ar"`, set `dir="rtl"` in `StreamAnswer` container.

### 9  CI & Build

Add npm scripts:

```json
"dev": "vite",
"build": "vite build",
"preview": "vite preview"
```

CI job (optional Phase 8) runs `pnpm build && du -sh dist/`.

---

## 📝 Unit & E2E Tests

* **Vitest + @testing-library/preact** for component tests.
* **Cypress** (optional) for streaming answer & upload flows.

Add a test that renders `StreamAnswer` and feeds 100 tokens under 500 ms to assert smooth typing.

---

## 🕑 Estimated Effort

| Task                                     | Time (hrs) |
| ---------------------------------------- | ---------- |
| Vite scaffold & Tailwind config          | 0.5        |
| Core components (Search, Stream, Upload) | 1.5        |
| Pages & routing                          | 0.5        |
| API integration & hooks                  | 1          |
| Theming, RTL, dark mode                  | 0.5        |
| History & Saved views                    | 0.5        |
| Settings & local store                   | 0.5        |
| Testing & polish                         | 1          |
| **Total**                                | **~6 hrs** |

---

## 🚑 Troubleshooting & Tips

| Symptom                 | Likely Cause                              | Fix                                                                     |
| ----------------------- | ----------------------------------------- | ----------------------------------------------------------------------- |
| SSE blocked by CORS     | API missing `Access-Control-Allow-Origin` | Ensure front‑end URL added in FastAPI CORS origins list (Phase 6).      |
| Arabic text overlaps UI | Missing font & RTL                        | Import Noto Sans Arabic and set `dir="rtl"`.                            |
| Tailwind purges styles  | Content paths wrong                       | Check `tailwind.config.ts` `content` glob includes `src/**/*.{tsx,ts}`. |
| Bundle too large        | lucide build‑time icons                   | Use tree‑shaken `lucide-preact` imports.                                |

---

## 📝 Deliverables

1. **`ui/`** folder with Preact/Tailwind project.  
2. Four routed pages with full functionality.  
3. Real‑time streaming answer display in Home page.  
4. Dark/light & RTL theme switching.  
5. Build script outputs `dist/` and serves via FastAPI `StaticFiles`.  
6. Git tag **`phase‑7`**.

---

_When `pnpm dev` shows the UI, answers stream, uploads process, and history/saved/settings all work, **Phase 7 is complete**. Next: Phase 8 — Testing & Utilities._
