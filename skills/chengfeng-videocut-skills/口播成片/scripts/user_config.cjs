const fs = require("fs");
const path = require("path");

const SKILL_DIR = path.resolve(__dirname, "..");
const DEFAULT_CONFIG_PATH = path.join(SKILL_DIR, "用户配置", "default.json");

const ASPECT_RATIO_PRESETS = {
  "3:4": {
    label: "3:4 竖屏高清",
    width: 1080,
    height: 1440,
    deviceScaleFactor: 1.5,
  },
  "16:9": {
    label: "16:9 横屏",
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
  },
  "4:3": {
    label: "4:3 横屏",
    width: 1440,
    height: 1080,
    deviceScaleFactor: 1,
  },
};

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function normalizeAspectRatio(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, "")
    .replace("：", ":");
}

function loadUserConfig(options = {}) {
  const configPath = path.resolve(options.configPath || DEFAULT_CONFIG_PATH);
  if (!fs.existsSync(configPath)) {
    throw new Error(`User config not found: ${configPath}`);
  }

  const config = readJson(configPath);
  const aspectRatio = normalizeAspectRatio(options.aspectRatio || config.aspectRatio || "3:4");
  const preset = ASPECT_RATIO_PRESETS[aspectRatio];
  if (!preset) {
    const available = Object.keys(ASPECT_RATIO_PRESETS).join(", ");
    throw new Error(`Unknown user config aspectRatio "${aspectRatio}". Available ratios: ${available}`);
  }

  return {
    config,
    configPath,
    aspectRatio,
    animationStyle: String(config.animationStyle || "xiaohei").trim(),
    label: preset.label,
    width: preset.width,
    height: preset.height,
    deviceScaleFactor: preset.deviceScaleFactor || 1,
    outputWidth: Math.round(preset.width * (preset.deviceScaleFactor || 1)),
    outputHeight: Math.round(preset.height * (preset.deviceScaleFactor || 1)),
  };
}

function renderSummary(userConfig) {
  const dpr = Number(userConfig.deviceScaleFactor || 1);
  const outputWidth = userConfig.outputWidth || Math.round(userConfig.width * dpr);
  const outputHeight = userConfig.outputHeight || Math.round(userConfig.height * dpr);
  if (dpr === 1) return `${userConfig.label} ${outputWidth}x${outputHeight}`;
  return `${userConfig.label} ${outputWidth}x${outputHeight} (logical ${userConfig.width}x${userConfig.height}, dpr ${dpr})`;
}

module.exports = {
  DEFAULT_CONFIG_PATH,
  ASPECT_RATIO_PRESETS,
  loadUserConfig,
  renderSummary,
};
