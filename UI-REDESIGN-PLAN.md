# UI Redesign Plan: Claude Design System Implementation

## Goal
Transform the current dark purple/black theme into the warm cream + coral + dark navy Claude design system as defined in `DESIGN-claude.md`.

## Current State
- Dark purple-black theme (`#0e0c16`) with blue (`#217bfe`) and pink (`#e55571`) accents
- System font stack, no serif typography
- No CSS custom properties or design tokens
- 10 CSS files with hardcoded hex values

## Target State (from DESIGN-claude.md)
- Warm cream canvas (`#faf9f5`) background
- Coral primary accent (`#cc785c`)
- Dark navy product surfaces (`#181715`)
- Slab-serif display headlines (Cormorant Garamond as substitute for Copernicus)
- Humanist sans body (Inter as substitute for StyreneB)
- Editorial spacing rhythm (96px sections)

---

## Implementation Steps

### Step 1: Create CSS Custom Properties (Design Tokens)
**File:** `client/src/index.css`
- Add `:root` block with all color, typography, spacing, and radius tokens from DESIGN-claude.md
- Update `body` to use cream canvas background, ink text color, and Inter font family
- Import Google Fonts: Cormorant Garamond (serif display) + Inter (body sans)

### Step 2: Redesign Root Layout (Header/Nav)
**File:** `client/src/layouts/rootLayout/rootLayout.css`
- Cream canvas background (`var(--color-canvas)`)
- 64px tall header with hairline bottom border
- Logo text in ink color with proper weight
- Clean, editorial nav bar feel

### Step 3: Redesign Homepage (Hero)
**File:** `client/src/routes/homepage/homepage.css`
- Hero section: 6/6 grid layout (text left, illustration right)
- h1 in Cormorant Garamond serif, 64px, weight 400, negative letter-spacing
- Coral CTA button (`var(--color-primary)`) with rounded-md
- Right-side illustration card on cream surface with rounded-xl
- Replace gradient text with solid ink color serif headline
- Dark navy card for the bot illustration area
- Cream-colored floating chat card instead of dark `#2c2937`
- Footer terms in muted text color

### Step 4: Redesign Dashboard Layout (Sidebar + Content)
**Files:** `client/src/layouts/dashboardLayouts/dashboardLayout.css`, `client/src/components/chatList/chatList.css`
- Sidebar: cream canvas background, generous padding
- Sidebar links: ink text, hover state with surface-card background
- Section titles: caption-uppercase typography (12px, 500 weight, 1.5px tracking)
- HR dividers: hairline color
- Content area: cream canvas background (not dark `#12101b`)
- Upgrade card: coral accent or surface-card background

### Step 5: Redesign Dashboard Page (New Chat Form)
**File:** `client/src/routes/dashboardpage/dashboardpage.css`
- Logo/title: Cormorant Garamond serif, ink color (not gradient)
- Option cards: surface-card background, rounded-lg, hairline border, 32px padding
- Input form: surface-card or canvas background, rounded-lg, hairline border
- Send button: coral primary or surface-dark-elevated on dark
- Input text: ink color on cream

### Step 6: Redesign Chat Page
**File:** `client/src/routes/chatpage/chatpage.css`
- Chat messages area: cream canvas background
- User messages: surface-card background, ink text, rounded-lg
- AI messages: transparent/cream background, ink text
- Message spacing: generous (20px gap)
- Code blocks: dark navy surface with monospace font

### Step 7: Redesign Chat Input (NewPrompt)
**File:** `client/src/components/newPrompt/newPrompt.css`
- Input bar: surface-card or canvas background with hairline border
- Rounded-lg shape
- Input text: ink color
- Send button: coral primary circle or surface-dark-elevated
- Upload button: same styling as send button

### Step 8: Update Sign-In/Sign-Up Pages
**Files:** `client/src/routes/signInPage/signInPage.css`, `client/src/routes/signUpPage/signUpPage.css`
- Cream canvas background
- Centered card layout on surface-card background

---

## Color Mapping (Old → New)

| Element | Old Value | New Token | New Value |
|---|---|---|---|
| Body background | `#0e0c16` | `--color-canvas` | `#faf9f5` |
| Body text | `white` | `--color-ink` | `#141413` |
| Primary accent | `#217bfe` | `--color-primary` | `#cc785c` |
| Secondary accent | `#e55571` | `--color-primary-active` | `#a9583e` |
| Card/input bg | `#2c2937` | `--color-surface-card` | `#efe9de` |
| Button bg | `#605e68` | `--color-surface-dark-elevated` | `#252320` |
| Dashboard content bg | `#12101b` | `--color-canvas` | `#faf9f5` |
| Hero image container | `#140e2d` | `--color-surface-dark` | `#181715` |
| Border | `#555` | `--color-hairline` | `#e6dfd8` |
| Muted text | `#888` | `--color-muted` | `#6c6a64` |
| Input text | `#ececec` | `--color-ink` | `#141413` |
| HR divider | `#ddd` (0.1) | `--color-hairline` | `#e6dfd8` |

## Typography Mapping

| Use | Old | New Font | New Weight | New Size |
|---|---|---|---|---|
| Display h1 | system-ui, 128px, gradient | Cormorant Garamond | 400 | 64px |
| Display h2 | system-ui | Cormorant Garamond | 400 | 48px |
| Body text | system-ui | Inter | 400 | 16px |
| Labels/nav | system-ui | Inter | 500 | 14px |
| Captions | system-ui | Inter | 500 | 13px |
| Code | system-ui | JetBrains Mono | 400 | 14px |

## Files to Modify (in order)

1. `client/src/index.css` — Add CSS variables, Google Fonts import, update body styles
2. `client/src/layouts/rootLayout/rootLayout.css` — Header/nav redesign
3. `client/src/routes/homepage/homepage.css` — Hero section redesign
4. `client/src/layouts/dashboardLayouts/dashboardLayout.css` — Dashboard layout
5. `client/src/components/chatList/chatList.css` — Sidebar redesign
6. `client/src/routes/dashboardpage/dashboardpage.css` — Dashboard page
7. `client/src/routes/chatpage/chatpage.css` — Chat page
8. `client/src/components/newPrompt/newPrompt.css` — Chat input
9. `client/src/routes/signInPage/signInPage.css` — Sign-in page
10. `client/src/routes/signUpPage/signUpPage.css` — Sign-up page

## No JSX Changes Required
The component JSX files do not need structural changes — the redesign is purely CSS-based. All class names remain the same; only the visual styling changes via CSS custom properties and updated rules.
