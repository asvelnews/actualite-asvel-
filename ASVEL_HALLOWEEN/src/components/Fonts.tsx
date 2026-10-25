import {FONT_CSS} from './fonts.generated';

// Polices libres (SIL OFL) intégrées en data-URL : décodage immédiat, aucun réseau,
// aucun delayRender (qui restait bloqué avec le rendu SwiftShader).
if (typeof document !== 'undefined' && !document.getElementById('asvel-fonts')) {
  const st = document.createElement('style');
  st.id = 'asvel-fonts';
  st.textContent = FONT_CSS;
  document.head.appendChild(st);
  ['400 40px Anton', '400 40px Creepster', '400 40px Oswald', '700 40px Oswald'].forEach((f) => document.fonts.load(f));
}

export const FONT = {
  title: 'Anton, Impact, sans-serif',
  horror: 'Creepster, Anton, sans-serif',
  body: 'Oswald, Arial Narrow, sans-serif',
};

export const C = {
  black: '#080608',
  blood: '#D71920',
  ember: '#FF641B',
  white: '#F4F1EC',
  gold: '#D6A85A',
};
