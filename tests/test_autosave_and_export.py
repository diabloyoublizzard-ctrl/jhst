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
    tagName: (tag || "DIV").toUpperCase(),
    className: "",
    style: {},
    _innerHTML: "",
    get innerHTML() {
      const childHtml = (this.children || []).map(c => c.innerHTML || c.textContent || "").join("\n");
      return this._innerHTML ? (childHtml ? this._innerHTML + "\n" + childHtml : this._innerHTML) : childHtml;
    },
    set innerHTML(v) {
      this._innerHTML = String(v || "");
      if (this._innerHTML === "") this.children = [];
    },
    textContent: "",
    value: "",
    disabled: false,
    children: [],
    dataset: {},
    attrs: {},
    classList: {
      _set: new Set(),
      add(...cs) { cs.forEach(c => this._set.add(c)); },
      remove(...cs) { cs.forEach(c => this._set.delete(c)); },
      toggle(c, f) {
        if (f === undefined) {
          if (this._set.has(c)) this._set.delete(c);
          else this._set.add(c);
        } else if (f) {
          this._set.add(c);
        } else {
          this._set.delete(c);
        }
      },
      contains(c) { return this._set.has(c); }
    },
    appendChild(child) {
      if (child && child.tagName === "FRAGMENT" && Array.isArray(child.children)) {
        child.children.forEach(c => this.children.push(c));
        child.children = [];
        return child;
      }
      this.children.push(child);
      return child;
    },
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return this.attrs[k] || ""; },
    _listeners: {},
    addEventListener(evt, fn) {
      this._listeners[evt] = this._listeners[evt] || [];
      this._listeners[evt].push(fn);
    },
    removeEventListener() {},
    querySelectorAll() { return []; },
    querySelector(sel) {
      if (sel === "button") {
        const btn = makeEl("", "button");
        this.appendChild(btn);
        return btn;
      }
      return makeEl("", sel || "div");
    },
    scrollIntoView() {},
    click() {
      if (this.disabled) return;
      (this._listeners.click || []).forEach(fn => fn());
    }
  };
  return el;
}

const document = {
  body: makeEl("body", "body"),
  visibilityState: "visible",
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl(id);
    return elements[id];
  },
  createElement(tag) { return makeEl("", tag); },
  createDocumentFragment() { return makeEl("", "FRAGMENT"); },
  querySelector(sel) { return makeEl("", sel); },
  querySelectorAll() { return []; },
  addEventListener() {}
};

const _store = {};
const localStorage = {
  getItem(k) { return Object.prototype.hasOwnProperty.call(_store, k) ? _store[k] : null; },
  setItem(k, v) { _store[k] = String(v); },
  removeItem(k) { delete _store[k]; }
};

var window = globalThis;
window.document = document;
window.localStorage = localStorage;
window.PENDING_PATCHES_QUEUE = window.PENDING_PATCHES_QUEUE || [];
window.LOADED_PATCHES = window.LOADED_PATCHES || [];
window.addGameData = function(p) { window.PENDING_PATCHES_QUEUE.push(p); };
window.addEventListener = function() {};
window.alert = function() {};
window.confirm = function() { return true; };
var setTimeout = function() { return 1; };
var clearTimeout = function() {};
var setInterval = function() { return 1; };
var clearInterval = function() {};
var lastDownloaded = null;
var Blob = function(parts, opts) { this.parts = parts; this.opts = opts; };
var URL = {
  createObjectURL(b) { lastDownloaded = b; return "blob:test-txt"; },
  revokeObjectURL() {}
};
'''

test_tail = r'''
function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

const report = {};

// Preload DOM elements that startNewLife / updateAllUI / resume touch
["log-container", "modal-start", "modal-event", "modal-epilogue", "tab-btn-immortal", "tab-immortal",
 "m-nav-immortal", "btn-leave-sect", "btn-fake-death", "btn-open-epilogue", "ui-life-stage-title",
 "ui-lifespan-hint", "ui-name", "ui-gender-badge", "ui-title-badge", "ui-age", "ui-ganzhi",
 "ui-sect", "ui-realm", "ui-body-tier", "stat-wu", "stat-de", "stat-ming", "stat-cai", "stat-qing",
 "ui-badges", "skills-count-badge", "artifacts-list", "skills-list", "resume-save-banner",
 "ep-paper-card", "ep-vertical-seal", "ep-rarity-line", "ep-hero-name", "ep-role-badge",
 "ep-cause-badge", "ep-open-quote", "ep-summary", "ep-cause-main", "ep-cause-pre", "ep-stat-strip",
 "ep-unique-grid", "ep-beast-header", "ep-beast-list", "ep-beast-story", "ep-focus-row",
 "ep-title-chain", "ep-skills-label", "ep-skills-list", "ep-tomb-header", "ep-bonds-inline",
 "ep-tombstones", "ep-seals", "ep-poetic-footer", "ep-seed-reward"].forEach(id => document.getElementById(id));

// 1. Set & state round-trip
candidateDraft = {
  name: "林清風",
  gender: "男",
  title: "初入江湖",
  heroId: null,
  sect: "青城派",
  location: "蜀中青城",
  originText: "生於巴蜀青城山下書香門第。",
  stats: { wu: 24, de: 30, ming: 12, cai: 18, qing: 22 },
  innateTalents: [],
  badges: ["劍道胚子"],
  presetSkills: ["青城劍法"]
};
startNewLife();

player.age = 128;
player.month = 6;
player.maxLifespan = 320;
player.isImmortalUnlocked = true;
player.inImmortalPhase = true;
player.immortalStage = 2;
player.qi = 9500;
player.bodyTierIndex = 2;
player.rootTierIndex = 3;
player.stats = { wu: 145, de: 120, ming: 98, cai: 66, qing: 135 };
player.skills = [
  { id: "sk1", name: "青城劍法", tier: "上乘", type: "招式", weapon: "劍法", exp: 10 },
  { id: "sk2", name: "太虛吐納術", tier: "鎮派", type: "內功", weapon: "心法", exp: 10 }
];
player.bonds = [
  { id: "ling_yan", name: "葉緋煙", intimacyIndex: 5, tacit: 4, relationTag: "神仙眷侶", isImmortal: true, age: 125, maxLifespan: 600, isDead: false }
];
player.usedEvents.add("ev_test_alpha");
player.usedImmortalEvents = new Set(["imm_vein_01", "imm_dao_02"]);
player.triggeredBattles.add("hengshan_crisis");
player.weaponHistoryFlags.add("wp_flag_1");
addLog("【奇遇】於青城後山覓得古劍譜殘頁，<span>潛心參詳</span>獲益匪淺。", "milestone");
addLog("【破境】靈氣貫通紫府，踏入金丹大道！", "immortal-log");

const savedOk = saveAutoGame({ force: true });
assert(savedOk === true, "Expected saveAutoGame({force:true}) to succeed");
assert(!!localStorage.getItem("JHST_AUTOSAVE_V1"), "Expected JHST_AUTOSAVE_V1 in localStorage");
const savedLogCount = player.logs.length;
assert(savedLogCount >= 3, "Expected >=3 saved logs, got " + savedLogCount);
report.case1_roundTripSaved = true;

// 2. Modal-open protection: mutate age while modal-event is open, verify saveAutoGame refuses overwrite
document.getElementById("modal-event").classList.add("show");
player.age = 999;
const blockedSave = saveAutoGame({ force: true });
assert(blockedSave === false, "Expected saveAutoGame to refuse overwrite while modal-event is open");
const summaryDuringModal = getAutoSaveSummary();
assert(summaryDuringModal && summaryDuringModal.age === 128, "Expected stored age to remain 128, got " + (summaryDuringModal && summaryDuringModal.age));
document.getElementById("modal-event").classList.remove("show");
report.case2_modalGuard = true;

// 3. Full reload & resume
renderResumeBanner();
assert(document.getElementById("resume-save-banner").style.display === "block", "Expected resume banner visible when save exists");
assert(document.getElementById("resume-save-banner").innerHTML.includes("林清風"), "Expected player name on resume banner");

player = null;
document.getElementById("log-container").innerHTML = "";
const resumed = resumeFromAutoSave();
assert(resumed === true, "Expected resumeFromAutoSave() to return true");
assert(player && player.name === "林清風" && player.age === 128, "Expected player age 128 restored");
assert(player.stats.wu === 145 && player.stats.qing === 135, "Expected stats restored");
assert(player.skills.length === 2 && player.bonds.length === 1, "Expected skills & bonds restored");
assert(player.usedEvents instanceof Set && player.usedEvents.has("ev_test_alpha"), "Expected usedEvents restored as real Set");
assert(player.usedImmortalEvents instanceof Set && player.usedImmortalEvents.has("imm_vein_01"), "Expected usedImmortalEvents restored as real Set");
assert(player.triggeredBattles instanceof Set && player.triggeredBattles.has("hengshan_crisis"), "Expected triggeredBattles restored as real Set");
assert(player.weaponHistoryFlags instanceof Set && player.weaponHistoryFlags.has("wp_flag_1"), "Expected weaponHistoryFlags restored as real Set");
assert(player.logs.length === savedLogCount, "Expected logs count preserved without pushing visual resume notice into player.logs");
const logChildren = document.getElementById("log-container").children;
assert(logChildren.length === savedLogCount + 1, "Expected rehydrated DOM logs + 1 visual resume notice, got " + logChildren.length);
assert(!document.getElementById("tab-btn-immortal").classList.contains("hidden"), "Expected #tab-btn-immortal visible after immortal resume");
assert(document.getElementById("ui-life-stage-title").textContent.includes("洞天修真卷"), "Expected immortal stage title");
assert(isPaused === true && userManualPaused === true, "Expected resumed game to start paused");
report.case3_reloadAndResume = true;

// 4. Dead-run resume without double daoSeeds
const seedsBeforeDeath = MetaState.daoSeeds;
triggerDeathOrAscension("壽終正寢，含笑坐化。");
const seedsAfterDeath = MetaState.daoSeeds;
assert(seedsAfterDeath > seedsBeforeDeath, "Expected daoSeeds to increase on death");
assert(player.isDead === true, "Expected player.isDead true");

player = null;
document.getElementById("log-container").innerHTML = "";
const resumedDead = resumeFromAutoSave();
assert(resumedDead === true, "Expected dead-run resume to succeed");
assert(MetaState.daoSeeds === seedsAfterDeath, "Expected daoSeeds NOT to double-increment on dead-run resume");
assert(document.getElementById("btn-open-epilogue").style.display === "inline-block", "Expected #btn-open-epilogue shown on dead-run resume");
assert(document.getElementById("ep-hero-name").textContent === "林清風", "Expected epilogue DOM rendered on dead-run resume");
report.case4_deadResumeNoDoubleSeeds = true;

// 5. MetaState persistence
MetaState.daoSeeds = 188;
MetaState.talents.martialRoot.level = 3;
MetaState.talents.martialRoot.cost = getTalentUpgradeCost(3);
MetaState.unlockedBaixiao.add("絕學：青城劍法");
MetaState.unlockedAchievements.add("ending_萬古流芳");
assert(saveMetaState() === true, "Expected saveMetaState() true");

MetaState.daoSeeds = 0;
MetaState.talents.martialRoot.level = 0;
MetaState.talents.martialRoot.cost = 10;
MetaState.unlockedBaixiao.clear();
MetaState.unlockedAchievements.clear();
assert(loadMetaState() === true, "Expected loadMetaState() true");
assert(MetaState.daoSeeds === 188, "Expected daoSeeds=188 restored, got " + MetaState.daoSeeds);
assert(MetaState.talents.martialRoot.level === 3 && MetaState.talents.martialRoot.cost === getTalentUpgradeCost(3), "Expected martialRoot talent & cost restored");
assert(MetaState.unlockedBaixiao instanceof Set && MetaState.unlockedBaixiao.has("絕學：青城劍法"), "Expected unlockedBaixiao restored as Set");
assert(MetaState.unlockedAchievements instanceof Set && MetaState.unlockedAchievements.has("ending_萬古流芳"), "Expected unlockedAchievements restored as Set");
report.case5_metaPersistence = true;

// 6. .txt export
const txtObj = exportFullLifeLogTxt();
assert(txtObj && /^\d{8}_\d{6}_江湖仙途_林清風_128歲\.txt$/.test(txtObj.filename), "Unexpected export filename: " + (txtObj && txtObj.filename));
assert(txtObj.content.includes("俠名：林清風"), "Missing 俠名 in txt export");
assert(txtObj.content.includes("五維：武力 145"), "Missing 五維 in txt export");
assert(txtObj.content.includes("修真："), "Missing 修真 in txt export");
assert(txtObj.content.includes("武學（2 門）"), "Missing 武學 in txt export");
assert(txtObj.content.includes("羈絆（1 人）：葉緋煙"), "Missing 羈絆 in txt export");
assert(txtObj.content.includes("於青城後山覓得古劍譜殘頁，潛心參詳獲益匪淺。"), "Missing sanitized log line in txt export");
assert(txtObj.content.includes("靈氣貫通紫府，踏入金丹大道！"), "Missing second log line in txt export");
assert(!txtObj.content.includes("<span>"), "Raw HTML tag leaked into txt export");
assert(lastDownloaded && lastDownloaded.parts && lastDownloaded.parts[0] === txtObj.content, "Expected Blob download payload");
report.case6_txtExport = { filename: txtObj.filename, lineCount: txtObj.lineCount };

// 7. Clear save
assert(clearAutoSave() === true, "Expected clearAutoSave() true");
assert(getAutoSaveSummary() === null, "Expected getAutoSaveSummary() === null after clear");
renderResumeBanner();
assert(document.getElementById("resume-save-banner").style.display === "none", "Expected resume banner hidden after clear");
report.case7_clearSave = true;

window.__TEST_REPORT = JSON.stringify({ ok: true, report });
'''

marker = 'window.addEventListener("DOMContentLoaded"'
idx = main_js.rfind(marker)
if idx == -1:
    raise RuntimeError("Could not find DOMContentLoaded marker in main_js")

test_code = jxa_driver + "\n" + data_js + "\n" + patches_js + "\n" + main_js[:idx] + "\n" + test_tail + "\n})();\nwindow.__TEST_REPORT;"

proc = subprocess.run(
    ["/usr/bin/osascript", "-l", "JavaScript", "-"],
    input=test_code,
    text=True,
    capture_output=True,
    check=False,
)
print("EXIT:", proc.returncode)
if proc.stdout.strip():
    print("STDOUT:", proc.stdout.strip())
if proc.stderr.strip():
    print("STDERR:", proc.stderr.strip())
if proc.returncode != 0:
    raise SystemExit(proc.returncode)
