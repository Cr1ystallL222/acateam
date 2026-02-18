import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: '#E60000', // Red for buttons/badges
                secondary: '#1A1A1A', // Dark grey for header/footer
                'dark-bg': '#2E2E2E', // Header background
                'text-main': '#171717',
                'text-muted': '#9CA3AF',
            },
            container: {
                center: true,
                padding: '1rem',
                screens: {
                    '2xl': '1280px',
                },
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
export default config
