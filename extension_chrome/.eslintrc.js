module.exports = {
    env: {
        browser: true,
        es2021: true,
        node: true,
    },
    extends: ['eslint:recommended', 'plugin:react/recommended', 'plugin:react-hooks/recommended', 'plugin:@typescript-eslint/recommended'],
    parser: '@typescript-eslint/parser',
    parserOptions: {
        ecmaFeatures: {
            jsx: true,
        },
        ecmaVersion: 2020,
        sourceType: 'module',
    },
    plugins: ['react', 'react-hooks', 'prettier', '@typescript-eslint'],
    rules: {
        'prettier/prettier': ['error', { endOfLine: 'auto' }],
        'react/react-in-jsx-scope': ['off'],
        'no-use-before-define': ['error', 'nofunc'],
        '@typescript-eslint/no-use-before-define': ['error', 'nofunc'],
        '@typescript-eslint/explicit-module-boundary-types': ['off'],
        '@typescript-eslint/ban-ts-comment': 0,
        '@typescript-eslint/no-var-requires': 0,
        '@typescript-eslint/no-explicit-any': 0,
        '@typescript-eslint/no-non-null-assertion': 0,
    },
    settings: {
        react: {
            version: 'detect',
        },
    },
};
