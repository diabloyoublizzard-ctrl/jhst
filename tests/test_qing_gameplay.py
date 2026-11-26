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
function makeTestPlayer(qingVal = 120) {
  return {
    name: "柳忘機",
    gender: "男",
    title: "少俠",
    age: 35,
    month: 4,
    ganzhiIndex: 0,
    maxLifespan: 82,
    lifespanEndModalShown: false,
    sect: "無門無派",
    tier: "凡胎俗骨",
    stats: { wu: 75, de: 65, ming: 65, qing: qingVal, cai: 30 },
    innateTalents: [],
    qi: 100,
    badges: [],
    titles: [],
    equippedWeapon: { name: "龍泉太阿劍", tier: 4 },
    ownedWeapons: [{ name: "龍泉太阿劍", tier: 4 }],
    sealedWeapons: [],
    collectedManuals: [],
    weaponHistoryFlags: new Set(),
    artifacts: [],
    comprehendedClassics: [],
    skills: [
      { id: "qjq", name: "七絕劍氣", tier: "上乘", type: "招式", weapon: "劍法", exp: 10 }
    ],
    bonds: [
      { id: "xiao_hanzhou", name: "沈寒舟", gender: "男", intimacyIndex: 4, tacit: 2, relationTag: "義結金蘭", isDead: false, age: 35, maxLifespan: 95 }
    ],
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
  document.getElementById("ev-modal-desc").textContent = "";
}

const report = { dir1: {}, dir2: {}, dir3: {}, hangouts: {} };

// Direction 1: enrichCrisisChoices + openEventModal
function renderCrisisChoicesFor(ev) {
  resetUi();
  const baseChoices = [{ text: "尋隙退避", onSelect: () => {} }];
  openEventModal(ev.title, "江湖風波", ev.desc, enrichCrisisChoices(ev, baseChoices));
  return document.getElementById("ev-modal-choices").children.map(b => b.innerHTML);
}

player = makeTestPlayer(120);
const framingBtnsHigh = renderCrisisChoicesFor({ title: "皇綱失竊疑雲", desc: "官府懷疑你涉案。" });
const poisonBtnsHigh = renderCrisisChoicesFor({ title: "南疆赤蠍瘴", desc: "毒瘴漫天，同伴險些昏迷。" });
const ambushBtnsHigh = renderCrisisChoicesFor({ title: "荒郊黑衣劫殺", desc: "數名山賊刀手截住去路。" });
const tombBtnsHigh = renderCrisisChoicesFor({ title: "北冥古墓 · 噬魂九幽陣", desc: "誤入先秦古墓地宮，石門閉合。" });

if (!framingBtnsHigh.some(h => h.includes("重情重義") && h.includes("八方作保"))) {
  throw new Error("Missing qing framing option: " + JSON.stringify(framingBtnsHigh));
}
if (!poisonBtnsHigh.some(h => h.includes("重情重義") && h.includes("故舊送藥"))) {
  throw new Error("Missing qing poison option: " + JSON.stringify(poisonBtnsHigh));
}
if (!ambushBtnsHigh.some(h => h.includes("重情重義") && h.includes("以情化戈"))) {
  throw new Error("Missing qing ambush option: " + JSON.stringify(ambushBtnsHigh));
}
if (tombBtnsHigh.some(h => h.includes("重情重義") || h.includes("以情化戈"))) {
  throw new Error("Unexpected qing option in solo tomb: " + JSON.stringify(tombBtnsHigh));
}

player = makeTestPlayer(50);
const ambushBtnsLow = renderCrisisChoicesFor({ title: "荒郊黑衣劫殺", desc: "數名山賊刀手截住去路。" });
if (ambushBtnsLow.some(h => h.includes("重情重義") || h.includes("以情化戈"))) {
  throw new Error("Unexpected qing option at qing=50: " + JSON.stringify(ambushBtnsLow));
}
report.dir1 = { framing: true, poison: true, ambush: true, soloTombExcluded: true, lowQingHidden: true };

// Direction 2: Snow-in-charcoal aid + Manual/Weapon aid + Dynamic lethal rescue
const origRandom = Math.random;
Math.random = () => 0.1;

resetUi();
player = makeTestPlayer(120);
player.heavyInjuries = 1;
player.injuries = 1;
if (!window.triggerQingFriendOrSpouseGift() || player.heavyInjuries !== 0) {
  Math.random = origRandom;
  throw new Error("Expected triggerQingFriendOrSpouseGift to cure 1 heavy injury");
}
report.dir2.heavyInjuryCured = true;

resetUi();
player = makeTestPlayer(120);
player.stats.cai = 3;
if (!window.triggerQingFriendOrSpouseGift() || player.stats.cai !== 13) {
  Math.random = origRandom;
  throw new Error("Expected triggerQingFriendOrSpouseGift to grant +10 silver when cai<=5, got cai=" + player.stats.cai);
}
report.dir2.povertyAidSilver = player.stats.cai;

resetUi();
player = makeTestPlayer(140);
player.collectedManuals = [{ name: "羅剎修羅槍" }];
if (!window.triggerQingFriendOrSpouseGift() || player.collectedManuals.length !== 0) {
  Math.random = origRandom;
  throw new Error("Expected triggerQingFriendOrSpouseGift to unlock collected manual");
}
report.dir2.manualUnlocked = true;

resetUi();
player = makeTestPlayer(160);
player.sealedWeapons = [{ name: "玄鐵判官筆" }];
if (!window.triggerQingFriendOrSpouseGift() || player.sealedWeapons.length !== 0) {
  Math.random = origRandom;
  throw new Error("Expected triggerQingFriendOrSpouseGift to unseal weapon");
}
report.dir2.weaponUnsealed = true;

player = makeTestPlayer(200);
Math.random = () => 0.72; // qingRescueProb at qing=200 is min(0.80, 0.40 + 13*0.03=0.79)
if (!tryMiracleRescueFromDeath("測試必死絕境", false)) {
  Math.random = origRandom;
  throw new Error("Expected tryMiracleRescueFromDeath to succeed at roll=0.72 with qing=200");
}
Math.random = origRandom;
report.dir2.miracleRescueHighQing = true;

// Direction 3: Immortal co-cultivation 3rd option + tribulation shield in tickImmortalYear
resetUi();
player = makeTestPlayer(300);
player.inImmortalPhase = true;
player.isImmortalUnlocked = true;
player.fakedDeath = true;
player.age = 550;
player.maxLifespan = 2000;
player.bonds = [
  { id: "tao_hua", name: "洛凝霜", gender: "女", intimacyIndex: 5, tacit: 3, relationTag: "神仙眷侶", isDead: false, isImmortal: true, age: 550, maxLifespan: 600 }
];
triggerImmortalMemoryVisit();
const immBtns = document.getElementById("ev-modal-choices").children;
const guardBtn = immBtns.find(b => b.innerHTML.includes("本命真元護道"));
if (!guardBtn) {
  throw new Error("Missing 3rd qing>=250 guard option in triggerImmortalMemoryVisit");
}
guardBtn.click();
if ((player.bonds[0].qingTribulationShield || 0) < 1 || player.bonds[0].maxLifespan <= 600) {
  throw new Error("Expected guard option to grant shield & lifespan extension: " + JSON.stringify(player.bonds[0]));
}
// Advance companion to exceed maxLifespan -> should consume shield and survive!
player.bonds[0].age = player.bonds[0].maxLifespan;
tickImmortalYear();
if (player.bonds[0].isDead || player.bonds[0].qingTribulationShield !== 0 || !document.getElementById("log-container").innerHTML.includes("情義護道 · 聯手渡玄雷劫")) {
  throw new Error("Expected tickImmortalYear to shield companion from tribulation: " + JSON.stringify(player.bonds[0]));
}
report.dir3.immortalShieldWorked = true;

// High-qing companion hangout scenarios (all 5 scenarios)
player = makeTestPlayer(80);
if (triggerHighQingCompanionHangout() !== false) {
  throw new Error("Expected hangout to return false when qing < 100");
}

const hangoutIds = [
  "hq_old_alley_wine",
  "hq_peak_martial_talk",
  "hq_riverside_life_talk",
  "hq_snow_hearth_trust",
  "hq_lantern_street_elders"
];
hangoutIds.forEach(hid => {
  resetUi();
  player = makeTestPlayer(220);
  player.lightInjuries = 1;
  player.injuries = 1;
  const ok = triggerHighQingCompanionHangout(null, hid);
  const btns = document.getElementById("ev-modal-choices").children;
  if (!ok || btns.length !== 3) {
    throw new Error(`Hangout ${hid} failed to open properly: ok=${ok}, btns=${btns.length}`);
  }
  let targetBtn = btns[0];
  if (hid === "hq_snow_hearth_trust") {
    targetBtn = btns.find(b => b.innerHTML.includes("接過對方的靈藥當場調息護脈"));
  } else if (hid === "hq_riverside_life_talk") {
    targetBtn = btns.find(b => b.innerHTML.includes("護住想護的人"));
  } else if (hid === "hq_lantern_street_elders") {
    targetBtn = btns.find(b => b.innerHTML.includes("買兩串冰糖葫蘆"));
  }
  const prevLife = player.maxLifespan;
  targetBtn.click();
  if (hid === "hq_snow_hearth_trust" && player.lightInjuries !== 0) {
    throw new Error("hq_snow_hearth_trust choice 1 did not cure light injury");
  }
  if ((hid === "hq_riverside_life_talk" || hid === "hq_lantern_street_elders") && player.maxLifespan !== prevLife + 1) {
    throw new Error(`Hangout ${hid} did not apply lifeGain +1`);
  }
  report.hangouts[hid] = document.getElementById("ev-modal-title").textContent;
});

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
