import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const DIST_DIR = path.join(ROOT_DIR, 'dist');
const WEB_DIR = path.join(ROOT_DIR, 'idp-platform', 'web');
const LITHOS_DIR = path.join(ROOT_DIR, 'idp-platform', 'lithos');

console.log('🚀 Starting Parsa.ai Production Build...');

// 1. Clean & recreate dist directory
if (fs.existsSync(DIST_DIR)) {
  fs.rmSync(DIST_DIR, { recursive: true, force: true });
}
fs.mkdirSync(DIST_DIR, { recursive: true });
fs.mkdirSync(path.join(DIST_DIR, 'static'), { recursive: true });

// 2. Build lithos Vite React app if present
if (fs.existsSync(LITHOS_DIR) && fs.existsSync(path.join(LITHOS_DIR, 'package.json'))) {
  console.log('📦 Building Lithos Vite/React app...');
  try {
    // Check if node_modules exists, if not install
    if (!fs.existsSync(path.join(LITHOS_DIR, 'node_modules'))) {
      console.log('📦 Installing lithos dependencies...');
      execSync('npm install', { cwd: LITHOS_DIR, stdio: 'inherit' });
    }
    execSync('npm run build', { cwd: LITHOS_DIR, stdio: 'inherit' });
    const lithosDist = path.join(LITHOS_DIR, 'dist');
    if (fs.existsSync(lithosDist)) {
      const targetLithosDist = path.join(DIST_DIR, 'lithos');
      fs.cpSync(lithosDist, targetLithosDist, { recursive: true });
      console.log('✅ Copied lithos dist to dist/lithos');
    }
  } catch (err) {
    console.warn('⚠️ Lithos build warning (non-fatal):', err.message);
  }
}

// 3. Copy Web static assets into dist and dist/static
if (fs.existsSync(WEB_DIR)) {
  console.log('📄 Packaging Parsa.ai Web UI assets...');
  const files = fs.readdirSync(WEB_DIR);
  for (const file of files) {
    const srcPath = path.join(WEB_DIR, file);
    const destPath = path.join(DIST_DIR, file);
    const staticDestPath = path.join(DIST_DIR, 'static', file);

    const stat = fs.statSync(srcPath);
    if (stat.isFile()) {
      fs.copyFileSync(srcPath, destPath);
      fs.copyFileSync(srcPath, staticDestPath);
    } else if (stat.isDirectory()) {
      fs.cpSync(srcPath, destPath, { recursive: true });
      fs.cpSync(srcPath, staticDestPath, { recursive: true });
    }
  }

  // Ensure homepage.html is set as primary index.html
  const homepageSrc = path.join(WEB_DIR, 'homepage.html');
  if (fs.existsSync(homepageSrc)) {
    fs.copyFileSync(homepageSrc, path.join(DIST_DIR, 'index.html'));
    fs.copyFileSync(homepageSrc, path.join(DIST_DIR, 'homepage.html'));
  }

  // Alias additional entrypoints for clean fallback
  const indexSrc = path.join(WEB_DIR, 'index.html');
  if (fs.existsSync(indexSrc)) {
    fs.copyFileSync(indexSrc, path.join(DIST_DIR, 'workspace.html'));
    fs.copyFileSync(indexSrc, path.join(DIST_DIR, 'studio.html'));
    fs.copyFileSync(indexSrc, path.join(DIST_DIR, 'ui.html'));
  }

  const apikeysSrc = path.join(WEB_DIR, 'apikeys.html');
  if (fs.existsSync(apikeysSrc)) {
    fs.copyFileSync(apikeysSrc, path.join(DIST_DIR, 'apikeys.html'));
    fs.copyFileSync(apikeysSrc, path.join(DIST_DIR, 'api-keys.html'));
    fs.copyFileSync(apikeysSrc, path.join(DIST_DIR, 'keys.html'));
  }

  console.log('✅ Parsa.ai Web UI packaged successfully into dist/');
}

// 4. Copy root wallpaper if present
const wallpaperName = 'mountains-wallpaper-3840x2160-winter-wonderland-picturesque-nature-12805.jpg';
const rootWallpaper = path.join(ROOT_DIR, wallpaperName);
if (fs.existsSync(rootWallpaper)) {
  fs.copyFileSync(rootWallpaper, path.join(DIST_DIR, wallpaperName));
  fs.copyFileSync(rootWallpaper, path.join(DIST_DIR, 'static', wallpaperName));
}

console.log('🎉 Production build complete! Output is in dist/');
