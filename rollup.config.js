import nodeResolve from '@rollup/plugin-node-resolve'; // Resolve node paths in scripts
import terser from '@rollup/plugin-terser'; // Minify
import { summary } from 'rollup-plugin-summary'; // Summarize build metrics
import 'dotenv/config';

const isProd = process.env.NODE_ENV === 'production';
console.log('Is prod:', isProd);

// Bundle JS -- don't need to hash as handled by Flask
export default [
	{
		input: './static/src/js/index.js',
		output: {
			dir: './static/public/',
			format: 'iife',
		},
		plugins: isProd
			? [nodeResolve(), terser(), summary()]
			: [nodeResolve()],
	},
];
