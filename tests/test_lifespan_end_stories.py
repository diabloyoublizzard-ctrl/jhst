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
function makeElderPlayer() {
  return {
    name: "柳忘機",
    gender: "男",
    title: "開山祖師",
    age: 72,
    month: 1,
    ganzhiIndex: 0,
    maxLifespan: 72,
    lifespanEndModalShown: false,
    sect: "太華清風派",
    sectOrigin: "華山派",
    sectTrait: "開山始祖",
    tier: "絕世宗師",
    stats: { wu: 140, de: 95, ming: 110, qing: 88, cai: 60 },
    innateTalents: ["書香世家"],
    qi: 500,
    badges: ["開山祖師", "滄州仁俠"],
    titles: ["玄鏡銅章捕快", "開山祖師"],
    titleHistory: [{ age: 72, title: "開山祖師" }],
    equippedWeapon: { name: "天蠶金絲手套", tier: 5, tierName: "神兵" },
    ownedWeapons: [{ name: "天蠶金絲手套", tier: 5, tierName: "神兵" }],
    sealedWeapons: [],
    weaponHistoryFlags: new Set(),
    artifacts: [],
    comprehendedClassics: [],
    collectedManuals: [],
    skills: [
      { id: "wrgy", name: "萬刃歸元", tier: "曠世", type: "招式", weapon: "劍法", exp: 10 },
      { id: "wxtj", name: "無相太虛訣", tier: "曠世", type: "內功", weapon: "心法", exp: 10 },
      { id: "txb", name: "九天玄虛踏星步", tier: "曠世", type: "輕功", weapon: "身法", exp: 10 }
    ],
    bonds: [
      { id: "ling_yan", name: "葉緋煙", intimacyIndex: 5, tacit: 3, relationTag: "紅塵伴侶", isDead: false },
      { id: "xiao_hanzhou", name: "沈寒舟", intimacyIndex: 5, tacit: 3, relationTag: "義結金蘭", isDead: true, deathAge: 52 }
    ],
    children: [
      { name: "柳慕雲", givenName: "慕雲", gender: "女", orderLabel: "長女", parentName: "葉緋煙", age: 25 }
    ],
    disciples: [
      { name: "陸青風", title: "大弟子", age: 24, inheritedSkill: "萬刃歸元" }
    ],
    mounts: [
      { id: "m1", name: "踏雪烏騅", tier: "神駒", icon: "🐎", isDead: false }
    ],
    karmicSeeds: [{ who: "昔年救下的江南書生", savedAtAge: 28 }],
    injuryHistory: [{ age: 36, kind: "heavy", source: "南疆黑水鎮 · 血巫教百鬼血祭" }],
    worldHistory: [],
    usedEvents: new Set(),
    usedEpochEvents: new Set(),
    triggeredBattles: new Set(),
    triggeredAllianceLeaderEvents: new Set(),
    fakedDeath: false,
    inImmortalPhase: false,
    isDead: false,
    injuries: 0,
    lightInjuries: 0,
    heavyInjuries: 0,
    hasCreatedOwnSkill: false,
    ownSkillName: null,
    isAllianceLeader: false,
    logs: []
  };
}

function resetUiForTest() {
  document.getElementById("log-container").innerHTML = "";
  document.getElementById("btn-open-epilogue").style.display = "none";
  document.getElementById("ev-modal-choices").innerHTML = "";
  document.getElementById("ev-modal-title").textContent = "";
  document.getElementById("ev-modal-tag").textContent = "";
  document.getElementById("ev-modal-desc").textContent = "";
  document.getElementById("ep-cause-pre").textContent = "";
}

const scenarioIds = [
  "end_spouse_sunset",
  "end_heir_lamp",
  "end_ferry_reunion",
  "end_sect_bell",
  "end_weapon_snow",
  "end_mount_vigil",
  "end_old_scars",
  "end_pavilion_wine",
  "end_memoir_ink",
  "end_pine_snow"
];

const results = { scenarios: {}, priorityRescueFirst: false, priorityStoryFallback: false };

scenarioIds.forEach(sid => {
  resetUiForTest();
  player = makeElderPlayer();
  const reason = `歷盡紅塵歲月，身無半點舊傷暗疾，於睡夢中安詳壽終正寢，享壽 ${player.age} 歲。`;
  triggerLifespanEndStoryModal(reason, sid);

  const modalTitle = document.getElementById("ev-modal-title").textContent;
  const modalDesc = document.getElementById("ev-modal-desc").textContent;
  const choiceBtns = document.getElementById("ev-modal-choices").children;
  if (!modalTitle || choiceBtns.length !== 2) {
    throw new Error(`Scenario ${sid} failed to open cleanly: title=${modalTitle}, choices=${choiceBtns.length}`);
  }
  if (player.isDead) {
    throw new Error(`Scenario ${sid} killed player before choice selection`);
  }
  if (document.getElementById("btn-open-epilogue").style.display === "inline-block") {
    throw new Error(`Scenario ${sid} revealed epilogue button before choice selection`);
  }

  if (sid === "end_weapon_snow") {
    const combined = modalTitle + "\n" + modalDesc + "\n" + choiceBtns.map(b => b.innerHTML).join("\n");
    if (/提劍|拔劍|劍標|歸鞘/.test(combined)) {
      throw new Error(`Glove weapon triggered sword phrasing in end_weapon_snow: ${combined}`);
    }
    if (!combined.includes("天蠶金絲手套")) {
      throw new Error(`end_weapon_snow missing equipped glove name: ${combined}`);
    }
  }

  choiceBtns[0].click();

  if (!player.isDead) {
    throw new Error(`Scenario ${sid} did not trigger death after choice click`);
  }
  if (document.getElementById("btn-open-epilogue").style.display !== "inline-block") {
    throw new Error(`Scenario ${sid} did not reveal btn-open-epilogue after choice click`);
  }
  const logsHtml = document.getElementById("log-container").innerHTML;
  if (!logsHtml.includes("📜 【塵緣落幕 · 到此一遊】")) {
    throw new Error(`Scenario ${sid} missing 到此一遊 log prompt after choice click`);
  }
  if (sid === "end_old_scars") {
    const preTxt = document.getElementById("ep-cause-pre").textContent;
    if (!player.deathReason.includes("壽終正寢") || preTxt.includes("宿疾溯源")) {
      throw new Error(`end_old_scars misclassified uninjured elder: reason=${player.deathReason}, pre=${preTxt}`);
    }
  }
  results.scenarios[sid] = modalTitle;
});

// Test priority order in tickMortalMonth: rescue first when random hits rescue
resetUiForTest();
player = makeElderPlayer();
player.age = 71;
player.month = 12;
player.maxLifespan = 72;
const origRandom = Math.random;
Math.random = () => 0.01;
tickMortalMonth();
const rescueTitle = document.getElementById("ev-modal-title").textContent;
const rescueTag = document.getElementById("ev-modal-tag").textContent;
if (!rescueTag.includes("生死大限")) {
  Math.random = origRandom;
  throw new Error(`Expected friend/karmic rescue modal first, got: ${rescueTitle} (${rescueTag})`);
}
const rescueChoices = document.getElementById("ev-modal-choices").children;
rescueChoices[0].click();
if (player.isDead || player.maxLifespan <= 72 || player.lifespanEndModalShown !== false) {
  Math.random = origRandom;
  throw new Error(`Expected successful rescue to extend lifespan and keep player alive: isDead=${player.isDead}, maxLifespan=${player.maxLifespan}, shown=${player.lifespanEndModalShown}`);
}
results.priorityRescueFirst = true;

// Test priority order in tickMortalMonth: when rescue does NOT trigger, 10-story modal opens BEFORE 到此一遊
resetUiForTest();
player = makeElderPlayer();
player.age = 71;
player.month = 12;
player.maxLifespan = 72;
Math.random = () => 0.99;
tickMortalMonth();
Math.random = origRandom;
const storyTitle = document.getElementById("ev-modal-title").textContent;
const storyTag = document.getElementById("ev-modal-tag").textContent;
const logBeforeChoice = document.getElementById("log-container").innerHTML;
if (!storyTitle || !storyTag.includes("壽元終章") || player.isDead || logBeforeChoice.includes("到此一遊")) {
  throw new Error(`Expected 10-story modal before 到此一遊, got title=${storyTitle}, tag=${storyTag}, isDead=${player.isDead}`);
}
document.getElementById("ev-modal-choices").children[0].click();
const logAfterChoice = document.getElementById("log-container").innerHTML;
if (!player.isDead || !logAfterChoice.includes("📜 【塵緣落幕 · 到此一遊】")) {
  throw new Error(`Expected 到此一遊 after story choice, isDead=${player.isDead}`);
}
results.priorityStoryFallback = true;

// Test immortal end-of-lifespan story IDs + tickImmortalYear lifespan clamp
const immIds = [
  "imm_end_grotto_dissolve",
  "imm_end_echo_mortals",
  "imm_end_weapon_monument",
  "imm_end_star_ferry"
];
results.immortalScenarios = {};
immIds.forEach(iid => {
  resetUiForTest();
  player = makeElderPlayer();
  player.inImmortalPhase = true;
  player.isImmortalUnlocked = true;
  player.immortalRealm = "大乘期";
  player.age = 31349;
  player.maxLifespan = 31349;
  triggerLifespanEndStoryModal(`壽元耗盡，於洞天福地坐化兵解，享壽 ${player.age} 歲。`, iid);
  const t = document.getElementById("ev-modal-title").textContent;
  const btns = document.getElementById("ev-modal-choices").children;
  if (!t || btns.length !== 2 || player.isDead) {
    throw new Error(`Immortal scenario ${iid} failed pre-choice check`);
  }
  btns[0].click();
  if (!player.isDead || !document.getElementById("log-container").innerHTML.includes("📜 【塵緣落幕 · 到此一遊】")) {
    throw new Error(`Immortal scenario ${iid} failed post-choice check`);
  }
  results.immortalScenarios[iid] = t;
});

// tickImmortalYear clamp test: age=30406, maxLifespan=31349 -> should clamp to 31349 (NOT 32006)
resetUiForTest();
player = makeElderPlayer();
player.inImmortalPhase = true;
player.isImmortalUnlocked = true;
player.immortalRealm = "大乘期";
player.age = 30406;
player.maxLifespan = 31349;
player.bonds = [
  { id: "tao_hua", name: "洛凝霜", intimacyIndex: 5, tacit: 17, relationTag: "義結金蘭", isDead: true, deathAge: 895 },
  { id: "meng_xiang", name: "孟孤鴻", intimacyIndex: 0, tacit: 0, relationTag: "", isDead: true, deathAge: 92 }
];
player.disciples = [
  { name: "林驚羽", title: "開山大弟子", originTitle: "寒門劍童", trait: "重情重義", age: 15, recruitedAtPlayerAge: 52, inheritedSkill: "七絕劍氣", lastInteractAge: -1 }
];
tickImmortalYear();
if (player.age !== 31349) {
  throw new Error(`Expected tickImmortalYear to clamp age to maxLifespan=31349, got ${player.age}`);
}
if (player.isDead) {
  throw new Error("Expected immortal end story modal before 到此一遊");
}
const immStoryTitle = document.getElementById("ev-modal-title").textContent;
if (!immStoryTitle || document.getElementById("ev-modal-choices").children.length !== 2) {
  throw new Error("Expected immortal end story modal to open when hitting maxLifespan");
}
// Disciple 林驚羽 must now be dead with deathAge <= 96, NOT 31312歲
if (!player.disciples[0].isDead || player.disciples[0].deathAge > 96) {
  throw new Error("Expected mortal disciple to pass away cleanly: " + JSON.stringify(player.disciples[0]));
}
renderBondsTab();
const bondsHtml = document.getElementById("bonds-list").innerHTML;
if (!bondsHtml.includes("已故 · 享壽") || bondsHtml.includes("師徒拆招")) {
  throw new Error("Expected bonds list to show 已故 · 享壽 for deceased disciple: " + bondsHtml);
}
interactWithFamilyMember("disciple", 0);
if (!document.getElementById("log-container").innerHTML.includes("緬懷佳徒")) {
  throw new Error("Expected memorial log when interacting with deceased disciple");
}
document.getElementById("ev-modal-choices").children[0].click();
if (!player.isDead || !document.getElementById("log-container").innerHTML.includes("享壽 31349 歲")) {
  throw new Error("Expected death reason after clicking immortal ending choice with clamped age 31349");
}
results.immortalClampAndDisciple = true;

// Female sworn bond wording check (義姊 instead of 義兄)
resetUiForTest();
player = makeElderPlayer();
player.gender = "女";
const taoChar = DB.CHARACTERS.find(c => c.id === "tao_hua");
const taoBond = { id: "tao_hua", name: "洛凝霜", gender: "女", intimacyIndex: 4, tacit: 3, relationTag: "" };
promptBondAscension(taoChar, taoBond);
const swornBtn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("義結金蘭"));
if (!swornBtn) throw new Error("Missing sworn button for 洛凝霜");
swornBtn.click();
const swornLogs = document.getElementById("log-container").innerHTML;
if (!swornLogs.includes("義姊") || swornLogs.includes("義兄")) {
  throw new Error("Female protagonist sworn log invalid: " + swornLogs);
}
results.femaleSwornFixed = true;

// Century event dynamic body/root tier replacement check
resetUiForTest();
player = makeElderPlayer();
player.inImmortalPhase = true;
player.bodyTierIndex = 5; // 荒古聖體
player.rootTierIndex = 5; // 混沌道胎靈根
triggerCenturyMajorImmortalEvent(1100);
const centBtn = document.getElementById("ev-modal-choices").children[0];
centBtn.click();
const centLog = document.getElementById("log-container").innerHTML;
if (/下品真靈根|上品天靈根|太虛不滅軀|金剛琉璃體/.test(centLog)) {
  throw new Error("Century event leaked lower tier name for max-tier player: " + centLog);
}
results.centuryTierDynamic = true;

// Healing single-emoji check (no 🩸【🩸)
resetUiForTest();
player = makeElderPlayer();
player.heavyInjuries = 1;
player.lightInjuries = 0;
player.injuries = 1;
triggerInjuryEvent();
document.getElementById("ev-modal-choices").children[0].click();
const healLog = document.getElementById("log-container").innerHTML;
if (healLog.includes("🩸【🩸") || healLog.includes("🩹【🩹")) {
  throw new Error("Duplicate emoji in healing log: " + healLog);
}
results.healingEmojiClean = true;

window.__TEST_REPORT = JSON.stringify({ ok: true, results });
})();
window.__TEST_REPORT;
'''

if "拈鬚" in data_js:
    raise AssertionError("data.js still contains 拈鬚")
if "洛凝霜河燈" in patches_js or "血色洛凝霜" in patches_js:
    raise AssertionError("patches.js still contains 洛凝霜河燈 or 血色洛凝霜")
if "蓮花河燈" not in patches_js or "血色寒梅漫天綻放" not in patches_js:
    raise AssertionError("patches.js missing fixed 蓮花河燈 or 血色寒梅漫天綻放")
if "明教光明頂" in index_html or "vs 浮動門檻" in index_html:
    raise AssertionError("index.html still contains 明教光明頂 or vs 浮動門檻")

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
