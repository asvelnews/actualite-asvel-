"""Encode les polices OFL de public/fonts en base64 dans src/components/fonts.generated.ts."""
import base64
fonts = [('Anton', 'anton-latin-400-normal.woff2', '400'), ('Creepster', 'creepster-latin-400-normal.woff2', '400'),
         ('Oswald', 'oswald-latin-400-normal.woff2', '400'), ('Oswald', 'oswald-latin-700-normal.woff2', '700')]
css = ''.join(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:block;src:url(data:font/woff2;base64,{base64.b64encode(open('public/fonts/' + f, 'rb').read()).decode()}) format('woff2');}}" for fam, f, w in fonts)
open('src/components/fonts.generated.ts', 'w').write('// Généré par tools_embed_fonts.py — polices SIL OFL encodées en base64\nexport const FONT_CSS = ' + repr(css) + ';\n')
