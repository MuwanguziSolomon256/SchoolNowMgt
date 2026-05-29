---
name: Ethos Glass
colors:
  surface: '#f8f9fc'
  surface-dim: '#d9dadd'
  surface-bright: '#f8f9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3f6'
  surface-container: '#edeef1'
  surface-container-high: '#e7e8eb'
  surface-container-highest: '#e1e2e5'
  on-surface: '#191c1e'
  on-surface-variant: '#46464f'
  inverse-surface: '#2e3133'
  inverse-on-surface: '#f0f1f4'
  outline: '#777680'
  outline-variant: '#c7c5d0'
  surface-tint: '#565a8b'
  primary: '#080b3a'
  on-primary: '#ffffff'
  primary-container: '#1e224f'
  on-primary-container: '#868abd'
  inverse-primary: '#bfc2fa'
  secondary: '#7c5800'
  on-secondary: '#ffffff'
  secondary-container: '#feb700'
  on-secondary-container: '#6b4b00'
  tertiary: '#2b0400'
  on-tertiary: '#ffffff'
  tertiary-container: '#500d00'
  on-tertiary-container: '#e96442'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e0e0ff'
  primary-fixed-dim: '#bfc2fa'
  on-primary-fixed: '#121643'
  on-primary-fixed-variant: '#3f4371'
  secondary-fixed: '#ffdea8'
  secondary-fixed-dim: '#ffba20'
  on-secondary-fixed: '#271900'
  on-secondary-fixed-variant: '#5e4200'
  tertiary-fixed: '#ffdbd2'
  tertiary-fixed-dim: '#ffb4a2'
  on-tertiary-fixed: '#3c0800'
  on-tertiary-fixed-variant: '#881f01'
  background: '#f8f9fc'
  on-background: '#191c1e'
  surface-variant: '#e1e2e5'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 20px
  gutter: 16px
  card-gap: 12px
  section-margin: 32px
---

## Brand & Style

The design system is a premium, high-fidelity framework tailored for educational administration and student engagement. It balances the warmth of African-inspired heritage with the cold precision of modern financial technology. The brand personality is **authoritative, illuminating, and visionary**, aiming to evoke a sense of organized calm and technological advancement.

The visual direction follows a **Glassmorphic** movement. It utilizes multi-layered translucency, vibrant background blurs, and high-contrast typography to create a sense of depth and hierarchy. The aesthetic is defined by its "weightless" feel, where information floats on light-refracting surfaces, grounded by a palette of deep earth tones.

## Colors

The palette is a sophisticated blend of **Deep Indigo** (Primary), providing a stable and professional foundation, and **Sun-Gold** (Secondary), representing excellence and enlightenment. **Terracotta** (Tertiary) is used sparingly as an accent for urgent data points or creative actions.

### Surface Strategy
- **Base Background:** A very soft, cool neutral (#F8F9FC) that allows glass layers to pop.
- **Glass Surfaces:** High-transparency white with a 20px - 40px background blur.
- **Gradients:** Use subtle linear gradients from Indigo to a slightly lighter Navy for primary actions. Accent gradients should use a "Sunset" mix of Gold and Terracotta for data visualizations.

## Typography

This design system utilizes **Hanken Grotesk** for headings to provide a sharp, contemporary, and slightly technical edge. **Inter** is utilized for all functional text, ensuring maximum legibility across dense data sets.

- **Contrast:** Headings should always use the Primary Indigo color to maintain a strong hierarchy.
- **Utility:** Use `label-md` in All Caps for section headers within cards or overlines for small metadata.
- **Optical Sizing:** On mobile, reduce display sizes by roughly 15% to ensure content fits within the narrower viewport without excessive wrapping.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** model optimized for mobile-first consumption. 

- **Grid:** A 4-column grid for mobile, expanding to 12 columns for tablet/desktop views.
- **Safe Zones:** Maintain a 20px horizontal margin on mobile to prevent content from touching the screen edges.
- **Rhythm:** Use an 8px base unit. All padding and margins should be multiples of 8 (e.g., 16, 24, 32).
- **Reflow:** Cards should stack vertically on mobile. On larger viewports, use a masonry or dashboard-style grid where key metrics span multiple columns.

## Elevation & Depth

Hierarchy is established through **Backdrop Blurs** and **Ambient Shadows** rather than solid fills.

- **Level 1 (Base):** Subtle, low-opacity cards with a 1px white border (inner stroke) to simulate glass edges.
- **Level 2 (Floating):** Used for active states or modals. Increase the shadow spread (Blur: 30px, Y: 10px) and decrease the opacity of the glass surface.
- **Depth Tints:** Shadows are not pure black; they use a very desaturated version of the Primary Indigo (`rgba(30, 34, 79, 0.08)`) to maintain a clean, integrated appearance.
- **Interactive Layers:** When an element is pressed, it should "sink" by reducing its shadow and increasing the opacity of the background blur.

## Shapes

The design system uses a **Rounded** shape language to feel approachable and modern. 

- **Standard Elements:** Buttons and input fields use a `0.5rem` (8px) radius.
- **Large Containers:** Content cards and modals use `1.5rem` (24px) for a soft, premium "tablet" feel.
- **Icon Enclosures:** Small circular badges or status chips should remain pill-shaped to contrast against the more structured rectangular cards.

## Components

### Buttons
- **Primary:** Deep Indigo background, white text, subtle Sun-Gold bottom glow on hover.
- **Secondary:** Glassmorphic fill (30% white), Primary Indigo text, 1px white border.

### Refined Cards
- Use `rgba(255, 255, 255, 0.7)` with a `backdrop-filter: blur(20px)`.
- Include a 1px top-left highlight border to simulate light hitting the edge of glass.

### Data Visualization
- Line charts should use a Primary Indigo stroke with a soft Sun-Gold gradient fill beneath the line.
- Progress rings use Sun-Gold for the active track and a low-opacity Indigo for the remaining path.

### Modern Navigation
- **Mobile Bottom Bar:** A floating glass island detached from the screen bottom by 12px, with a high blur and 24px corner radius.
- **Active State:** Use a Sun-Gold dot or a subtle Indigo glow behind the icon.

### Input Fields
- Transparent backgrounds with a soft bottom border. 
- On focus, the border transitions to Primary Indigo with a soft outer glow in Sun-Gold.