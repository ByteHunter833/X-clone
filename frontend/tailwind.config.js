module.exports = {
	extend: {
		animation: {
			fadeIn: 'fadeIn 0.5s ease-in forwards',
		},
		keyframes: {
			fadeIn: {
				'0%': { opacity: '0' },
				'100%': { opacity: '1' },
			},
		},
	},
}
