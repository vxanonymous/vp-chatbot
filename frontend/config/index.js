/**
 * Frontend Configuration Module
 * 
 * This module contains all frontend configuration files including:
 * - Build configuration (vite.config.js, babel.config.js)
 * - Styling configuration (tailwind.config.js, postcss.config.js)
 * - Testing configuration (jest.config.js)
 * - Deployment configuration (nginx.conf)
 * - Package management (package.json, package-lock.json)
 * - Environment configuration (.env files)
 */

// Export all configuration files
export { default as viteConfig } from './vite.config.js';
export { default as babelConfig } from './babel.config.js';
export { default as tailwindConfig } from './tailwind.config.js';
export { default as postcssConfig } from './postcss.config.js';
export { default as jestConfig } from './jest.config.js';
export { default as nginxConfig } from './nginx.conf';

// Package configuration
export { default as packageConfig } from './package.json';

// Environment configuration
export const envConfig = {
  development: import.meta.env.DEV,
  production: import.meta.env.PROD,
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  environment: import.meta.env.MODE || 'development'
};

export default {
  vite: viteConfig,
  babel: babelConfig,
  tailwind: tailwindConfig,
  postcss: postcssConfig,
  jest: jestConfig,
  nginx: nginxConfig,
  package: packageConfig,
  env: envConfig
}; 