/* eslint-env node */
/**
 * Smart-EMAPs フロントエンド ESLint 設定
 * - Vue3 + TypeScript + Prettier 連携
 * - 既存コードへの影響を最小にするため、warn ベースで段階的適用
 */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 'latest',
    sourceType: 'module',
    extraFileExtensions: ['.vue'],
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:vue/vue3-recommended',
    'prettier',
  ],
  plugins: ['@typescript-eslint', 'vue'],
  rules: {
    // TypeScript / Vue コンパイラが未使用・未定義を検出するため ESLint の no-undef は二重になる
    'no-undef': 'off',
    // 既存コードに合わせた緩和（必要に応じて段階的に厳格化）
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    '@typescript-eslint/no-non-null-asserted-optional-chain': 'warn',
    'no-unused-vars': 'off',
    // 日本語コメント・UI 文言での全角スペース等を許容
    'no-irregular-whitespace': 'off',
    'no-useless-escape': 'warn',
    'no-constant-condition': 'warn',
    'no-case-declarations': 'warn',
    'no-unsafe-finally': 'warn',
    'no-empty': 'warn',
    'no-dupe-else-if': 'warn',
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'off',
    'vue/require-default-prop': 'off',
    'vue/no-use-v-if-with-v-for': 'warn',
    'vue/valid-v-for': 'warn',
    'vue/no-deprecated-filter': 'off',
    'vue/no-ref-as-operand': 'warn',
    'vue/attributes-order': 'warn',
    'vue/html-self-closing': 'off',
    'vue/max-attributes-per-line': 'off',
    'vue/singleline-html-element-content-newline': 'off',
    'vue/html-indent': 'off',
    'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
    'no-debugger': 'warn',
  },
  ignorePatterns: [
    'dist/',
    'node_modules/',
    'public/',
    'src/auto-imports.d.ts',
    'src/components.d.ts',
    '*.min.js',
  ],
  overrides: [
    {
      files: ['*.vue'],
      rules: {
        '@typescript-eslint/no-unused-vars': 'off',
      },
    },
  ],
}
