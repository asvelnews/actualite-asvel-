import {Config} from '@remotion/cli/config';

// Rendu 60 FPS, PNG intermédiaire pour garder la qualité des dégradés de fumée
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
Config.setPublicDir('./public');
Config.setChromiumOpenGlRenderer('angle'); // composition logicielle : les effets sont calculés sur CPU
// Chromium headless préinstallé (sur Windows, supprimer cette ligne : Remotion télécharge le sien)
if (process.platform === 'linux' && require('fs').existsSync('/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell')) {
  Config.setBrowserExecutable('/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell');
}
