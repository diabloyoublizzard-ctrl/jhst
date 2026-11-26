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
    get innerHTML() { return this._innerHTML + (this.children || []).map(c => c.innerHTML || c.textContent || "").join("\n"); },
    set innerHTML(v) {
      this._innerHTML = String(v);
      if (this._innerHTML === "") this.children = [];
    },
    textContent: "",
    disabled: false,
    children: [],
    dataset: {},
    classList: {
      _set: new Set(),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      toggle(c, f) { if (f) this._set.add(c); else this._set.delete(c); },
      contains(c) { return this._set.has(c); }
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    insertAdjacentHTML(pos, html) {
      this._innerHTML += String(html || "");
    },
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
function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

function makeBattlePlayer() {
  return {
    name: "沈驚鴻",
    gender: "男",
    title: "名宿",
    age: 43,
    month: 6,
    ganzhiIndex: 7,
    maxLifespan: 79,
    sect: "無門無派",
    tier: "凡胎俗骨",
    bodyTierIndex: 1, // 銅皮鐵骨
    stats: { wu: 126, de: 199, ming: 143, qing: 136, cai: 29 },
    innateTalents: [{ name: "書香世家" }],
    qi: 100,
    badges: [],
    titles: [],
    titleHistory: [],
    equippedWeapon: { name: "鳴鴻赤血刀", tier: 4 },
    ownedWeapons: [{ name: "鳴鴻赤血刀", tier: 4 }],
    sealedWeapons: [],
    collectedManuals: [],
    weaponHistoryFlags: new Set(),
    artifacts: [],
    comprehendedClassics: [],
    skills: [],
    bonds: [],
    children: [],
    disciples: [],
    mounts: [],
    karmicSeeds: [],
    injuryHistory: [],
    worldHistory: [],
    usedEvents: new Set(),
    usedEpochEvents: new Set(),
    triggeredBattles: new Set(),
    triggeredAllianceLeaderEvents: new Set(),
    fakedDeath: false,
    inImmortalPhase: false,
    isImmortalUnlocked: false,
    isAllianceLeader: false,
    isDead: false,
    injuries: 0,
    lightInjuries: 0,
    heavyInjuries: 0,
    logs: []
  };
}

function resetUi() {
  document.getElementById("log-container").innerHTML = "";
  document.getElementById("ev-modal-choices").innerHTML = "";
  document.getElementById("ev-modal-title").textContent = "";
  document.getElementById("ev-modal-tag").textContent = "";
  document.getElementById("ev-modal-desc").textContent = "";
}

const origRandom = Math.random;
const report = {};

const hsBattle = DB.MAJOR_BATTLES.find(b => b.id === "huashan_dahui");
const ygBattle = DB.MAJOR_BATTLES.find(b => b.id === "hengshan_crisis" || b.id === "battle_hengshan");
const wsBattle = DB.MAJOR_BATTLES.find(b => b.id === "wushendian_final");
assert(!!hsBattle && !!ygBattle && !!wsBattle, "Expected major battles in DB");

// Case 1: Reproduce 43歲 沈驚鴻 build from 202611230748.txt
player = makeBattlePlayer();
player.skills = [
  { id: "wxtj", name: "無相太虛訣", tier: "曠世", type: "內功", weapon: "心法", masteryStage: "已參悟" },
  { id: "qjq", name: "七絕劍氣", tier: "上乘", type: "招式", weapon: "劍法", masteryStage: "已參悟" },
  { id: "syq", name: "碎岳槍法", tier: "上乘", type: "招式", weapon: "槍棍", masteryStage: "已參悟" },
  { id: "jfb", name: "疾風步", tier: "進階", type: "輕功", weapon: "身法", masteryStage: "臻至圓滿" }
];
const feiyan = { id: "ye_feiyan", name: "葉緋煙", intimacyIndex: 4, isDead: false };
player.bonds = [feiyan];
const s1Eval = evaluateBossReadiness(hsBattle, feiyan);
assert(s1Eval.martialScore === 5.5, "Case 1 failed martialScore: " + s1Eval.martialScore);
assert(s1Eval.extraScore === 1.5, "Case 1 failed extraScore: " + s1Eval.extraScore);
assert(s1Eval.totalScore === 7.0, "Case 1 failed totalScore: " + s1Eval.totalScore);
assert(s1Eval.targetScore === 4.5 && s1Eval.minMartialScore === 3.5, "Case 1 failed target/min: " + JSON.stringify(s1Eval));
assert(s1Eval.isReady === true && s1Eval.effectiveGap === 0, "Case 1 expected isReady=true");

// Drive stage 4 fatal choice of huashan_dahui across rolls: should NEVER enter 底氣不繼 / 鎮派未足
for (let i = 0; i < 15; i++) {
  resetUi();
  player.isDead = false;
  player.heavyInjuries = 0;
  player.lightInjuries = 1;
  player.injuries = 1;
  playBattleStage(hsBattle, 4);
  if (i === 0) {
    const descTxt = document.getElementById("ev-modal-desc").textContent;
    assert(descTxt.includes("底氣十足") && descTxt.includes("無相太虛訣"), "Case 1 pre-battle UI missing readiness summary: " + descTxt);
  }
  const btn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("司馬玄冥") || b.innerHTML.includes("擋") || b.innerHTML.includes("迎戰"));
  assert(!!btn, "Missing huashan stage 4 fatal button");
  Math.random = () => 0.05; // would have fallen into 25% death in old 1/3 check!
  btn.click();
  Math.random = origRandom;
  const logHtml = document.getElementById("log-container").innerHTML;
  assert(!logHtml.includes("底氣不繼") && !logHtml.includes("底氣未足") && !logHtml.includes("鎮派未足"), "Case 1 unexpectedly entered low-readiness penalty branch: " + logHtml);
}
report.case1_shenJinghongPassed = true;

// Case 2: Age/Stage thresholds & battle_wushendian bugfix (stages 1-4 NOT treated as boss fight)
player = makeBattlePlayer();
player.bodyTierIndex = 0;
player.equippedWeapon = null;
player.bonds = [];
player.skills = [{ id: "qjq", name: "七絕劍氣", tier: "上乘", type: "招式", weapon: "劍法", masteryStage: "已參悟" }];
const earlyEv = evaluateBossReadiness(ygBattle, null);
const midEv = evaluateBossReadiness(hsBattle, null);
const lateEv = evaluateBossReadiness(wsBattle, null);
assert(earlyEv.targetScore === 3.5 && earlyEv.minMartialScore === 2.5, "Early threshold mismatch");
assert(midEv.targetScore === 4.5 && midEv.minMartialScore === 3.5, "Mid threshold mismatch");
assert(lateEv.targetScore === 5.0 && lateEv.minMartialScore === 4.0, "Late threshold mismatch");

const wsAliasBattle = Object.assign({}, wsBattle, { id: "battle_wushendian" });
[1, 2, 3, 4].forEach(st => {
  resetUi();
  playBattleStage(wsAliasBattle, st);
  const desc = document.getElementById("ev-modal-desc").textContent;
  assert(!desc.includes("最終 BOSS 三系底氣評估"), "Bugfix failed: battle_wushendian stage " + st + " triggered final boss warning");
});
resetUi();
playBattleStage(wsAliasBattle, 5, "5A1");
assert(document.getElementById("ev-modal-desc").textContent.includes("最終 BOSS 三系底氣評估"), "battle_wushendian stage 5 should show boss warning");
report.case2_thresholdsAndBugfix = true;

// Case 3: 2 鎮派 without extras in 戮神殿 -> isReady === true (not stricter than old rule)
player = makeBattlePlayer();
player.bodyTierIndex = 0;
player.equippedWeapon = null;
player.bonds = [];
player.skills = [
  { id: "zp1", name: "純陽無極功", tier: "鎮派", type: "內功", weapon: "心法", masteryStage: "已參悟" },
  { id: "zp2", name: "太極劍法", tier: "鎮派", type: "招式", weapon: "劍法", masteryStage: "已參悟" }
];
const twoZpEv = evaluateBossReadiness(wsBattle, null);
assert(twoZpEv.martialScore === 5.0 && twoZpEv.extraScore === 0 && twoZpEv.isReady === true, "Case 3 failed: " + JSON.stringify(twoZpEv));
report.case3_twoZhenpaiReady = true;

// Case 4: Extra bonus capped at 1.5 + martialScore floor enforcement (no 一般/進階-only free pass)
player = makeBattlePlayer();
player.bodyTierIndex = 2; // +0.8
player.equippedWeapon = { name: "干將莫邪雙劍", tier: 5 }; // +0.6
const companion = { id: "b1", name: "沈寒舟", intimacyIndex: 5, relationTag: "義結金蘭", isDead: false }; // +0.8
player.bonds = [companion];
player.skills = [
  { id: "j1", name: "虎嘯拳", tier: "進階", type: "招式", weapon: "拳掌", masteryStage: "臻至圓滿" }, // 1.0
  { id: "j2", name: "吐納功", tier: "一般", type: "內功", weapon: "心法", masteryStage: "臻至圓滿" }, // 0.5
  { id: "j3", name: "健行步", tier: "一般", type: "輕功", weapon: "身法", masteryStage: "臻至圓滿" }  // 0.5 -> total 2.0 < minMartialScore (2.5 / 3.5 / 4.0)
];
const floorEarlyEv = evaluateBossReadiness(ygBattle, companion);
assert(floorEarlyEv.extraScore === 1.5, "Case 4 failed: extraScore cap expected 1.5, got " + floorEarlyEv.extraScore);
assert(floorEarlyEv.martialScore === 2.0 && floorEarlyEv.martialGap === 0.5 && !floorEarlyEv.isReady, "Case 4 failed: expected !isReady due to minMartialScore");
// Verify that surviving when martialGap > 0 ALWAYS pays heavy injury (never downgrades to light injury)
let heavyPaidOnFloorSurvive = 0;
for (let k = 0; k < 20; k++) {
  resetUi();
  player.isDead = false;
  player.stats.wu = 300;
  player.lightInjuries = 0;
  player.heavyInjuries = 0;
  player.injuries = 0;
  playBattleStage(wsBattle, 5, "5A1");
  const btn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("正面擊碎司馬玄冥魔身"));
  Math.random = () => 0.1; // ensures survive roll (0.1 < 0.22+) AND heavy/light branch roll (0.1 < 0.40 if not guarded)
  btn.click();
  Math.random = origRandom;
  assert(!player.isDead && (player.heavyInjuries || 0) >= 1, "Case 4 failed: martialGap>0 allowed pass without heavy injury: " + JSON.stringify({ isDead: player.isDead, heavy: player.heavyInjuries, light: player.lightInjuries }));
  heavyPaidOnFloorSurvive++;
}
assert(heavyPaidOnFloorSurvive === 20, "Expected 20 heavy injuries");
report.case4_extraCapAndMartialFloor = true;

// Case 5: Smooth survival curve: mild deficit (gap=1.0) wins much more often than severe deficit (gap=4.5)
function runTrials(skills, gapLabel) {
  let wins = 0;
  let heavyTotal = 0;
  for (let t = 0; t < 40; t++) {
    resetUi();
    player = makeBattlePlayer();
    player.bodyTierIndex = 0;
    player.equippedWeapon = null;
    player.bonds = [];
    player.stats.wu = 260;
    player.skills = skills;
    playBattleStage(wsBattle, 5, "5A1");
    const btn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("正面擊碎司馬玄冥魔身"));
    // Fix random deterministically across grid [0.02..0.98]
    const fixed = (t + 0.5) / 40;
    const seq = [fixed, 0.9, 0.5, 0.5, 0.5]; // stage survive roll, then non-downgrade / heavy roll
    let idx = 0;
    // Wait: applyFloatingReqToChoice already ran; btn.click calls rollFloatingPlayerWu (1 random) then surviveProb roll!
    // Use 0.5 for float mult so effWu ~ 260 >= reqWu*1.2, then fixed for survive roll!
    Math.random = () => {
      const i = idx++;
      if (i === 0) return 0.5;
      if (i === 1) return fixed;
      return 0.8;
    };
    btn.click();
    Math.random = origRandom;
    if (!player.isDead) {
      wins++;
      heavyTotal += (player.heavyInjuries || 0);
    }
  }
  return { gapLabel, wins, heavyTotal };
}
const mildRes = runTrials([
  { id: "zp1", name: "純陽無極功", tier: "鎮派", type: "內功", weapon: "心法", masteryStage: "已參悟" }, // 2.5
  { id: "sc1", name: "七絕劍氣", tier: "上乘", type: "招式", weapon: "劍法", masteryStage: "已參悟" }   // 1.5 -> total 4.0 vs 5.0 (gap 1.0, martialGap 0)
], "mild");
const severeRes = runTrials([
  { id: "jj1", name: "虎嘯拳", tier: "進階", type: "招式", weapon: "拳掌", masteryStage: "已參悟" }     // 0.5 -> total 0.5 vs 5.0 (gap 4.5)
], "severe");
assert(mildRes.wins > severeRes.wins && mildRes.wins >= 30 && severeRes.wins >= 10 && severeRes.wins <= 22, "Case 5 curve mismatch: mild=" + JSON.stringify(mildRes) + " severe=" + JSON.stringify(severeRes));
report.case5_smoothCurve = { mild: mildRes, severe: severeRes };

window.__TEST_REPORT = JSON.stringify({ ok: true, report });
})();
window.__TEST_REPORT;
'''

marker = 'window.addEventListener("DOMContentLoaded"'
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
