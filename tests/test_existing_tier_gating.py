import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data_js = (ROOT / "data.js").read_text(encoding="utf-8")
patches_js = (ROOT / "patches.js").read_text(encoding="utf-8")
index_html = (ROOT / "index.html").read_text(encoding="utf-8")
scripts = re.findall(r"<script[^>]*>([\s\S]*?)</script>", index_html)
main_js = max(scripts, key=len)

jxa_driver = r'''
const elements = {};
function makeEl(id, tag) {
  const el = {
    id: id || "",
    tagName: (tag || "div").toUpperCase(),
    className: "",
    style: {},
    _innerHTML: "",
    get innerHTML() { return this._innerHTML; },
    set innerHTML(v) { this._innerHTML = String(v); if (this._innerHTML === "") this.children = []; },
    textContent: "",
    disabled: false,
    children: [],
    dataset: {},
    classList: {
      add() {},
      remove() {},
      toggle() {},
      contains() { return false; }
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    _listeners: {},
    addEventListener(evt, fn) {
      this._listeners[evt] = this._listeners[evt] || [];
      this._listeners[evt].push(fn);
    },
    removeEventListener() {},
    querySelectorAll() { return []; },
    querySelector(sel) { return makeEl("", sel || "div"); },
    scrollIntoView() {},
    click() {
      if (this.disabled) return;
      if (this.onclick) this.onclick();
      (this._listeners["click"] || []).forEach(fn => fn());
    }
  };
  return el;
}

const document = {
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl(id, "div");
    return elements[id];
  },
  createElement(tag) {
    return makeEl("", tag);
  },
  querySelectorAll() { return []; },
  querySelector() { return null; },
  addEventListener() {},
  body: makeEl("body", "body")
};

const window = this;
window.innerWidth = 1280;
window.addEventListener = function() {};
window.scrollTo = function() {};
const localStorage = {
  _d: {},
  getItem(k) { return Object.prototype.hasOwnProperty.call(this._d, k) ? this._d[k] : null; },
  setItem(k, v) { this._d[k] = String(v); },
  removeItem(k) { delete this._d[k]; }
};
const console = { log() {}, warn() {}, error() {} };
function alert() {}
function confirm() { return true; }
function setTimeout() { return 0; }
function clearTimeout() {}
function setInterval() { return 0; }
function clearInterval() {}
function Audio() { return { play() { return Promise.resolve(); }, pause() {}, addEventListener() {} }; }
'''

test_tail = r'''
function makeBasePlayer(skills) {
  return {
    name: "柳忘機",
    gender: "男",
    title: "玄鏡銅章捕快",
    age: 23,
    month: 6,
    maxLifespan: 56,
    sect: "無門無派",
    tier: "凡胎俗骨",
    stats: { wu: 51, de: 73, ming: 37, qing: 70, cai: 31 },
    innateTalents: [],
    qi: 100,
    badges: ["商賈之家", "精打細算", "玄鏡銅章捕快"],
    titles: [],
    equippedWeapon: { name: "精鋼百煉刀", tier: 2 },
    ownedWeapons: [{ name: "精鋼百煉刀", tier: 2 }],
    sealedWeapons: [],
    weaponHistoryFlags: new Set(),
    artifacts: [],
    collectedManuals: [],
    skills: skills,
    bonds: [],
    children: [],
    disciples: [],
    worldHistory: [],
    usedEvents: new Set(),
    usedEpochEvents: new Set(),
    triggeredBattles: new Set(),
    triggeredAllianceLeaderEvents: new Set(),
    fakedDeath: false,
    inImmortalPhase: false,
    isDead: false,
    hasCreatedOwnSkill: false,
    ownSkillName: null,
    isAllianceLeader: false,
    logs: []
  };
}

function findEncounterOwner(encId) {
  for (let i = 0; i < DB.CHARACTERS.length; i++) {
    const ch = DB.CHARACTERS[i];
    const enc = (ch.encounters || []).find(e => e.id === encId);
    if (enc) return { ch, enc };
  }
  return null;
}

function forceTriggerSpecificScenario(charId, encId) {
  const ch = DB.CHARACTERS.find(c => c.id === charId);
  const origEnc = ch.encounters.slice();
  const targetEnc = origEnc.find(e => e.id === encId);
  if (!targetEnc) throw new Error("Missing encounter " + encId);
  ch.encounters = [Object.assign({}, targetEnc, { minIntimacy: 0 })];
  document.getElementById("ev-modal-choices").children = [];
  triggerCompanionEncounter(charId);
  ch.encounters = origEnc;
  return document.getElementById("ev-modal-choices").children.map(btn => ({
    text: btn.innerHTML,
    disabled: !!btn.disabled
  }));
}

const report = { ok: true, checks: {} };

// Test 7A: Screenshot exact build on xhz_s5_2 (金殿叩閽 · 雙俠護萬民請命書)
const screenshotSkills = [
  { id: "tiyunzong", name: "梯雲縱", tier: "上乘", type: "輕功/身法", pendingEnlightenment: true, reqWu: 65, desc: "道門無上輕身之法" },
  { id: "cdcl", name: "彩蝶穿林", tier: "進階", type: "輕功/身法", exp: 10 },
  { id: "jfb", name: "疾風步", tier: "進階", type: "輕功/身法", exp: 20 },
  { id: "sxbf", name: "四象步法", tier: "進階", type: "輕功/身法", exp: 20 }
];
const xhzOwner = findEncounterOwner("xhz_s5_2");
if (!xhzOwner) throw new Error("xhz_s5_2 not found");
player = makeBasePlayer(JSON.parse(JSON.stringify(screenshotSkills)));
player.bonds = [{
  id: xhzOwner.ch.id,
  name: xhzOwner.ch.name,
  intimacyIndex: 5,
  tacit: 10,
  triggeredEncounters: [],
  usedEncounterIndices: [],
  isDead: false
}];
const xhzLowChoices = forceTriggerSpecificScenario(xhzOwner.ch.id, "xhz_s5_2");
report.checks.xhzLowChoices = xhzLowChoices;

if (xhzLowChoices.length !== 3) {
  throw new Error("Expected 3 choices for xhz_s5_2, got " + xhzLowChoices.length);
}
const zhenpaiOptLow = xhzLowChoices.find(c => c.text.includes("以一招看家絕學開道"));
if (!zhenpaiOptLow) throw new Error("Missing 以一招看家絕學開道 option in xhzLowChoices: " + JSON.stringify(xhzLowChoices));
if (!zhenpaiOptLow.disabled) throw new Error("以一招看家絕學開道 should be disabled without 上乘招式");
if (!zhenpaiOptLow.text.includes("🔒 【需上乘以上招式】")) throw new Error("Missing 🔒 【需上乘以上招式】 badge");
if (!zhenpaiOptLow.text.includes("以一招看家絕學開道，劈開漫天箭雨")) throw new Error("Unexpected placeholder in locked text: " + zhenpaiOptLow.text);
if (zhenpaiOptLow.text.includes("《") || zhenpaiOptLow.text.includes("【】")) throw new Error("Dirty brackets in locked text: " + zhenpaiOptLow.text);
const mingOptLow = xhzLowChoices.find(c => c.text.includes("動用江湖百派人脈"));
if (!mingOptLow || mingOptLow.disabled) throw new Error("動用江湖百派人脈 should remain unlocked");

// Test 7B: With 上乘招式 羅剎修羅槍 (relaxed from 鎮派 to 上乘!)
const highSkills = screenshotSkills.concat([
  { id: "luosha", name: "羅剎修羅槍", tier: "上乘", type: "招式", weapon: "槍棍", exp: 20 }
]);
player = makeBasePlayer(highSkills);
player.stats.wu = 72;
player.bonds = [{
  id: xhzOwner.ch.id,
  name: xhzOwner.ch.name,
  intimacyIndex: 5,
  tacit: 10,
  triggeredEncounters: [],
  usedEncounterIndices: [],
  isDead: false
}];
const xhzHighChoices = forceTriggerSpecificScenario(xhzOwner.ch.id, "xhz_s5_2");
report.checks.xhzHighChoices = xhzHighChoices;
const zhenpaiOptHigh = xhzHighChoices.find(c => c.text.includes("以一招《羅剎修羅槍》開道"));
if (!zhenpaiOptHigh || zhenpaiOptHigh.disabled) throw new Error("以一招《羅剎修羅槍》開道 should unlock with 上乘招式");
if (!zhenpaiOptHigh.text.includes("✨ 【上乘招式 · 《羅剎修羅槍》】")) throw new Error("Missing 羅剎修羅槍 badge: " + zhenpaiOptHigh.text);

// Test 8: Dual-gated encounter fallback (lyr_s5_2)
const lyrOwner = findEncounterOwner("lyr_s5_2");
if (!lyrOwner) throw new Error("lyr_s5_2 not found");
player = makeBasePlayer(JSON.parse(JSON.stringify(screenshotSkills)));
player.stats = { wu: 40, de: 40, ming: 40, qing: 40, cai: 10 };
player.bonds = [{
  id: lyrOwner.ch.id,
  name: lyrOwner.ch.name,
  intimacyIndex: 5,
  tacit: 10,
  triggeredEncounters: [],
  usedEncounterIndices: [],
  isDead: false
}];
const lyrChoices = forceTriggerSpecificScenario(lyrOwner.ch.id, "lyr_s5_2");
report.checks.lyrChoices = lyrChoices;
const fallbackChoice = lyrChoices.find(c => c.text.includes("並肩應對"));
if (!fallbackChoice) throw new Error("Missing gate-free positive fallback choice on lyr_s5_2");
if (fallbackChoice.disabled) throw new Error("Fallback choice should NOT be disabled");

// Test 9: Non-companion openEventModal raw fallback (relaxed to 上乘) + 進階 tier test
player = makeBasePlayer(JSON.parse(JSON.stringify(screenshotSkills)));
document.getElementById("ev-modal-choices").children = [];
openEventModal("江湖風波", "荒廟血戰", "敵酋殺招已至", [
  { text: "以絕世武功硬抗敵酋殺招", onSelect() {} },
  { text: "以一招《招式名》開道突圍", reqSkillTier: "進階", reqSkillCategory: "招式", onSelect() {} },
  { text: "尋隙退避", onSelect() {} }
]);
const nonCompLow = document.getElementById("ev-modal-choices").children.map(b => ({ text: b.innerHTML, disabled: !!b.disabled }));
report.checks.nonCompLow = nonCompLow;
const nonCompLowUpper = nonCompLow.find(c => c.text.includes("以絕世武功硬抗敵酋殺招"));
const nonCompLowAdv = nonCompLow.find(c => c.text.includes("以一招看家絕學開道突圍"));
if (!nonCompLowUpper || !nonCompLowUpper.disabled || !nonCompLowUpper.text.includes("🔒 【需上乘以上招式】")) {
  throw new Error("Non-companion low check failed: " + JSON.stringify(nonCompLow));
}
if (!nonCompLowAdv || !nonCompLowAdv.disabled || !nonCompLowAdv.text.includes("🔒 【需進階以上招式】")) {
  throw new Error("進階 locked check failed: " + JSON.stringify(nonCompLow));
}

player = makeBasePlayer([
  { id: "hxq", name: "虎嘯拳", tier: "進階", type: "招式", weapon: "拳掌", exp: 10 },
  { id: "wrgy", name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", exp: 10 }
]);
document.getElementById("ev-modal-choices").children = [];
openEventModal("江湖風波", "荒廟血戰", "敵酋殺招已至", [
  { text: "以絕世武功硬抗敵酋殺招", onSelect() {} },
  { text: "以一招《招式名》開道突圍", reqSkillTier: "進階", reqSkillCategory: "招式", onSelect() {} },
  { text: "尋隙退避", onSelect() {} }
]);
const nonCompHigh = document.getElementById("ev-modal-choices").children.map(b => ({ text: b.innerHTML, disabled: !!b.disabled }));
report.checks.nonCompHigh = nonCompHigh;
const nonCompHighUpper = nonCompHigh.find(c => c.text.includes("硬抗敵酋殺招"));
const nonCompHighAdv = nonCompHigh.find(c => c.text.includes("開道突圍"));
if (!nonCompHighUpper || nonCompHighUpper.disabled || !nonCompHighUpper.text.includes("萬刃歸元")) {
  throw new Error("Non-companion high check failed: " + JSON.stringify(nonCompHigh));
}
if (!nonCompHighAdv || nonCompHighAdv.disabled || !/✨ 【(進階|曠世)招式 · 《/.test(nonCompHighAdv.text)) {
  throw new Error("進階 unlocked check failed: " + JSON.stringify(nonCompHigh));
}

// Test 10: Final BOSS 鎮派三系檢定 (wushendian_final 5A1)
const wsBattle = DB.MAJOR_BATTLES.find(b => b.id === "wushendian_final");
if (!wsBattle) throw new Error("wushendian_final not found");
let bossZeroCleanPasses = 0;
for (let trial = 0; trial < 10; trial++) {
  player = makeBasePlayer([{ id: "hxq", name: "虎嘯拳", tier: "進階", type: "招式", weapon: "拳掌", exp: 10 }]);
  player.stats.wu = 300;
  player.lightInjuries = 0;
  player.heavyInjuries = 0;
  player.injuries = 0;
  playBattleStage(wsBattle, 5, "5A1");
  const descTxt = document.getElementById("ev-modal-desc").textContent || document.getElementById("ev-modal-desc").innerHTML || "";
  if (trial === 0) {
    report.checks.bossZeroWarningShown = descTxt.includes("最終 BOSS 三系底氣評估");
  }
  const allBossBtns = document.getElementById("ev-modal-choices").children.map(b => ({ html: b.innerHTML, disabled: !!b.disabled }));
  const bossBtn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("正面擊碎司馬玄冥魔身"));
  if (!bossBtn || bossBtn.disabled) throw new Error("Final BOSS option check failed: " + JSON.stringify(allBossBtns));
  bossBtn.click();
  if (!player.isDead && (player.heavyInjuries || 0) === 0) {
    bossZeroCleanPasses++;
  }
}
if (bossZeroCleanPasses > 0) {
  throw new Error("Expected 0 clean passes without 2 鎮派 pillars, got " + bossZeroCleanPasses);
}

// Now test with 2 鎮派 pillars (招式 + 內功) + high wu: should allow clean / light-injury pass
player = makeBasePlayer([
  { id: "wrgy", name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", exp: 10 },
  { id: "wxtj", name: "無相太虛訣", tier: "曠世", type: "內功", weapon: "心法", exp: 10 }
]);
player.stats.wu = 350;
player.lightInjuries = 0;
player.heavyInjuries = 0;
player.injuries = 0;
playBattleStage(wsBattle, 5, "5A1");
const bossBtn2 = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("正面擊碎司馬玄冥魔身"));
// 正常武力決戰在 effWu < reqWu×1.2（reqWu 含 ±33% 浮動）時，roll < 1/3 會重傷；此處固定擲骰 0.99 走「輕傷／無傷」分支以避免隨機誤判
const _origRandTwoPillars = Math.random;
Math.random = () => 0.99;
bossBtn2.click();
Math.random = _origRandTwoPillars;
report.checks.bossTwoPillarsOutcome = {
  isDead: !!player.isDead,
  heavyInjuries: player.heavyInjuries || 0,
  lightInjuries: player.lightInjuries || 0
};
if (player.isDead || (player.heavyInjuries || 0) > 0) {
  throw new Error("With 2 鎮派 pillars + wu=350, expected clean/light-injury pass, got: " + JSON.stringify(report.checks.bossTwoPillarsOutcome));
}

// Check 1: 白骨流沙 & 瀚海雪毒 do NOT get inappropriate combat choices injected
player = makeBasePlayer([
  { id: "bhwd", name: "八荒無敵", tier: "曠世", type: "招式", weapon: "拳掌", exp: 10 },
  { id: "txb", name: "九天玄虛踏星步", tier: "曠世", type: "輕功", weapon: "身法", exp: 10 }
]);
player.bonds = [
  { charId: "sha_gulan", name: "阿史那嵐", intimacyIndex: 2, tacit: 2, relationTag: "" },
  { charId: "tuoba_jun", name: "赫連錚", intimacyIndex: 4, tacit: 3, relationTag: "" }
];
const agulan = DB.CHARACTERS.find(c => c.id === "sha_gulan");
const agulanStorm = (agulan.encounters || []).find(e => (e.title || "").includes("白骨流沙"));
triggerCompanionEncounter(agulan, agulanStorm, false);
const agulanChoices = document.getElementById("ev-modal-choices").children.map(b => b.innerHTML);
if (agulanChoices.some(h => h.includes("一舉定局") || h.includes("肝膽俱裂"))) {
  throw new Error("白骨流沙 unexpectedly received combat choices: " + JSON.stringify(agulanChoices));
}

const helian = DB.CHARACTERS.find(c => c.id === "tuoba_jun");
const helianPoison = (helian.encounters || []).find(e => (e.title || "").includes("瀚海雪毒"));
triggerCompanionEncounter(helian, helianPoison, false);
const helianChoices = document.getElementById("ev-modal-choices").children.map(b => b.innerHTML);
if (helianChoices.some(h => h.includes("封死敵人退路") || h.includes("肝膽俱裂"))) {
  throw new Error("瀚海雪毒 unexpectedly received combat choices: " + JSON.stringify(helianChoices));
}
report.checks.noInappropriateInjection = true;

// Check 2: Cangzhou stages hide ±33%, [基準, [中位數, spoilers, and schedule dynamic echo age
player = makeBasePlayer([
  { id: "bhwd", name: "八荒無敵", tier: "曠世", type: "招式", weapon: "拳掌", exp: 10 },
  { id: "wxtj", name: "無相太虛訣", tier: "曠世", type: "內功", weapon: "心法", exp: 10 }
]);
player.age = 34;
player.stats.wu = 200;
const czBattle = (DB.MAJOR_BATTLES || []).find(b => b.id === "cangzhou_tieshidu");
playBattleStage(czBattle, 3, "3");
const czDesc3 = document.getElementById("ev-modal-desc").textContent || document.getElementById("ev-modal-desc").innerHTML || "";
const czChoices3 = document.getElementById("ev-modal-choices").children.map(b => b.innerHTML).join(" | ");
if (/±33%|\[基準|\[中位數|宿命之嘆|可改變命運之關鍵分水嶺/.test(czDesc3 + czChoices3)) {
  throw new Error("Found hidden formula or spoiler in Cangzhou stage 3: " + czDesc3);
}
const saveXmBtn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("救小醫女溫小滿"));
saveXmBtn.click();
report.checks.cangzhouEchoScheduled = {
  outcome: player.cangzhouOutcome,
  targetAge: player.cangzhouEchoTargetAge,
  targetMonth: player.cangzhouEchoTargetMonth
};
if (!player.cangzhouEchoTargetAge || player.cangzhouEchoTargetAge < 37 || player.cangzhouEchoTargetAge > 42) {
  throw new Error("Invalid cangzhouEchoTargetAge: " + JSON.stringify(report.checks.cangzhouEchoScheduled));
}

// Check 3: Rename check (皇甫無極 / 八荒無敵)
const dbStr = JSON.stringify(DB);
if (!dbStr.includes("八荒無敵") || dbStr.includes("八荒無敵武") || !dbStr.includes("皇甫無極") || dbStr.includes("武無敵")) {
  throw new Error("Rename verification failed");
}
report.checks.renameVerified = true;

window.__TEST_REPORT = JSON.stringify(report);
})();
window.__TEST_REPORT;
'''

marker = "window.addEventListener(\"DOMContentLoaded\""
idx = main_js.rfind(marker)
if idx == -1:
    raise RuntimeError("Could not find DOMContentLoaded marker in main_js")
main_js_injected = main_js[:idx] + "\n" + test_tail
test_code = jxa_driver + "\n" + data_js + "\n" + patches_js + "\n" + main_js_injected

proc = subprocess.run(
    ["/usr/bin/osascript", "-l", "JavaScript", "-"],
    input=test_code,
    text=True,
    capture_output=True,
    check=False,
)
print("EXIT:", proc.returncode)
if proc.stdout:
    print("STDOUT:", proc.stdout.strip())
if proc.stderr:
    print("STDERR:", proc.stderr.strip())
if proc.returncode != 0:
    raise SystemExit(proc.returncode)
