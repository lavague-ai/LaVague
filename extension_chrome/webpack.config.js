const CopyPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const Dotenv = require('dotenv-webpack');
const TerserPlugin = require('terser-webpack-plugin');
const path = require('path');
const outputPath = 'dist';

module.exports = (env, { mode }) => {
    const isProduction = mode === 'production';

    return {
        entry: {
            main: [path.resolve(__dirname, 'src', 'main.ts')],
            background: path.resolve(__dirname, 'src', 'background.ts'),
            content: path.resolve(__dirname, 'src', 'content.ts'),
        },
        output: {
            path: path.join(__dirname, outputPath),
            filename: '[name].js',
        },
        resolve: {
            extensions: ['.tsx', '.ts', '.js'],
            alias: {
                '@': path.resolve(__dirname, 'src/'),
            },
        },
        module: {
            rules: [
                {
                    test: /\.(ts|tsx)?$/,
                    use: 'ts-loader',
                    exclude: /node_modules/,
                },
                {
                    test: /\.?(js|jsx)$/,
                    exclude: /node_modules/,
                    use: {
                        loader: 'babel-loader',
                        options: {
                            presets: ['@babel/preset-env', '@babel/preset-react', '@babel/preset-typescript'],
                            plugins: [
                                [
                                    'babel-plugin-styled-components',
                                    {
                                        minify: isProduction,
                                        transpileTemplateLiterals: isProduction,
                                    },
                                ],
                            ],
                        },
                    },
                },
                {
                    test: /\.s[ac]ss$/i,
                    use: ['style-loader', 'css-loader', 'sass-loader'],
                },
                {
                    test: /\.(jpg|jpeg|png|gif|woff|woff2|eot|ttf|svg)$/i,
                    use: 'url-loader?limit=1024',
                },
            ],
        },
        plugins: [
            new CopyPlugin({
                patterns: [{ from: '.', to: '.', context: 'public' }],
            }),
            new MiniCssExtractPlugin({
                filename: '[name].css',
            }),
            new Dotenv(),
        ],
        optimization: {
            minimize: isProduction,
            mergeDuplicateChunks: true,
            removeEmptyChunks: true,
            sideEffects: false,
            minimizer: [
                new TerserPlugin({
                    terserOptions: {
                        keep_classnames: true,
                        keep_fnames: true,
                    },
                }),
            ],
        },
        devtool: isProduction ? 'source-map' : 'inline-source-map',
    };
};
