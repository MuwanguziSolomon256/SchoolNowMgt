/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Surfaces
        surface: "#f8f9fc",
        "surface-dim": "#d9dadd",
        "surface-bright": "#f8f9fc",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f2f3f6",
        "surface-container": "#edeef1",
        "surface-container-high": "#e7e8eb",
        "surface-container-highest": "#e1e2e5",
        "on-surface": "#191c1e",
        "on-surface-variant": "#46464f",
        "inverse-surface": "#2e3133",
        "inverse-on-surface": "#f0f1f4",

        // Outline & Borders
        outline: "#777680",
        "outline-variant": "#c7c5d0",

        // Tint
        "surface-tint": "#565a8b",

        // Primary
        primary: "#080b3a",
        "on-primary": "#ffffff",
        "primary-container": "#1e224f",
        "on-primary-container": "#868abd",
        "inverse-primary": "#bfc2fa",
        "primary-fixed": "#e0e0ff",
        "primary-fixed-dim": "#bfc2fa",
        "on-primary-fixed": "#121643",
        "on-primary-fixed-variant": "#3f4371",

        // Secondary
        secondary: "#7c5800",
        "on-secondary": "#ffffff",
        "secondary-container": "#feb700",
        "on-secondary-container": "#6b4b00",
        "secondary-fixed": "#ffdea8",
        "secondary-fixed-dim": "#ffba20",
        "on-secondary-fixed": "#271900",
        "on-secondary-fixed-variant": "#5e4200",

        // Tertiary
        tertiary: "#2b0400",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#500d00",
        "on-tertiary-container": "#e96442",
        "tertiary-fixed": "#ffdbd2",
        "tertiary-fixed-dim": "#ffb4a2",
        "on-tertiary-fixed": "#3c0800",
        "on-tertiary-fixed-variant": "#881f01",

        // Error
        error: "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",

        // Background
        background: "#f8f9fc",
        "on-background": "#191c1e",
        "surface-variant": "#e1e2e5",
      },

      borderRadius: {
        sm: "0.25rem",
        DEFAULT: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },

      spacing: {
        base: "8px",
        "section-margin": "32px",
        gutter: "16px",
        "container-padding": "20px",
        "card-gap": "12px",
      },

      fontFamily: {
        "headline-lg": ["Hanken Grotesk", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "headline-lg-mobile": ["Hanken Grotesk", "sans-serif"],
        "display-lg": ["Hanken Grotesk", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "label-md": ["Inter", "sans-serif"],
        "headline-md": ["Hanken Grotesk", "sans-serif"],
      },

      fontSize: {
        "headline-lg": [
          "28px",
          {
            lineHeight: "36px",
            fontWeight: "600",
          },
        ],
        "body-lg": [
          "16px",
          {
            lineHeight: "24px",
            fontWeight: "400",
          },
        ],
        "headline-lg-mobile": [
          "24px",
          {
            lineHeight: "32px",
            fontWeight: "600",
          },
        ],
        "display-lg": [
          "36px",
          {
            lineHeight: "44px",
            letterSpacing: "-0.02em",
            fontWeight: "700",
          },
        ],
        "body-md": [
          "14px",
          {
            lineHeight: "20px",
            fontWeight: "400",
          },
        ],
        "label-md": [
          "12px",
          {
            lineHeight: "16px",
            letterSpacing: "0.05em",
            fontWeight: "600",
          },
        ],
        "headline-md": [
          "22px",
          {
            lineHeight: "28px",
            fontWeight: "600",
          },
        ],
      },

      boxShadow: {
        "glass": "0 10px 30px -5px rgba(30, 34, 79, 0.08)",
        "glass-deep": "0 10px 30px -10px rgba(30, 34, 79, 0.08)",
        "btn-primary": "0 8px 24px rgba(8, 11, 58, 0.12)",
        "btn-primary-hover": "0 12px 32px rgba(8, 11, 58, 0.2)",
      },

      backdropBlur: {
        "glass": "20px",
      },

      keyframes: {
        "shimmer": {
          "0%": {
            backgroundPosition: "-1000px 0",
          },
          "100%": {
            backgroundPosition: "1000px 0",
          },
        },
        "fade-in": {
          "0%": {
            opacity: "0",
          },
          "100%": {
            opacity: "1",
          },
        },
        "slide-in": {
          "0%": {
            transform: "translateY(20px)",
            opacity: "0",
          },
          "100%": {
            transform: "translateY(0)",
            opacity: "1",
          },
        },
      },

      animation: {
        "shimmer": "shimmer 2s infinite",
        "fade-in": "fade-in 0.3s ease-in-out",
        "slide-in": "slide-in 0.3s ease-in-out",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
  ],
};
