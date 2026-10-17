<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
  <img alt="Pulkit Chauhan: final-year CS student who builds fast, tested systems in C++, Go, Python and TypeScript. Diagram of five systems and a title block of credentials." src="./assets/hero-light.svg" width="100%">
</picture>

I'm Pulkit, a final-year CS student at UPES Dehradun. I like building the layer between raw data and the people who use it, and I try to put a measurement next to every claim. I'm looking for software engineering roles starting January 2027.

## Things I've built

<a href="https://github.com/pulk17/NASDAQ-ITCH-OrderBook">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/detail-a-dark.svg">
  <img alt="A. PitchFork: Nobody sends you the market. You rebuild it. Replays a full NASDAQ trading day from the raw exchange feed and rebuilds every stock&#x27;s order book: 459.8M messages in 51.6 s on a laptop. Tests an order-flow signal across 6,307 symbols. It calls the next move right 55.28% of the time, yet only 13 symbols stay profitable after paying the spread. The same C++ core compiles to a 46 KB WebAssembly module, so a real trading day replays live in your browser. Built with C++17, WebAssembly, Linux, JavaScript." src="./assets/detail-a-light.svg" width="100%">
</picture>
</a>

[Code](https://github.com/pulk17/NASDAQ-ITCH-OrderBook)&nbsp;&nbsp;|&nbsp;&nbsp;[Live backtest report](https://pitchfork.pages.dev/)

<a href="https://github.com/CCExtractor/sample-platform">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/detail-b-dark.svg">
  <img alt="B. sample-platform: Google Summer of Code 2026 with CCExtractor Built the REST API and web console for the platform that regression-tests CCExtractor, an open-source subtitle extractor, against real video samples. 34 of my commits are in upstream master: an OpenAPI 3 contract with 79 operations, scoped-token auth, multi-GB uploads and a React 19 console. 330+ API tests aimed at the edges, like revoked tokens, two uploads with the same name, and the 4xx path of every route. Built with Python, Flask, MySQL, React, TypeScript." src="./assets/detail-b-light.svg" width="100%">
</picture>
</a>

[Code](https://github.com/CCExtractor/sample-platform)&nbsp;&nbsp;|&nbsp;&nbsp;[My merged commits](https://github.com/CCExtractor/sample-platform/commits/master?author=pulk17)

<a href="https://github.com/pulk17/k8n">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/detail-c-dark.svg">
  <img alt="C. k8n: A visual IDE for Kubernetes Draw your app as a graph of Kubernetes resources, review the YAML it compiles to, then deploy. Imported resources are patched, never overwritten. An MCP server gives Claude Code and other agents 9 cluster tools. Writes are dry-run by default, and a read-only mode drops them entirely. A supervisor agent hands work to inspector and architect agents, which diagnose crash loops and OOM kills and propose fixes you approve. Built with Go, Gin, Next.js, React Flow, PostgreSQL, Helm." src="./assets/detail-c-light.svg" width="100%">
</picture>
</a>

[Code](https://github.com/pulk17/k8n)&nbsp;&nbsp;|&nbsp;&nbsp;[Live site](https://k8n.pages.dev/)

<a href="https://github.com/pulk17/undercover-game">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/detail-d-dark.svg">
  <img alt="D. Undercover: A real-time multiplayer party game Everyone plays from their own phone. The server owns the game state and checks every move, so nobody can cheat by editing their client. Game phases run over Socket.IO and sessions live in Redis, so the state never depends on a single server process. Installable as a PWA, with request validation, rate limiting and error monitoring built in. Built with TypeScript, React, Socket.IO, Redis, Supabase." src="./assets/detail-d-light.svg" width="100%">
</picture>
</a>

[Code](https://github.com/pulk17/undercover-game)&nbsp;&nbsp;|&nbsp;&nbsp;[Play it](https://undercover-game-client.vercel.app/)

<a href="https://github.com/pulk17/Band-Former">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/detail-e-dark.svg">
  <img alt="E. Band-Former: Song in, playable guitar tab out Python ML stages isolate the guitar with HTDemucs, track the beat and transcribe the notes. A C++ engine maps notes to frets, classifies chords from chroma features and picks a consistent fingering with a minimax-Viterbi search. Paste a YouTube link or upload a file in the web app. Runs on Linux, Windows and macOS. Built with Python, PyTorch, C++17, FastAPI." src="./assets/detail-e-light.svg" width="100%">
</picture>
</a>

[Code](https://github.com/pulk17/Band-Former)

## Skills

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/skills-dark.svg">
  <img alt="Skills table: each skill lists the projects above that use it." src="./assets/skills-light.svg" width="100%">
</picture>

## How I work

- **I measure before I optimise.** PitchFork's README lists every optimisation with its measured speed-up, plus the ones that didn't help, like io_uring and profile-guided optimisation.
- **I report results I don't like.** My order-flow signal is right 55% of the time and still loses money after costs. The write-up says so up front.
- **I test the edges.** sample-platform's API ships with 330+ tests for things like revoked tokens and two uploads with the same name.
- **I keep a human in the loop for AI.** k8n's agents can only propose changes, and every write is a dry run unless you say otherwise.

## Get in touch

[Email](mailto:chauhanpulkit1708@gmail.com)&nbsp;&nbsp;|&nbsp;&nbsp;[LinkedIn](https://www.linkedin.com/in/pulk1t/)&nbsp;&nbsp;|&nbsp;&nbsp;[Codeforces](https://codeforces.com/profile/pulk1t)&nbsp;&nbsp;|&nbsp;&nbsp;[LeetCode](https://leetcode.com/u/pulk1tt/)&nbsp;&nbsp;|&nbsp;&nbsp;[Website](https://pulk1t.vercel.app/)
