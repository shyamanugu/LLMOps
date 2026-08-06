/**
 * Design tokens for the LLMOps Console.
 *
 * A restrained, accessible light theme built around navy + teal with a neutral
 * gray scale. These values are the single source of truth for TypeScript-side
 * styling; the same palette is mirrored as CSS custom properties in `global.css`.
 */

export const palette = {
  navy: '#1F3A5F',
  navyDark: '#162A45',
  navyLight: '#2C5080',
  teal: '#2A9D8F',
  tealDark: '#218075',
  tealSoft: '#E6F4F1',
  // Neutral gray scale (50 -> 900).
  gray50: '#F7F9FB',
  gray100: '#EEF1F5',
  gray200: '#E1E6EC',
  gray300: '#CBD3DC',
  gray400: '#9AA6B2',
  gray500: '#6B7785',
  gray600: '#4E5964',
  gray700: '#374049',
  gray800: '#232A31',
  gray900: '#141a1f',
  white: '#FFFFFF',
  // Semantic status colors (accessible against white).
  success: '#2A9D8F',
  warning: '#B8860B',
  danger: '#B4442E',
  info: '#1F3A5F',
} as const;

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
} as const;

export const radius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  pill: '999px',
} as const;

export const typography = {
  fontFamily:
    "'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
  monoFamily: "'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace",
} as const;

export type StatusTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

export type Palette = typeof palette;
