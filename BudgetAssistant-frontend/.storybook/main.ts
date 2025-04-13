import type { StorybookConfig } from '@storybook/angular';
import path from 'path';

const config: StorybookConfig = {
  "stories": [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  "addons": [
    "@storybook/addon-essentials",
    "@storybook/addon-onboarding",
    "@chromatic-com/storybook",
    "@storybook/addon-interactions"
  ],
  "framework": {
    "name": "@storybook/angular",
    "options": {}
  },
  webpackFinal: async (baseConfig) => {
    if (!baseConfig.resolve) {
      baseConfig.resolve = {};
    }
    baseConfig.resolve.alias = {
      ...(baseConfig.resolve.alias || {}),
      '@daanvdn/budget-assistant-client': path.resolve(__dirname, '../node_modules/@daanvdn/budget-assistant-client'),
      '@daanvdn/budget-assistant-client/model': path.resolve(__dirname, '../node_modules/@daanvdn/budget-assistant-client/model')

    };
    baseConfig.devtool = 'source-map';

    return baseConfig;
  },
};
export default config;