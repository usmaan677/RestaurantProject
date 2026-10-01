# RestaurantManagement

A restaurant management web app. The front end is a React single-page app built with
Vite, styled with Tailwind CSS, and routed with React Router.

## Prerequisites

Install these before you start:

| Tool | Version | Check with | Get it |
| --- | --- | --- | --- |
| Node.js | 22 LTS or newer | `node -v` | [nodejs.org](https://nodejs.org) |
| npm | comes with Node | `npm -v` | — |
| Git | any recent | `git --version` | [git-scm.com](https://git-scm.com) |

Node 22.13+ or 24+ is recommended. Node 20.19+ will run the app, but some dev
tooling (ESLint 10) asks for a newer version and prints `EBADENGINE` warnings.

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/usmaan677/RestaurantManagement.git
cd RestaurantManagement

# 2. Move into the front end
cd frontend

# 3. Install dependencies
npm install

# 4. Start the dev server
npm run dev
```

Then open **http://localhost:5173** in a browser.

The server hot-reloads: save a file and the page updates without a refresh.
Press `Ctrl+C` in the terminal to stop it.

> All npm commands must be run from inside the `frontend/` folder, not the repo
> root. Running `npm install` at the root will fail — there is no `package.json` there.

## Available scripts

Run these from `frontend/`:

| Command | What it does |
| --- | --- |
| `npm run dev` | Start the dev server at http://localhost:5173 with hot reload |
| `npm run build` | Build the production bundle into `frontend/dist/` |
| `npm run preview` | Serve the built `dist/` folder locally to check the production build |
| `npm run lint` | Run ESLint over the source |

## Project structure

```
RestaurantManagement/
├── README.md
└── frontend/
    ├── package.json          # dependencies and scripts
    ├── vite.config.js        # Vite config + Tailwind plugin
    ├── index.html            # single HTML entry point
    └── src/
        ├── main.jsx          # app entry; mounts React and BrowserRouter
        ├── App.jsx           # navbar + route table
        ├── index.css         # Tailwind import
        ├── assets/           # images
        ├── components/
        │   └── Navbar.jsx    # site navigation
        └── pages/
            ├── Home.jsx      # /
            └── LogIn.jsx     # /login
```

## Routes

| Path | Page | Notes |
| --- | --- | --- |
| `/` | `pages/Home.jsx` | Landing page |
| `/login` | `pages/LogIn.jsx` | Login form (front end only; no backend yet) |
| anything else | inline in `App.jsx` | "Page not found" fallback |

The login form currently logs its values to the browser console. It does not
authenticate against a server.

### Adding a page

Three edits:

1. Create `src/pages/YourPage.jsx` exporting a component as its default export.
2. Add a `<Route path="/your-path" element={<YourPage />} />` line in `src/App.jsx`.
3. Add `{ to: '/your-path', label: 'Your Page' }` to the `links` array in
   `src/components/Navbar.jsx` so it appears in the navbar.

## Tech stack

- **React 19** — UI library
- **Vite 8** — dev server and build tool
- **Tailwind CSS 4** — utility-first styling, via the `@tailwindcss/vite` plugin
- **React Router 7** — client-side routing

Tailwind 4 needs no `tailwind.config.js` and no `postcss.config.js`. It is wired
up in two places only: the `tailwindcss()` plugin in `vite.config.js`, and the
`@import "tailwindcss";` line in `src/index.css`. Older guides that tell you to
run `npx tailwindcss init -p` are for Tailwind 3 and do not apply here.

## Troubleshooting

**Blank page, console says "useRoutes() may be used only in the context of a Router"**
`src/main.jsx` is missing the `<BrowserRouter>` wrapper around `<App />`.

**Tailwind classes do nothing / text renders unstyled**
Check that `vite.config.js` includes `tailwindcss()` in its `plugins` array, and
that `src/index.css` contains `@import "tailwindcss";`. Restart the dev server
after editing `vite.config.js` — Vite does not hot-reload its own config.

**`Port 5173 is in use`**
Another dev server is already running. Stop it, or let Vite pick the next free
port when it offers.

**`npm error enoent Could not read package.json`**
You are in the repo root. Run `cd frontend` first.

**`EBADENGINE` warnings during `npm install`**
Your Node version is older than ESLint 10 wants. The app still builds and runs;
upgrade to Node 24+ to silence them.

**The login form autofills an email and password**
That is the browser's password manager recognising a login form, not app code.
Clear saved entries for `localhost` in your browser's password settings, or
ignore it.
