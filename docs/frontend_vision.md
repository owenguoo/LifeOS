# LifeOS Frontend Vision

## Design Philosophy

### Core Principles
- **Mobile-First**: Prioritized for mobile web experience
- **Dark Minimalistic**: Clean, uncluttered interface with a blurred gradient background  

## Design System

### Color Palette
```css
/* Primary Colors */
--background: #0d0d0d          /* Deep black background */
--surface: #1a1a1a             /* Elevated surfaces */
--surface-hover: #2a2a2a       /* Interactive elements */
--primary: #7a2246             /* Burgundy accent */
--primary-hover: #5a1a35       /* Darker burgundy for interactions */

/* Text Colors */
--text-primary: #f1f1f1        /* Primary text */
--text-secondary: #a1a1aa      /* Secondary text */
--text-muted: #71717a          /* Muted text */
--text-accent: #f2858e         /* Coral accent text */

/* Status Colors */
--success: #10b981             /* Green for positive actions */
--warning: #f59e0b             /* Amber for warnings */
--error: #ef4444               /* Red for errors */
--info: #f2858e                /* Coral for information */

/* Borders & Dividers */
--border: #27272a              /* Subtle borders */
--border-hover: #3f3f46        /* Interactive borders */

/* Blurred Background Colors */
--bg-blur-primary: #0d0d0d      /* Deep black base */
--bg-blur-secondary: #7a2246    /* Burgundy transition */
--bg-blur-accent: #f2858e       /* Coral highlight */

/* Background Blur Effect */
--bg-blur: blur(40px)           /* Heavy blur for atmospheric effect */
--bg-opacity: 0.8               /* Subtle transparency */
```

### Typography
```css
/* Font Stack */
font-family: 'Onest', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Scale */
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
```

### Spacing & Layout
```css
/* Spacing Scale */
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
--space-12: 3rem     /* 48px */

/* Container Max Widths */
--container-sm: 640px
--container-md: 768px
--container-lg: 1024px
```

## Layout Structure

### Mobile-First Layout
```
┌─────────────────────────────────┐
│           LifeOS                │ ← Fixed top 
│      "Today you did ___"        │
├─────────────────────────────────┤
│                                 │
|        (search bar)             |
│        Widget (ex. time)        │ 
│                                 │
│                                 │
├─────────────────────────────────┤
│   Bottom Navigation (ALL ICONS) | ← Fixed bottom
│  [Chat] [Activity] [Automations]│
└─────────────────────────────────┘
```
Imagine it like a desktop wallpaper screen rather than a traditional website.
IT IS PRIMARILY FOR MOBILE USE, PRIORITIZE IT

## Component Library
#### Top Header
- Daily summary "today you did ___" (animation to change it every 10 seconds)
(SAVED FOR LATER, DO NOT IMPLEMENT) <!-- - Quick action buttons (user, settings) -->

#### Search Bar
- Centered with rounded corners
- Recent searches dropdown

#### Customizable dashboard widgets
- Takes up same horizontal space as search bar
- Start with just the a basic time widget (ex. 21:31)

#### Activity Feed
- Chronological list of recent memories
- Grouped by time periods (Today, Yesterday, This Week)
- Pull-to-refresh functionality

#### Chat Interface
- Use Vercel's Next.js AI Chatbot template (DO NOT IMPLEMENT ON YOUR OWN, I WILL ADD IT)

#### Automations
- List of available automations (just Google Calendar for now) with a toggle on/off

## Technical Implementation

### Framework & Libraries
- **Next.js 15** with App Router
- **Tailwind CSS** for styling
- **ShadCN** for components
- **Framer Motion** for animations
- **Zustand** for state management (if needed)

### Component Architecture
```
src/
├── components/
│   ├── ...
├── hooks/            # Custom React hooks
├── lib/              # Utility functions
└── styles/           # Global styles
```

### State Management
- Local component state for UI interactions
(SAVED FOR LATER, DO NOT IMPLEMENT) <!-- - Global state for user preferences and app settings -->
- Server state management with React Query

---

*This vision document serves as the foundation for all frontend development decisions and should be referenced when making design and implementation choices.* 