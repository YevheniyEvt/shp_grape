# Frontend

Next.js (App Router, TypeScript), Tailwind CSS, shadcn/ui.

Run commands from the repository root with `just` (`just front`, `just test-front`, `just lint`),
or from this folder with `npm run dev`, `npm run test`, `npm run lint`, `npm run typecheck`.

UI strings use `t()` / `nt()` / `pt()` and are translated in Django's `locale/*/LC_MESSAGES/djangojs.po`
(`just messages` extracts them).
