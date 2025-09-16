# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

## Theme handling

Wrap the application in `ThemeProvider` (see `src/App.tsx`) to sync the selected appearance with `localStorage` and the document root classes. The `ThemeToggle` component now relies on the provider's `useTheme()` hook to flip between the light and dark themes, respecting the system preference when configured.

## Chat layout

The chat sidebar previously lived inside `src/pages/Chat.tsx`; it now resides in `src/components/ChatSidebar.tsx`. `Chat.tsx` passes connection and conversation handlers into that component so you can iterate on the sidebar UI in isolation.

`AppLayout` also accepts an optional `sidebarTitle` prop that renders inside a `SidebarHeader`, keeping page titles consistent across layouts.

The sidebar now exposes a settings dialog (`src/components/ChatSettingsDialog.tsx`) via a bottom-aligned button. Connections are managed from within that dialog, alongside a logout action that wires through `Chat.tsx` to call the API and reset the current user. A top-level "New chat" button clears the current conversation selection and resets the chosen connection so users can start fresh. The composer/input bar lives in `src/components/ChatInputBar.tsx`, keeping the page focused on data flow rather than UI wiring—its send button stays disabled until a database connection is chosen, the picker highlights when selection is missing, the picker itself locks while viewing an existing conversation so the session stays tied to the recorded connection, and when no conversation is active the composer sits centered with a short call-to-action to guide the user. Both the composer and message list respect the shared `--layout-max-width` variable (see `src/index.css`) so the content column never exceeds 1280px.
