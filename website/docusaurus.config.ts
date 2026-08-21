import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'AI-Native Development Course',
  tagline: 'From zero to building production AI systems',
  favicon: 'img/favicon.ico',

  url: 'https://gauravprwl14.github.io',
  baseUrl: '/ai-native-course/',

  organizationName: 'gauravprwl14',
  projectName: 'ai-native-course',

  onBrokenLinks: 'warn', // ConceptMap uses slug-only hrefs; would need a full slug→tier lookup to generate correct paths
  onBrokenMarkdownLinks: 'warn',

  // Prevent flash-of-wrong-theme + preconnect for Google Fonts performance.
  headTags: [
    {
      tagName: 'script',
      attributes: {},
      innerHTML: `(function(){try{var t=localStorage.getItem('theme');document.documentElement.setAttribute('data-theme',t&&(t==='light'||t==='dark')?t:'dark')}catch(e){}})();`,
    },
    { tagName: 'link', attributes: { rel: 'preconnect', href: 'https://fonts.googleapis.com' } },
    { tagName: 'link', attributes: { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: 'anonymous' } },
  ],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          showLastUpdateTime: true,
          showLastUpdateAuthor: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Default to dark; user can still toggle.
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },

    image: 'img/social-card.png',
    navbar: {
      title: 'AI-Native Course',
      logo: {
        alt: 'AI-Native Course Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'courseSidebar',
          position: 'left',
          label: 'Course',
        },
        {
          href: 'https://github.com/gauravprwl14/ai-native-course',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Tiers',
          items: [
            { label: 'Tier 1 — Foundations', to: '/tier-1-foundations' },
            { label: 'Tier 2 — Builder', to: '/tier-2-builder' },
            { label: 'Tier 3 — Advanced', to: '/tier-3-advanced' },
            { label: 'Tier 4 — Architect', to: '/tier-4-architect' },
          ],
        },
        {
          title: 'Resources',
          items: [
            { label: 'GitHub', href: 'https://github.com/gauravprwl14/ai-native-course' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} AI-Native Course. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'json', 'yaml', 'typescript'],
    },
    // Switch from 'neutral' (grey) to 'base' (coloured) for light mode.
    // Dark mode keeps the built-in 'dark' theme.
    mermaid: {
      theme: { light: 'base', dark: 'dark' },
      options: {
        themeVariables: {
          primaryColor: '#0891b2',
          primaryTextColor: '#ffffff',
          primaryBorderColor: '#0e7490',
          lineColor: '#8b949e',
          secondaryColor: '#cffafe',
          tertiaryColor: '#ecfeff',
          background: '#ffffff',
          mainBkg: '#0891b2',
          nodeBorder: '#0e7490',
          clusterBkg: '#ecfeff',
          titleColor: '#0d1117',
          edgeLabelBackground: '#ffffff',
          fontFamily: 'Inter, system-ui, sans-serif',
        },
      },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
