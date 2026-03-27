import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'AI-Native Development Course',
  tagline: 'From zero to building production AI systems',
  favicon: 'img/favicon.ico',

  url: 'https://your-org.github.io',
  baseUrl: '/ai-native-course/',

  organizationName: 'your-org',
  projectName: 'ai-native-course',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

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
          href: 'https://github.com/your-org/ai-native-course',
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
            { label: 'GitHub', href: 'https://github.com/your-org/ai-native-course' },
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
    mermaid: {
      theme: { light: 'neutral', dark: 'dark' },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
