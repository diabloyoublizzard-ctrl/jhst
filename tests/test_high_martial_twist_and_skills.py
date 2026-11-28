import json
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
    insertAdjacentHTML(pos, html) { this._innerHTML = (this._innerHTML || "") + String(html || ""); },
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
      if (this.onclick) this.onclick();
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
function setTimeout() { return 1; }
function clearTimeout() {}
function setInterval() { return 1; }
function clearInterval() {}
function Audio() { return { play() { return Promise.resolve(); }, pause() {}, addEventListener() {} }; }
'''

test_tail = r'''
function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

function logTexts() {
  return (player.logs || []).map(l => (typeof l === "string" ? l : (l && l.text ? String(l.text) : String(l || ""))));
}

function preloadDom() {
  [
    "log-container", "modal-start", "modal-event", "modal-epilogue",
    "btn-leave-sect", "btn-fake-death", "btn-open-epilogue",
    "ev-modal-title", "ev-modal-tag", "ev-modal-desc", "ev-modal-choices",
    "tab-btn-immortal", "tab-immortal", "m-nav-immortal",
    "ui-life-stage-title", "ui-lifespan-hint", "ui-name", "ui-gender-badge",
    "ui-title-badge", "ui-age", "ui-ganzhi", "ui-sect", "ui-realm",
    "ui-body-tier", "stat-wu", "stat-de", "stat-ming", "stat-cai", "stat-qing",
    "ui-badges", "skills-count-badge", "artifacts-list", "skills-list", "bonds-list"
  ].forEach(id => document.getElementById(id));
}

function initTestPlayer(overrides = {}) {
  preloadDom();
  candidateDraft = {
    name: overrides.name || "林清羽",
    gender: overrides.gender || "女",
    title: overrides.title || "初入江湖",
    heroId: null,
    sect: overrides.sect || "無門無派",
    location: "蜀中青城",
    originText: "生於巴蜀青城山下。",
    stats: Object.assign({ wu: 35, de: 50, ming: 40, cai: 50, qing: 50 }, overrides.stats || {}),
    innateTalents: [],
    badges: overrides.badges || [],
    presetSkills: overrides.presetSkills || ["太祖長拳"]
  };
  startNewLife();
  Object.assign(player, overrides);
  document.getElementById("modal-event").classList.remove("show");
  player.logs = [];
  return player;
}

function openSpecificDilemmaById(dilemmaId) {
  const pool = getUnifiedJianghuDilemmasPool();
  const target = pool.find(e => e && e.id === dilemmaId);
  assert(!!target, "Missing dilemma with id: " + dilemmaId);
  player.usedEvents = new Set();
  pool.forEach(ev => {
    if (ev && ev.id !== dilemmaId) {
      player.usedEvents.add(`dilemma_${ev.id || ev.title}`);
    }
  });
  document.getElementById("ev-modal-choices").innerHTML = "";
  const ok = triggerDynamicDilemma(true);
  assert(ok === true, "Expected dilemma to trigger: " + dilemmaId);
  return document.getElementById("ev-modal-choices").children;
}

const report = {};

// ============================================================
// 1. Low vs High Martial Surprise Twist + ✨ marker + heroic exclusion
// ============================================================
{
  // 1a. Low martial player on 北冥黑風口 -> no ✨ on 鑽入石縫, original penalty applies
  initTestPlayer({
    age: 26,
    month: 4,
    stats: { wu: 35, de: 40, ming: 40, cai: 50, qing: 40 },
    skills: [{ name: "太祖長拳", tier: "一般", type: "招式", weapon: "拳掌", pendingEnlightenment: false }]
  });
  const lowBtns = openSpecificDilemmaById("major_steppe_cavalry_raid");
  const lowCrawlBtn = lowBtns.find(b => (b.innerHTML || "").includes("鑽入石縫"));
  assert(!!lowCrawlBtn, "1a: expected 鑽入石縫 choice for low martial player");
  assert(!(lowCrawlBtn.innerHTML || "").includes("✨"), "1a: low martial player must NOT see ✨ on 鑽入石縫");
  const prevCaiLow = player.stats.cai;
  const prevMingLow = player.stats.ming;
  lowCrawlBtn.click();
  assert(player.stats.cai < prevCaiLow && player.stats.ming < prevMingLow, "1a: low martial 鑽入石縫 should lose cai & ming");
  assert(!logTexts().some(l => l.includes("扮豬吃老虎")), "1a: low martial must not trigger surprise twist");

  // 1b. High martial player (wu=95 + 萬刃歸元 + 武林盟主) -> sees ✨ and triggers surprise twist!
  initTestPlayer({
    age: 35,
    month: 4,
    title: "武林盟主",
    isAllianceLeader: true,
    badges: ["武林盟主"],
    stats: { wu: 95, de: 80, ming: 85, cai: 50, qing: 80 },
    skills: [{ name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", pendingEnlightenment: false }]
  });
  const highBtns = openSpecificDilemmaById("major_steppe_cavalry_raid");
  const highCrawlBtn = highBtns.find(b => (b.innerHTML || "").includes("鑽入石縫"));
  assert(!!highCrawlBtn, "1b: expected 鑽入石縫 choice for high martial player");
  assert((highCrawlBtn.innerHTML || "").includes("✨"), "1b: high martial 鑽入石縫 must include ✨ hint");
  const prevCaiHigh = player.stats.cai;
  const prevMingHigh = player.stats.ming;
  highCrawlBtn.click();
  assert(player.stats.cai > prevCaiHigh && player.stats.ming > prevMingHigh, "1b: high martial surprise twist must increase cai & ming");
  assert(logTexts().some(l => l.includes("😎【扮豬吃老虎 · 渠底拾寶戲群盜】")), "1b: expected 扮豬吃老虎 log");

  // 1c. High martial lightInjury dilemma (北冥古墓 · 硬抗毒霧) -> twist prevents lightInjury
  initTestPlayer({
    age: 35,
    month: 4,
    stats: { wu: 95, de: 60, ming: 60, cai: 50, qing: 50 },
    skills: [{ name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", pendingEnlightenment: false }]
  });
  const tombBtns = openSpecificDilemmaById("dilemma_youzhou_tomb");
  const holdBreathBtn = tombBtns.find(b => (b.innerHTML || "").includes("硬抗毒霧"));
  assert(!!holdBreathBtn && (holdBreathBtn.innerHTML || "").includes("✨"), "1c: expected 硬抗毒霧 with ✨ for high martial");
  holdBreathBtn.click();
  assert(player.lightInjuries === 0, "1c: high martial twist on 硬抗毒霧 must avoid light injury");
  assert(logTexts().some(l => l.includes("😎【藏拙低俯 · 窺見先秦壁刻】")), "1c: expected 藏拙低俯 log");

  // 1d. Heroic rescue option (護民硬扛) must NEVER get ✨ or twist even at high martial
  initTestPlayer({
    age: 35,
    month: 4,
    stats: { wu: 100, de: 80, ming: 80, cai: 50, qing: 80 },
    skills: [{ name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", pendingEnlightenment: false }]
  });
  const puppetBtns = openSpecificDilemmaById("major_mojia_puppet_riot");
  const heroicBtn = puppetBtns.find(b => (b.innerHTML || "").includes("護民硬扛"));
  assert(!!heroicBtn, "1d: expected 護民硬扛 choice");
  assert(!(heroicBtn.innerHTML || "").includes("✨"), "1d: heroic rescue 護民硬扛 must NOT have ✨ twist");
  heroicBtn.click();
  assert(!logTexts().some(l => l.includes("😎【")), "1d: heroic rescue must preserve original outcome");
  report.surpriseTwist = true;
}

// ============================================================
// 2. Eliminate duplicate same-skill buttons in crisis modals
// ============================================================
{
  // 2a. Player has only ONE high-tier attack skill (萬刃歸元) -> 北冥黑風口 shows only 🔥 曠世版, never duplicate
  initTestPlayer({
    age: 35,
    month: 4,
    stats: { wu: 95, de: 80, ming: 85, cai: 50, qing: 130 },
    skills: [
      { name: "太祖長拳", tier: "一般", type: "招式", weapon: "拳掌", pendingEnlightenment: false },
      { name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", pendingEnlightenment: false }
    ]
  });
  const stepBtns = openSpecificDilemmaById("major_steppe_cavalry_raid");
  const htmls = stepBtns.map(b => b.innerHTML || "");
  const wrgyButtons = htmls.filter(h => h.includes("《萬刃歸元》"));
  assert(wrgyButtons.length === 1, "2a: expected 《萬刃歸元》 only once, got " + wrgyButtons.length + ": " + JSON.stringify(htmls));
  assert(wrgyButtons[0].includes("🔥 【曠世招式 · 《萬刃歸元》】"), "2a: expected 🔥 【曠世招式 · 《萬刃歸元》】, got " + wrgyButtons[0]);

  // 2b. Player has 羅剎修羅槍 (上乘) + 萬刃歸元 (曠世) -> 2 buttons pick different skills
  initTestPlayer({
    age: 35,
    month: 4,
    stats: { wu: 95, de: 80, ming: 85, cai: 50, qing: 60 },
    skills: [
      { name: "羅剎修羅槍", tier: "上乘", type: "招式", weapon: "槍棍", pendingEnlightenment: false },
      { name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", pendingEnlightenment: false }
    ]
  });
  const stepBtns2 = openSpecificDilemmaById("major_steppe_cavalry_raid");
  const htmls2 = stepBtns2.map(b => b.innerHTML || "");
  assert(htmls2.some(h => h.includes("🔥 【曠世招式 · 《萬刃歸元》】")), "2b: expected 鎮派/曠世 button with 《萬刃歸元》");
  assert(htmls2.some(h => h.includes("✨ 【上乘招式 · 《羅剎修羅槍》】")), "2b: expected 上乘 button with different skill 《羅剎修羅槍》: " + JSON.stringify(htmls2));
  report.noDupCrisisSkills = true;
}

// ============================================================
// 3. Non-BOSS rotates all mastered skills vs BOSS locks highest tier
// ============================================================
{
  const mixedSkills = [
    { name: "太祖長拳", tier: "一般", type: "招式", weapon: "拳掌", pendingEnlightenment: false },
    { name: "虎嘯拳", tier: "進階", type: "招式", weapon: "拳掌", pendingEnlightenment: false },
    { name: "羅剎修羅槍", tier: "上乘", type: "招式", weapon: "槍棍", pendingEnlightenment: false },
    { name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", pendingEnlightenment: false }
  ];
  initTestPlayer({
    age: 40,
    month: 5,
    stats: { wu: 120, de: 90, ming: 90, cai: 80, qing: 80 },
    skills: mixedSkills
  });

  // 3a. Normal mode rotates across all tiers including 一般 (太祖長拳)
  const pickedNormal = new Set();
  for (let i = 0; i < 40; i++) {
    const sk = pickLearnedSkill("招式", "", true);
    if (sk && sk.name) pickedNormal.add(sk.name);
  }
  assert(pickedNormal.size >= 3 && pickedNormal.has("太祖長拳"), "3a: expected all tiers including 太祖長拳 in normal mode, got " + JSON.stringify(Array.from(pickedNormal)));

  // 3b. BOSS mode (preferHighest: true & openEventModal with isBossBattle: true) locks 100% to 萬刃歸元
  const pickedBossDirect = new Set();
  for (let i = 0; i < 20; i++) {
    const sk = pickLearnedSkill("招式", "", true, { preferHighest: true });
    if (sk && sk.name) pickedBossDirect.add(sk.name);
  }
  assert(pickedBossDirect.size === 1 && pickedBossDirect.has("萬刃歸元"), "3b: preferHighest must lock to 萬刃歸元, got " + JSON.stringify(Array.from(pickedBossDirect)));

  for (let i = 0; i < 20; i++) {
    document.getElementById("ev-modal-choices").innerHTML = "";
    openEventModal(
      "最終決戰 · 絕巔之戰",
      "⚔️ 武林浩劫（第 5/5 幕）",
      "魔主殺招將至！",
      [{ text: "【正面強破 · 力戰魔頭】施展平生絕學正面硬撼！", reqStat: { wu: 60 }, onSelect() {} }],
      { isBossBattle: true }
    );
    const bossHtml = document.getElementById("ev-modal-choices").children[0].innerHTML || "";
    assert(bossHtml.includes("《萬刃歸元》") && !bossHtml.includes("《太祖長拳》") && !bossHtml.includes("《虎嘯拳》"), "3b: BOSS modal must use highest tier 《萬刃歸元》, got: " + bossHtml);
  }

  // 3c. Actual playBattleStage BOSS stage (wushendian_final 5A1) never uses 一般/進階 skills
  const wsBattle = DB.MAJOR_BATTLES.find(b => b.id === "wushendian_final");
  assert(!!wsBattle, "3c: expected wushendian_final battle");
  player.skills = mixedSkills.concat([{ name: "無相太虛訣", tier: "曠世", type: "內功", weapon: "心法", pendingEnlightenment: false }]);
  player.stats.wu = 350;
  for (let i = 0; i < 10; i++) {
    playBattleStage(wsBattle, 5, "5A1");
    const stageHtmls = document.getElementById("ev-modal-choices").children.map(b => b.innerHTML || "");
    stageHtmls.forEach(h => {
      assert(!h.includes("《太祖長拳》") && !h.includes("《虎嘯拳》") && !h.includes("《羅剎修羅槍》"), "3c: BOSS stage used non-highest skill: " + h);
    });
  }
  report.bossVsNormalSkills = true;
}

report.ok = true;
window.__TEST_REPORT = JSON.stringify(report);
'''

marker = 'window.addEventListener("DOMContentLoaded"'
assert marker in main_js, "Expected DOMContentLoaded marker in main_js"
injected_main_js = main_js.replace(marker, test_tail + "\n    " + marker, 1)
full_js = "\n".join([jxa_driver, data_js, patches_js, injected_main_js, "window.__TEST_REPORT;"])
proc = subprocess.run(
    ["/usr/bin/osascript", "-l", "JavaScript", "-"],
    input=full_js,
    text=True,
    capture_output=True,
)
print("EXIT:", proc.returncode)
if proc.stdout:
    print("STDOUT:", proc.stdout.strip())
if proc.stderr:
    print("STDERR:", proc.stderr.strip())
assert proc.returncode == 0, f"JXA test failed: {proc.stderr}"
data = json.loads(proc.stdout.strip())
assert data.get("ok") is True
print("TWIST PARSED:", json.dumps(data, ensure_ascii=False))
