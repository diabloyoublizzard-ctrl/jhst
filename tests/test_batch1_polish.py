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

const _origRand = Math.random;
function withFixedRand(val, fn) {
  Math.random = () => val;
  try {
    return fn();
  } finally {
    Math.random = _origRand;
  }
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
    title: "初入江湖",
    heroId: null,
    sect: overrides.sect || "青城派",
    location: "蜀中青城",
    originText: "生於巴蜀青城山下。",
    stats: Object.assign({ wu: 80, de: 80, ming: 75, cai: 60, qing: 120 }, overrides.stats || {}),
    innateTalents: [],
    badges: [],
    presetSkills: ["青城劍法"]
  };
  startNewLife();
  Object.assign(player, overrides);
  document.getElementById("modal-event").classList.remove("show");
  player.logs = [];
  return player;
}

const report = {};

// ============================================================
// 1. runAutoFateImmortalCultivation & attemptBreakthrough
// ============================================================
{
  // 1a. Non-lethal fail must log to main chronicle and NOT consume taixu_armor
  initTestPlayer({
    age: 140,
    month: 2,
    maxLifespan: 240,
    isImmortalUnlocked: true,
    inImmortalPhase: true,
    immortalStage: 0,
    qi: IMMORTAL_REALMS[0].maxQi,
    artifacts: [{ id: "taixu_armor", name: "太虛神甲", type: "上古防具" }]
  });
  const actedFail = withFixedRand(0.9999, () => runAutoFateImmortalCultivation());
  assert(actedFail === true, "1a: expected runAutoFateImmortalCultivation to attempt breakthrough");
  assert(player.artifacts.some(a => a.id === "taixu_armor"), "1a: non-lethal breakthrough fail must NOT consume taixu_armor");
  assert(logTexts().some(l => l.includes("破境") || l.includes("閉關沖關") || l.includes("衝擊")), "1a: breakthrough failure must log to main chronicle");

  // 1b. Lethal fail (maxLifespan - 15 <= age AND lifeMargin <= 12 so auto-fate risks it) MUST consume taixu_armor and keep alive
  player.age = 230;
  player.maxLifespan = 240; // lifeMargin = 10 <= 12, maxLifespan - 15 = 225 <= 230
  player.qi = IMMORTAL_REALMS[0].maxQi;
  player.logs = [];
  const actedLethal = withFixedRand(0.9999, () => runAutoFateImmortalCultivation());
  assert(actedLethal === true, "1b: expected desperate auto breakthrough at lifeMargin <= 12");
  assert(!player.artifacts.some(a => a.id === "taixu_armor"), "1b: lethal breakthrough tribulation MUST consume taixu_armor");
  assert(player.isDead === false, "1b: taixu_armor should save player from lethal breakthrough tribulation");
  assert(logTexts().some(l => l.includes("太虛神甲")), "1b: consuming taixu_armor should log protection message");

  // 1c. Breakthrough success advances stage and logs to main chronicle
  player.age = 140;
  player.maxLifespan = 300;
  player.immortalStage = 0;
  player.qi = IMMORTAL_REALMS[0].maxQi;
  player.logs = [];
  const actedSuccess = withFixedRand(0.0, () => runAutoFateImmortalCultivation());
  assert(actedSuccess === true && player.immortalStage === 1, "1c: breakthrough success should advance immortalStage");
  assert(logTexts().some(l => l.includes(IMMORTAL_REALMS[1].name) || l.includes("破境")), "1c: breakthrough success must log to main chronicle");

  // 1d. Body temper & root cleanse gating (skip if unsafe margin or rate < 0.65; run when >= 0.65 and safe)
  initTestPlayer({
    age: 140,
    maxLifespan: 160, // margin 20 < 25 -> unsafe for body/root in immortal phase
    isImmortalUnlocked: true,
    inImmortalPhase: true,
    immortalStage: 2, // maxQi = 6500
    bodyTierIndex: 0,
    rootTierIndex: 0,
    qi: 2000, // >= BODY_TIERS[1].cost (1800) and < maxQi (6500)
    stats: { wu: 500, de: 500, ming: 500, cai: 500, qing: 500 }
  });
  const unsafeBodySkip = runAutoFateImmortalCultivation();
  assert(unsafeBodySkip === false && player.bodyTierIndex === 0, "1d: should skip body temper when immortal lifeMargin < 25");

  // Low rate check (< 0.65)
  player.maxLifespan = 400;
  player.immortalStage = 7; // maxQi = 2000000
  player.bodyTierIndex = 4; // next rate: 0.30 + 0.14 + 0.06 = 0.50 < 0.65
  player.rootTierIndex = 4; // next rate: 0.26 + 0.14 + 0.06 = 0.46 < 0.65
  player.stats = { wu: 1, de: 1, ming: 1, cai: 1, qing: 1 };
  player.qi = 500000; // >= 400000 / 480000, < 2000000
  assert(getBodyTemperRate() < 0.65 && getRootCleanseRate() < 0.65, "1d: expected both rates < 0.65 at tier 4");
  assert(runAutoFateImmortalCultivation() === false, "1d: should skip body/root when rates < 0.65");

  // Safe & high rate -> triggers body temper then root cleanse
  player.immortalStage = 2; // maxQi = 6500
  player.bodyTierIndex = 0;
  player.rootTierIndex = 0;
  player.stats = { wu: 300, de: 300, ming: 300, cai: 300, qing: 300 };
  const bodyCost = BODY_TIERS[1].cost;
  const rootCost = ROOT_TIERS[1].cost;
  player.qi = bodyCost + rootCost; // 4400 < 6500
  assert(getBodyTemperRate() >= 0.65, "1d: expected high-stat test body temper rate >= 0.65");
  const didBody = withFixedRand(0.0, () => runAutoFateImmortalCultivation());
  assert(didBody === true && player.bodyTierIndex === 1, "1d: expected auto body temper to execute once");

  player.bodyTierIndex = BODY_TIERS.length - 1; // max out body tier so next action picks root cleanse
  player.qi = rootCost; // 2600 < 6500
  assert(getRootCleanseRate() >= 0.65, "1d: expected high-stat test root cleanse rate >= 0.65");
  const didRoot = withFixedRand(0.0, () => runAutoFateImmortalCultivation());
  assert(didRoot === true && player.rootTierIndex === 1, "1d: expected auto root cleanse to execute once");
  report.autoFateImmortal = true;
}

// ============================================================
// 2. Gender-aware partner & sect narratives
// ============================================================
{
  const maleChar = DB.CHARACTERS.find(c => c.gender === "男");
  assert(!!maleChar, "2: expected a male character in DB.CHARACTERS");
  initTestPlayer({ gender: "女", age: 30, sect: "峨眉派" });
  const maleBond = {
    id: maleChar.id,
    name: maleChar.name,
    gender: "男",
    intimacyIndex: 5,
    tacit: 4,
    relationTag: "神仙眷侶",
    isDead: false,
    age: 32,
    maxLifespan: 100
  };
  player.bonds = [maleBond];

  assert(Array.isArray(SPOUSE_WARMTH_EVENTS_MALE) && SPOUSE_WARMTH_EVENTS_MALE.length > 0, "2: SPOUSE_WARMTH_EVENTS_MALE must exist");
  assert(Array.isArray(SPOUSE_WARMTH_EVENTS_FEMALE) && SPOUSE_WARMTH_EVENTS_FEMALE.length > 0, "2: SPOUSE_WARMTH_EVENTS_FEMALE must exist");
  const maleWarmthStr = JSON.stringify(SPOUSE_WARMTH_EVENTS_MALE);
  assert(!/珠玉首飾|縫補|眉眼彎彎/.test(maleWarmthStr), "2: male warmth events must not contain feminine tropes");

  // Reunion scenario for male partner across many draws
  for (let i = 0; i < 8; i++) {
    const sc = buildSwornOrCloseReunionScenario(maleChar, maleBond);
    const scStr = JSON.stringify(sc);
    assert(!/珠玉首飾|縫補|眉眼彎彎/.test(scStr), "2: male reunion scenario must not contain feminine tropes");
  }

  // Hangout scenario with male companion
  player.usedHighQingHangouts = [];
  const hangSc = buildHighQingHangoutScenarios(maleChar, maleBond);
  assert(!/咱們姊妹/.test(JSON.stringify(hangSc)), "2: male hangout must not use 咱們姊妹");

  // Female player sect maze event (sect_ev_4_maze) -> 長姊風範
  const registeredSect = Object.values(DB.SECTS)[0].name;
  initTestPlayer({ gender: "女", age: 22, sect: registeredSect });
  player.usedSectEvents = new Set();
  SECT_INTERNAL_EVENTS_POOL.forEach(ev => {
    if (ev && ev.id !== "sect_ev_4_maze") player.usedSectEvents.add(ev.id);
  });
  const triggeredMaze = triggerSectInternalEvent();
  assert(triggeredMaze === true, "2: expected triggerSectInternalEvent to open sect_ev_4_maze");
  const mazeBtns = document.getElementById("ev-modal-choices").children;
  assert(mazeBtns.length === 3, "2: expected 3 sect_ev_4_maze modal buttons");
  const elderBtn = mazeBtns.find(b => (b.innerHTML || "").includes("請出陣圖"));
  assert(!!elderBtn, "2: expected 請出陣圖 choice in sect_ev_4_maze");
  withFixedRand(0.0, () => elderBtn.click());
  const mazeLogs = logTexts().join("\n");
  assert(mazeLogs.includes("長姊風範"), "2: female player sect_ev_4_maze log should include 長姊風範");
  assert(!mazeLogs.includes("長兄風範"), "2: female player sect_ev_4_maze log must not include 長兄風範");
  report.genderNarratives = true;
}

// ============================================================
// 3. Immortal mount one-time awakening log
// ============================================================
{
  initTestPlayer({
    age: 130,
    maxLifespan: 500,
    isImmortalUnlocked: true,
    inImmortalPhase: true,
    mounts: [{ id: "m_test", name: "踏雪烏騅", title: "龍駒", immortalized: false }]
  });
  withFixedRand(0.9999, () => tickImmortalYear());
  const awakenLogs1 = logTexts().filter(l => l.includes("靈獸蛻凡 · 護道長生"));
  assert(awakenLogs1.length === 1, "3: first tickImmortalYear must emit 靈獸蛻凡 · 護道長生 once");
  assert(player.mounts[0].immortalized === true, "3: mount must be marked immortalized");

  player.logs = [];
  withFixedRand(0.9999, () => tickImmortalYear());
  const awakenLogs2 = logTexts().filter(l => l.includes("靈獸蛻凡 · 護道長生"));
  assert(awakenLogs2.length === 0, "3: second tickImmortalYear must NOT emit 靈獸蛻凡 · 護道長生 again");
  report.immortalMount = true;
}

// ============================================================
// 4. Farewell rift cancels promptBondAscension & logs 重逢已逝 · 舊約成空
// ============================================================
{
  const targetChar = DB.CHARACTERS.find(c => !c.isCustom) || DB.CHARACTERS[0];
  initTestPlayer({ age: 55, month: 3, maxLifespan: 120 });
  const riftBond = {
    id: targetChar.id,
    name: targetChar.name,
    gender: targetChar.gender,
    intimacyIndex: 4,
    tacit: 3,
    relationTag: null,
    isDead: false,
    isImmortal: false,
    farewellTriggered: true,
    pendingConfessionMonths: 1,
    intimacyAtFarewell: 4,
    hadRiftAfterFarewell: true,
    age: 55,
    maxLifespan: 90
  };
  player.bonds = [riftBond];
  withFixedRand(0.9999, () => tickMortalMonth());
  assert(logTexts().some(l => l.includes("重逢已逝 · 舊約成空")), "4: farewell rift must log 重逢已逝 · 舊約成空");
  assert(riftBond.isImmortal !== true, "4: bond with farewell rift must NOT ascend");
  report.farewellRiftCheck = true;
}

// ============================================================
// 5. Auto grave visit enforces 1/year cooldown (lastAutoGraveVisitAge)
// ============================================================
{
  initTestPlayer({ age: 48, month: 3, maxLifespan: 90, isImmortalUnlocked: true, inImmortalPhase: false });
  const deadBond = {
    id: "dead_companion_1",
    name: "蘇晴",
    gender: "女",
    intimacyIndex: 3,
    tacit: 2,
    relationTag: "紅顏知己",
    isDead: true,
    deathAge: 42,
    age: 42,
    maxLifespan: 80,
    restingPlace: "青城後山"
  };
  player.bonds = [deadBond];
  let seed = 12345;
  Math.random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  try {
    for (let i = 0; i < 1500 && !(deadBond.visitedGraveCount >= 1); i++) {
      player.age = 48;
      player.month = 3;
      player.isDead = false;
      document.getElementById("modal-event").classList.remove("show");
      tickMortalMonth();
    }
    assert(player.lastAutoGraveVisitAge === 48, "5: player.lastAutoGraveVisitAge should be set on grave visit");
    assert(deadBond.lastAutoGraveVisitAge === 48, "5: deadBond.lastAutoGraveVisitAge should be set on grave visit");
    assert(deadBond.visitedGraveCount === 1, "5: expected deadBond.visitedGraveCount === 1");
    assert(logTexts().some(l => l.includes("故人長思 · 墓前祭奠")), "5: expected 故人長思 · 墓前祭奠 log");

    for (let i = 0; i < 400; i++) {
      player.age = 48;
      player.month = 4;
      player.isDead = false;
      document.getElementById("modal-event").classList.remove("show");
      tickMortalMonth();
    }
    assert(deadBond.visitedGraveCount === 1, "5: same age must NOT trigger auto grave visit again");
  } finally {
    Math.random = _origRand;
  }
  report.graveCooldown = true;
}

// ============================================================
// 6. buildSwornOrCloseReunionScenario shared deduplication
// ============================================================
{
  const targetChar = DB.CHARACTERS.find(c => !c.isCustom) || DB.CHARACTERS[0];
  initTestPlayer({ age: 40, stats: { wu: 80, de: 80, ming: 75, cai: 60, qing: 220 } });
  const bond = {
    id: targetChar.id,
    name: targetChar.name,
    gender: targetChar.gender,
    intimacyIndex: 4,
    tacit: 3,
    relationTag: "紅顏知己",
    isDead: false,
    age: 38,
    maxLifespan: 95,
    usedReunionTitles: []
  };
  player.bonds = [bond];
  player.usedHighQingHangouts = [];

  const seenTitles = new Set();
  for (let i = 0; i < 6; i++) {
    const sc = buildSwornOrCloseReunionScenario(targetChar, bond);
    assert(!!sc && !!sc.title, "6: reunion scenario must return a title");
    assert(!seenTitles.has(sc.title), "6: duplicate reunion title within pool: " + sc.title);
    seenTitles.add(sc.title);
    assert((bond.usedReunionTitles.length + player.usedHighQingHangouts.length) === i + 1, "6: total dedup count mismatch at draw " + i);
  }
  // Pre-seed all high-qing hangout IDs -> reunion should not return any hq_* scene
  const allHqIds = buildHighQingHangoutScenarios(targetChar, bond).map(s => s.id);
  player.usedHighQingHangouts = [...allHqIds];
  bond.usedReunionTitles = [];
  for (let i = 0; i < 6; i++) {
    const sc = buildSwornOrCloseReunionScenario(targetChar, bond);
    assert(!(sc.id && sc.id.startsWith("hq_")), "6: pre-used hangout should not appear in reunion: " + sc.id);
  }
  report.reunionDedup = true;
}

// ============================================================
// 7. Text & UI polish
// ============================================================
{
  // 7a. data.js / DB has zero simplified '击'
  assert(!JSON.stringify(DB).includes("击"), "7a: DB must contain zero simplified 击");

  // 7b. Battle armor block emits only 1 armor log (no double armor log)
  initTestPlayer({
    age: 35,
    maxLifespan: 90,
    stats: { wu: 10, de: 50, ming: 50, cai: 50, qing: 50 },
    artifacts: [{ id: "taixu_armor", name: "太虛神甲", type: "上古防具" }]
  });
  const syntheticBattle = {
    id: "test_battle_armor",
    title: "測試決戰",
    stages: [
      {
        subtitle: "第一幕",
        desc: "強敵壓境",
        choices: [
          {
            text: "正面硬撼（需武力≥999）",
            reqStat: { wu: 999 },
            isFatal: true,
            allowFatalChallenge: true
          }
        ]
      }
    ]
  };
  playBattleStage(syntheticBattle, 1);
  const bBtns = document.getElementById("ev-modal-choices").children;
  assert(bBtns.length === 1, "7b: expected 1 synthetic battle choice button");
  withFixedRand(0.0, () => bBtns[0].click());
  const armorLogs = logTexts().filter(l => l.includes("🛡️"));
  assert(armorLogs.length === 1, "7b: battle taixu_armor save must emit exactly 1 🛡️ log, got " + armorLogs.length);

  // 7c. Dilemma lightInjury with explicit 輕傷+1 in result must NOT duplicate 【擦傷留下輕傷+1】
  initTestPlayer({ age: 30, maxLifespan: 90 });
  const fakeDilemma = {
    id: "test_light_inj_dup",
    title: "試煉暗箭",
    desc: "暗箭襲來。",
    choices: [
      {
        text: "側身硬擋",
        lightInjury: 1,
        result: "雖避開要害仍被擦傷臂膀（輕傷+1）。",
        stats: { wu: 1 }
      }
    ]
  };
  DB.EVENTS = DB.EVENTS || {};
  DB.EVENTS.dynamic_dilemmas = DB.EVENTS.dynamic_dilemmas || [];
  DB.EVENTS.dynamic_dilemmas.push(fakeDilemma);
  // Mark every other dilemma as used so triggerDynamicDilemma picks fakeDilemma
  const allDil = getUnifiedJianghuDilemmasPool();
  player.usedEvents = new Set();
  allDil.forEach(ev => {
    if (ev.id !== "test_light_inj_dup") player.usedEvents.add(`dilemma_${ev.id || ev.title}`);
  });
  const dilOk = triggerDynamicDilemma(true);
  assert(dilOk === true, "7c: expected fake dilemma to open");
  const dilBtn = document.getElementById("ev-modal-choices").children.find(b => (b.innerHTML || "").includes("側身硬擋"));
  assert(!!dilBtn, "7c: expected 側身硬擋 choice");
  dilBtn.click();
  const injLog = logTexts().find(l => l.includes("試煉暗箭"));
  assert(!!injLog && injLog.includes("輕傷+1") && !injLog.includes("擦傷留下輕傷+"), "7c: dilemma log must not duplicate light injury suffix: " + injLog);
  DB.EVENTS.dynamic_dilemmas.pop();

  // 7d. triggerSelfMartialEncounter instant mastery emits only 1 mastery log (no 當場頓悟 · 因緣際會)
  initTestPlayer({ age: 30, maxLifespan: 90, stats: { wu: 300, de: 100, ming: 100, cai: 100, qing: 100 } });
  const smOk = triggerSelfMartialEncounter();
  assert(smOk === true, "7d: expected triggerSelfMartialEncounter to open");
  const smBtns = document.getElementById("ev-modal-choices").children;
  assert(smBtns.length > 0, "7d: expected self martial encounter choices");
  withFixedRand(0.5, () => smBtns[0].click());
  const masteryLogs = logTexts().filter(l => l.includes("📘"));
  assert(masteryLogs.length === 1, "7d: instant mastery must emit exactly 1 📘 log, got " + masteryLogs.length);
  assert(!logTexts().some(l => l.includes("當場頓悟 · 因緣際會")), "7d: must not emit duplicate 當場頓悟 · 因緣際會 log");

  // 7e. Ancient weapon box uses 🗝️ instead of bare 匣
  initTestPlayer({ age: 30, maxLifespan: 90, stats: { wu: 200, de: 200, ming: 200, cai: 200, qing: 200 } });
  const wpOk = withFixedRand(0.0, () => triggerWeaponEncounter());
  assert(wpOk === true, "7e: expected triggerWeaponEncounter to open");
  const wpBtns = document.getElementById("ev-modal-choices").children;
  assert(wpBtns.length > 0, "7e: expected weapon encounter choices");
  // roll = 0.5 falls into [1/3, 2/3) -> ancient sealed box branch
  withFixedRand(0.5, () => wpBtns[0].click());
  const sealedLog = logTexts().find(l => l.includes("古煞未消 · 收入古兵匣收藏"));
  assert(!!sealedLog && sealedLog.includes("🗝️【古煞未消 · 收入古兵匣收藏】") && !sealedLog.includes("匣【古煞未消"), "7e: sealed weapon log must use 🗝️");

  // 7f. Hangout & active mount logs have zero nested brackets 【...【...】...】
  const anyChar = DB.CHARACTERS.find(c => !c.isCustom) || DB.CHARACTERS[0];
  initTestPlayer({
    age: 35,
    maxLifespan: 90,
    stats: { wu: 100, de: 100, ming: 100, cai: 100, qing: 220 },
    bonds: [{ id: anyChar.id, name: anyChar.name, gender: anyChar.gender, intimacyIndex: 5, tacit: 4, relationTag: "紅顏知己", isDead: false, age: 35, maxLifespan: 95 }],
    mounts: [{ id: "m_chk", name: "雪裡白", title: "名駒" }]
  });
  triggerHighQingCompanionHangout(anyChar.id);
  const hBtns = document.getElementById("ev-modal-choices").children;
  if (hBtns.length > 0) withFixedRand(0.0, () => hBtns[0].click());
  withFixedRand(0.0, () => triggerActiveMountScenario());
  const mBtns = document.getElementById("ev-modal-choices").children;
  if (mBtns.length > 0) withFixedRand(0.0, () => mBtns[0].click());
  logTexts().forEach(l => {
    assert(!/【[^】]*【[^】]*】/.test(l), "7f: log contains nested 【...【...】】 brackets: " + l);
  });

  // 7g. #btn-leave-sect hidden when player dies + updateTopUI()
  initTestPlayer({ age: 25, sect: "武當派", isDead: false, inImmortalPhase: false });
  updateTopUI();
  assert(document.getElementById("btn-leave-sect").style.display !== "none", "7g: leave-sect button should be visible while alive in sect");
  player.isDead = true;
  updateTopUI();
  assert(document.getElementById("btn-leave-sect").style.display === "none", "7g: leave-sect button must hide when player.isDead = true");
  report.textAndUiPolish = true;
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
print("BATCH1 PARSED:", json.dumps(data, ensure_ascii=False))
