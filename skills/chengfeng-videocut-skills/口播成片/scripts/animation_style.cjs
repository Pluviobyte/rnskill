const fs = require("fs");
const path = require("path");
const { loadUserConfig } = require("./user_config.cjs");

const SKILL_DIR = path.resolve(__dirname, "..");
const DEFAULT_ANIMATION_STYLES_PATH = path.join(SKILL_DIR, "动画", "styles.json");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function resolveInsideAnimation(relativePath) {
  return path.join(SKILL_DIR, "动画", relativePath);
}

function loadAnimationStyle(options = {}) {
  const stylesPath = path.resolve(options.stylesPath || DEFAULT_ANIMATION_STYLES_PATH);
  if (!fs.existsSync(stylesPath)) {
    throw new Error(`Animation styles registry not found: ${stylesPath}`);
  }

  const userConfig = loadUserConfig({
    configPath: options.userConfigPath || options.configPath,
  });
  const registry = readJson(stylesPath);
  const styleName = String(options.style || userConfig.animationStyle || "xiaohei").trim();
  const style = registry.styles && registry.styles[styleName];
  if (!style) {
    const available = Object.keys(registry.styles || {}).join(", ");
    throw new Error(`Unknown animation style "${styleName}". Available styles: ${available}`);
  }

  return {
    registry,
    stylesPath,
    userConfigPath: userConfig.configPath,
    styleName,
    label: style.label || styleName,
    skillDir: style.skillDir ? resolveInsideAnimation(style.skillDir) : "",
    skillFile: style.skillFile ? resolveInsideAnimation(style.skillFile) : "",
    templateDir: style.templateDir ? resolveInsideAnimation(style.templateDir) : "",
  };
}

function renderAnimationSummary(animationStyle) {
  return `${animationStyle.label} (${animationStyle.styleName})`;
}

module.exports = {
  DEFAULT_ANIMATION_STYLES_PATH,
  loadAnimationStyle,
  renderAnimationSummary,
};
