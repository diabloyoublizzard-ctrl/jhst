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
function withSeededRand(seedInit, fn) {
  let s = seedInit >>> 0;
  Math.random = () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
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
    sect: overrides.sect || "無門無派",
    location: "蜀中青城",
    originText: "生於巴蜀青城山下。",
    stats: Object.assign({ wu: 40, de: 60, ming: 40, cai: 60, qing: 120 }, overrides.stats || {}),
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
// 1. Seasonal / month filtering across event pools
// ============================================================
{
  initTestPlayer({ age: 30, month: 7, inImmortalPhase: false });

  // 1a. Specific festival & seasonal checks
  assert(isEventSeasonallyValid("除夕夜家裡置辦年貨", 12) === true, "1a: 除夕 valid in month 12");
  assert(isEventSeasonallyValid("除夕夜家裡置辦年貨", 7) === false, "1a: 除夕 invalid in month 7");
  assert(isEventSeasonallyValid("江南水鄉端午龍舟競渡", 5) === true && isEventSeasonallyValid("端午子時行經五毒嶺", 6) === true, "1a: 端午 valid in month 5-6");
  assert(isEventSeasonallyValid("江南水鄉端午龍舟競渡", 12) === false, "1a: 端午 invalid in month 12");
  assert(isEventSeasonallyValid("梅雨蝕骨 · 舊傷復發", 5) === true && isEventSeasonallyValid("江南梅雨連綿", 10) === false, "1a: 梅雨 only month 5-6");
  assert(isEventSeasonallyValid("又逢重陽佳節", 9) === true && isEventSeasonallyValid("重陽登高之際", 2) === false, "1a: 重陽 only month 9-10");
  assert(isEventSeasonallyValid("清明細雨紛紛", 4) === true && isEventSeasonallyValid("清明時節", 8) === false, "1a: 清明 only month 3-4");
  assert(isEventSeasonallyValid("春雨綿綿時節", 3) === true && isEventSeasonallyValid("春雨綿綿時節", 7) === false, "1a: 春雨 only month 2-5");
  assert(isEventSeasonallyValid("盛夏酷暑難耐", 7) === true && isEventSeasonallyValid("盛夏酷暑難耐", 1) === false, "1a: 盛夏 only month 6-8");

  // Winter takes precedence over trailing "開春後"
  const deerText = "冬日大雪封山，一隻受驚的小山鹿跑進院子，你拿乾草細心餵食並替牠包紮擦傷，開春後才放歸山林。";
  assert(isEventSeasonallyValid(deerText, 12) === true && isEventSeasonallyValid(deerText, 1) === true, "1a: winter deer valid in 12/1");
  assert(isEventSeasonallyValid(deerText, 4) === false && isEventSeasonallyValid(deerText, 6) === false, "1a: winter deer must be invalid in 4 and 6 despite 開春後");

  // 1b. False-positive safety checks (weapon/place/idiom phrases)
  const neutralPhrases = [
    "寒泉秋水劍",
    "行經天池雪山風口，你在漫天狂風暴雪中拔刃獨舞",
    "你在後山梅花樁上練習門派基礎步法",
    "雪中送炭",
    "終南山竹林 · 醉春風裡結知音",
    "溫熱的桂花釀"
  ];
  neutralPhrases.forEach(p => {
    assert(isEventSeasonallyValid(p, 7) === true, "1b: neutral phrase blocked in month 7: " + p);
    assert(isEventSeasonallyValid(p, 1) === true, "1b: neutral phrase blocked in month 1: " + p);
  });

  // 1c. pickNonRepeatingEvent across age buckets in month 7 & month 4
  const ages = [20, 35, 60, 95];
  ages.forEach(a => {
    player.age = a;
    player.month = 7;
    for (let i = 0; i < 10; i++) {
      const ev = pickNonRepeatingEvent(DB.EVENTS.mortal_adventures, "mortal");
      assert(!/除夕|端午|重陽|冬日|大雪封山|寒冬|冬至|春雨|春日/.test(ev.text || ""), "1c(m7): off-season routine picked: " + ev.text);
    }
    player.month = 4;
    for (let i = 0; i < 10; i++) {
      const ev = pickNonRepeatingEvent(DB.EVENTS.mortal_adventures, "mortal");
      assert(!/除夕|端午|重陽|冬日|大雪封山|寒冬|冬至/.test(ev.text || ""), "1c(m4): off-season routine picked: " + ev.text);
    }
  });

  // 1d. Spouse warmth & sect events in month 7 skip off-season entries
  const femaleChar = DB.CHARACTERS.find(c => c.gender === "女") || DB.CHARACTERS[0];
  initTestPlayer({
    age: 32,
    month: 7,
    stats: { wu: 60, de: 60, ming: 60, cai: 60, qing: 120 },
    bonds: [{ id: femaleChar.id, name: femaleChar.name, gender: "女", intimacyIndex: 5, tacit: 4, relationTag: "紅塵伴侶", isDead: false, age: 30, maxLifespan: 95 }]
  });
  for (let i = 0; i < 15; i++) {
    triggerQingFriendOrSpouseGift();
  }
  const warmthLogs = logTexts().join("\n");
  assert(!warmthLogs.includes("春雨") && !warmthLogs.includes("冒著風雪"), "1d: spouse warmth in month 7 must not log 春雨 or 冒著風雪");

  const registeredSect = Object.values(DB.SECTS)[0].name;
  initTestPlayer({ age: 25, month: 7, sect: registeredSect });
  player.usedSectEvents = new Set();
  for (let i = 0; i < SECT_INTERNAL_EVENTS_POOL.length; i++) {
    document.getElementById("modal-event").classList.remove("show");
    triggerSectInternalEvent();
  }
  assert(!document.getElementById("ev-modal-title").textContent.includes("寒冬閉關"), "1d: sect event in month 7 must skip 寒冬閉關");
  assert(!logTexts().some(l => l.includes("寒冬閉關")), "1d: sect logs in month 7 must not include 寒冬閉關");

  // 1e. Immortal phase bypasses seasonal check
  player.inImmortalPhase = true;
  assert(isEventSeasonallyValid("除夕夜家裡置辦年貨", 7) === true, "1e: immortal phase should bypass seasonal filter");
  report.seasonalFilter = true;
}

// ============================================================
// 2. Unique Mythic Encounters & autosave restore
// ============================================================
{
  const totalMythics = DB.MYTHIC_ENCOUNTERS.length;
  assert(totalMythics >= 4, "2: expected at least 4 mythic encounters in DB");
  initTestPlayer({ age: 30, month: 5, stats: { wu: 90, de: 90, ming: 80, cai: 60, qing: 120 } });

  const seenTitles = new Set();
  for (let i = 0; i < totalMythics; i++) {
    document.getElementById("modal-event").classList.remove("show");
    const ok = triggerMythicEncounter();
    assert(ok === true, "2: expected mythic encounter #" + (i + 1) + " to succeed");
    const title = document.getElementById("ev-modal-title").textContent;
    assert(!!title && !seenTitles.has(title), "2: duplicate mythic encounter title: " + title);
    seenTitles.add(title);
  }
  assert(player.usedMythicEncounters.size === totalMythics, "2: expected usedMythicEncounters size " + totalMythics);

  // 5th call returns false and does NOT open modal
  document.getElementById("modal-event").classList.remove("show");
  const extraCall = triggerMythicEncounter();
  assert(extraCall === false, "2: exhausted mythic encounters must return false");
  assert(!document.getElementById("modal-event").classList.contains("show"), "2: exhausted mythic encounter must not open modal");

  // Autosave round-trip preserves usedMythicEncounters
  const savedOk = saveAutoGame({ force: true });
  assert(savedOk === true, "2: expected saveAutoGame({force:true}) to succeed");
  const prevUsedSize = player.usedMythicEncounters.size;
  const raw = localStorage.getItem(AUTO_SAVE_KEY);
  assert(!!raw, "2: expected autosave payload in localStorage");
  initTestPlayer({ age: 16 });
  assert(player.usedMythicEncounters.size === 0, "2: new life starts with empty usedMythicEncounters");
  const restored = deserializeState(raw);
  player = ensurePlayerIntegrity(restored.player);
  assert(player.usedMythicEncounters instanceof Set && player.usedMythicEncounters.size === prevUsedSize, "2: restored player must keep usedMythicEncounters Set");
  assert(triggerMythicEncounter() === false, "2: restored exhausted mythic player must still return false");

  // Debug allowRepeat = true still opens modal
  assert(triggerMythicEncounter(true) === true, "2: triggerMythicEncounter(true) must allow repeat for debug button");
  assert(document.getElementById("modal-event").classList.contains("show"), "2: debug mythic must open modal");
  report.uniqueMythic = true;
}

// ============================================================
// 3. Routine event fake-enlightenment / body-upgrade / injury text alignment
// ============================================================
{
  // Verify all gainSkill / bodyUpgrade items in DB.EVENTS.mortal_adventures have fallback texts
  DB.EVENTS.mortal_adventures.forEach(ev => {
    if (ev.gainSkill) {
      assert(typeof ev.noSkillText === "string" && ev.noSkillText.length > 0, "3: missing noSkillText for " + ev.gainSkill);
    }
    if (ev.bodyUpgrade) {
      assert(typeof ev.noUpgradeText === "string" && ev.noUpgradeText.length > 0, "3: missing noUpgradeText for bodyUpgrade");
    }
  });

  const origMortalPool = DB.EVENTS.mortal_adventures;
  const fuhaiEv = origMortalPool.find(e => e.gainSkill === "覆海刀法");
  assert(!!fuhaiEv, "3: expected 覆海刀法 event in DB.EVENTS.mortal_adventures");

  try {
    // 3a. >= 8 mastered skills and skill roll misses -> outputs noSkillText, skill not added
    const eightSkills = ["羅漢拳", "太祖長拳", "兩儀劍法", "狂風刀法", "疾風步", "四象步法", "吐納功", "無極玄功"].map(n => ({
      name: n, tier: "一般", type: "招式", pendingEnlightenment: false
    }));
    initTestPlayer({
      age: 35,
      month: 3,
      isImmortalUnlocked: true,
      inImmortalPhase: false,
      bottleneckCooldown: 99,
      bonds: [],
      mounts: [],
      injuries: 0,
      lightInjuries: 0,
      heavyInjuries: 0,
      stats: { wu: 10, de: 60, ming: 40, cai: 60, qing: 60 },
      skills: eightSkills
    });
    DB.EVENTS.mortal_adventures = [fuhaiEv];
    MetaState.usedRoutineDeck = {};
    withSeededRand(101, () => {
      for (let i = 0; i < 60 && player.logs.length === 0; i++) {
        player.age = 35;
        player.month = 3;
        player.usedEvents.clear();
        MetaState.usedRoutineDeck.mortal = new Set();
        tickMortalMonth();
      }
    });
    assert(player.logs.length === 1, "3a: expected routine log to fire");
    assert(!player.skills.some(s => s.name === "覆海刀法"), "3a: 覆海刀法 should not be granted when >= 8 skills & roll misses");
    assert(logTexts()[0].includes("胸中剛猛刀意與武道底蘊愈發渾厚"), "3a: should output noSkillText: " + logTexts()[0]);
    assert(!logTexts()[0].includes("豁然領悟出剛猛無匹的刀法"), "3a: must not output misleading gain text");

    // 3b. < 5 skills and not yet known -> outputs original text and grants 覆海刀法
    initTestPlayer({
      age: 35,
      month: 3,
      isImmortalUnlocked: true,
      inImmortalPhase: false,
      bottleneckCooldown: 99,
      bonds: [],
      mounts: [],
      injuries: 0,
      lightInjuries: 0,
      heavyInjuries: 0,
      stats: { wu: 10, de: 60, ming: 40, cai: 60, qing: 60 },
      skills: [{ name: "太祖長拳", tier: "一般", type: "招式", pendingEnlightenment: false }]
    });
    MetaState.usedRoutineDeck = {};
    withSeededRand(202, () => {
      for (let i = 0; i < 60 && player.logs.length === 0; i++) {
        player.age = 35;
        player.month = 3;
        player.usedEvents.clear();
        MetaState.usedRoutineDeck.mortal = new Set();
        tickMortalMonth();
      }
    });
    assert(player.skills.some(s => s.name === "覆海刀法"), "3b: expected 覆海刀法 to be granted when < 5 skills");
    assert(logTexts()[0].includes("豁然領悟出剛猛無匹的刀法"), "3b: should output original gain text when granted");

    // 3c. Already has 覆海刀法 even with < 5 skills -> noSkillText
    player.logs = [];
    player.usedEvents.clear();
    MetaState.usedRoutineDeck.mortal = new Set();
    withSeededRand(303, () => {
      for (let i = 0; i < 60 && player.logs.length === 0; i++) {
        player.age = 35;
        player.month = 3;
        player.usedEvents.clear();
        MetaState.usedRoutineDeck.mortal = new Set();
        tickMortalMonth();
      }
    });
    assert(logTexts()[0].includes("胸中剛猛刀意與武道底蘊愈發渾厚"), "3c: already-owned skill should output noSkillText: " + logTexts()[0]);

    // 3d. lightInjury: 1 when injury roll misses -> 並未留下內傷
    const lightEv = {
      minAge: 25,
      maxAge: 50,
      text: "你在山道阻截劫匪雖大獲全勝，手臂卻遭刀鋒逼近！【留下輕傷】",
      stats: { ming: 1 },
      lightInjury: 1
    };
    DB.EVENTS.mortal_adventures = [lightEv];
    initTestPlayer({
      age: 35,
      month: 3,
      isImmortalUnlocked: true,
      inImmortalPhase: false,
      bottleneckCooldown: 99,
      bonds: [],
      mounts: [],
      injuries: 0,
      lightInjuries: 0,
      heavyInjuries: 0,
      stats: { wu: 10, de: 60, ming: 40, cai: 60, qing: 60 }
    });
    let dodged = false;
    withSeededRand(404, () => {
      for (let i = 0; i < 120; i++) {
        player.age = 35;
        player.month = 3;
        player.lightInjuries = 0;
        player.injuries = 0;
        player.logs = [];
        player.usedEvents.clear();
        MetaState.usedRoutineDeck.mortal = new Set();
        tickMortalMonth();
        if (player.logs.length > 0 && player.lightInjuries === 0) {
          assert(!logTexts()[0].includes("【留下輕傷】"), "3d: missed injury must not log 【留下輕傷】");
          assert(logTexts()[0].includes("並未留下內傷"), "3d: missed injury should log 並未留下內傷: " + logTexts()[0]);
          dodged = true;
          break;
        }
      }
    });
    assert(dodged === true, "3d: expected at least one missed-injury routine outcome");
  } finally {
    DB.EVENTS.mortal_adventures = origMortalPool;
  }
  report.routineConsistency = true;
}

report.ok = true;
window.__TEST_REPORT = JSON.stringify(report);
'''

assert "春雷炸響" not in main_js and "秋夜月華如水" not in main_js, "4: checkPendingSkillComprehension must use season-neutral phrasing"

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
print("BATCH2 PARSED:", json.dumps(data, ensure_ascii=False))
