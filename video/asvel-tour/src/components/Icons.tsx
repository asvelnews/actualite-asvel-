// Pictogrammes vectoriels dessinés à la main (aucune image, aucun emoji).
import React from 'react';

type P = {size?: number; color?: string; style?: React.CSSProperties};

export const Check: React.FC<P & {bg?: string}> = ({size = 28, color = '#fff', bg = '#1FD16B', style}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" style={style}>
		<rect x="1" y="1" width="22" height="22" rx="5" fill={bg} />
		<path d="M6.2 12.4l3.7 3.7 7.9-8.3" fill="none" stroke={color} strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
	</svg>
);

export const Plane: React.FC<P> = ({size = 28, color = '#fff', style}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" style={style}>
		<path
			d="M21.5 12c0-.8-.7-1.4-1.5-1.4h-5.2L9.6 2.5H7.5l2.6 8.1H5.2L3.6 8.4H2l1 3.6-1 3.6h1.6l1.6-2.2h4.9l-2.6 8.1h2.1l5.2-8.1H20c.8 0 1.5-.6 1.5-1.4z"
			fill={color}
		/>
	</svg>
);

export const Bus: React.FC<P> = ({size = 28, color = '#fff', style}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" style={style}>
		<rect x="3" y="3" width="18" height="15" rx="3" fill={color} />
		<rect x="5" y="5.5" width="14" height="6" rx="1" fill="#070B10" />
		<circle cx="7.5" cy="15" r="1.3" fill="#070B10" />
		<circle cx="16.5" cy="15" r="1.3" fill="#070B10" />
		<rect x="5" y="18" width="3" height="3" rx="1" fill={color} />
		<rect x="16" y="18" width="3" height="3" rx="1" fill={color} />
	</svg>
);

export const Flame: React.FC<P> = ({size = 28, color = '#FF6A2B', style}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" style={style}>
		<path d="M12 2c.6 3.6 5.8 6.1 5.8 12a5.8 5.8 0 01-11.6 0c0-2.6 1.4-4.4 2.6-5.6.2 1.8 1 2.9 2.1 3.4C10.6 8.6 11 5.4 12 2z" fill={color} />
		<path d="M12 12.2c1.6 1.6 2.9 2.9 2.9 4.7a2.9 2.9 0 01-5.8 0c0-1.5.9-2.6 2.9-4.7z" fill="#FFD23F" />
	</svg>
);

export const House: React.FC<P> = ({size = 28, color = '#fff', style}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" style={style}>
		<path d="M12 3l9 8h-2.6v9.5H14.2v-6h-4.4v6H5.6V11H3z" fill={color} />
	</svg>
);

export const Stadium: React.FC<P> = ({size = 28, color = '#fff', style}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" style={style}>
		<ellipse cx="12" cy="9" rx="10" ry="4" fill="none" stroke={color} strokeWidth="2" />
		<path d="M2 9v6c0 2.2 4.5 4 10 4s10-1.8 10-4V9" fill="none" stroke={color} strokeWidth="2" />
		<ellipse cx="12" cy="9" rx="5" ry="1.8" fill={color} />
		<path d="M7 17.6v-4M12 18.8v-4.4M17 17.6v-4" stroke={color} strokeWidth="1.6" />
	</svg>
);
