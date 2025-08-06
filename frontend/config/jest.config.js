module.exports = {
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [
    '/node_modules/(?!(react-markdown|remark-parse|remark-gfm|unified|bail|is-plain-obj|trough|vfile|vfile-message|unist-util-visit|unist-util-stringify-position|mdast-util-to-string)/)'
  ],
}; 