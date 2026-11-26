import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data_js = (ROOT / "data.js").read_text(encoding="utf-8")
patches_js = (ROOT / "patches.js").read_text(encoding="utf-8")
index_html = (ROOT / "index.html").read_text(encoding="utf-8")
mobile_html = (ROOT / "jhst_mobile.html").read_text(encoding="utf-8")

# Check Item 8 & UI preservation statically across repo files
for fname, content in [
    ("index.html", index_html),
    ("data.js", data_js),
    ("patches.js", patches_js),
    ("jhst_mobile.html", mobile_html),
]:
    if "天機天機閣" in content:
        raise AssertionError(f"Item 8 failed: found '天機天機閣' in {fname}")

assert "天機閣" in index_html, "Expected '天機閣' in index.html"
assert "古兵匣收藏" in index_html and "秘笈收藏" in index_html and "【武道】分頁" in index_html, (
    "Expected preserved UI guidance text for 武道分頁 / 古兵匣 / 秘笈收藏"
)
assert mobile_html.count("data:audio") == 0, "Expected 0 data:audio embeds in jhst_mobile.html"

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

function hasBrokenUnicode(str) {
  const s = String(str || "");
  if (s.includes("\uFFFD")) return true;
  for (let i = 0; i < s.length; i++) {
    const code = s.charCodeAt(i);
    if (code >= 0xD800 && code <= 0xDBFF) {
      const next = i + 1 < s.length ? s.charCodeAt(i + 1) : 0;
      if (next < 0xDC00 || next > 0xDFFF) return true;
      i++;
    } else if (code >= 0xDC00 && code <= 0xDFFF) {
      return true;
    }
  }
  return false;
}

function makeBasePlayer() {
  return {
    name: "測試俠客",
    gender: "男",
    title: "武林宿老",
    age: 72,
    month: 1,
    ganzhiIndex: 0,
    maxLifespan: 82,
    lifespanEndModalShown: false,
    lifespanRescueCount: 0,
    usedLifespanRescues: [],
    sect: "無門無派",
    tier: "絕世宗師",
    stats: { wu: 100, de: 80, ming: 85, qing: 100, cai: 60 },
    innateTalents: [{ name: "天資聰穎" }],
    qi: 100,
    badges: [],
    titles: [],
    titleHistory: [],
    equippedWeapon: null,
    ownedWeapons: [],
    sealedWeapons: [],
    collectedManuals: [],
    weaponHistoryFlags: new Set(),
    artifacts: [],
    comprehendedClassics: [],
    skills: [{ id: "qjq", name: "七絕劍氣", tier: "上乘", type: "招式", weapon: "劍法", exp: 30 }],
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

// ---------------- Item 1: Relationship prefixes removed ----------------
resetUi();
player = makeBasePlayer();
player.age = 72;
player.month = 12;
player.maxLifespan = 90;
player.bonds = [
  { id: "c1", name: "洛凝霜", intimacyIndex: 3, relationTag: "", age: 72, maxLifespan: 73, isDead: false, restingPlace: "十里寒梅林" },
  { id: "c2", name: "墨千機", intimacyIndex: 0, relationTag: "", age: 72, maxLifespan: 73, isDead: false, restingPlace: "雁門亂石崗" },
  { id: "c3", name: "蘇月華", intimacyIndex: 5, relationTag: "紅塵伴侶", age: 72, maxLifespan: 73, isDead: false, restingPlace: "雲夢翠微峰" }
];
Math.random = () => 0.99; // skip early signal rescue and mount/random events
tickMortalMonth();
Math.random = origRandom;
const deathLogs = document.getElementById("log-container").innerHTML;
assert(!deathLogs.includes("你的友好往來"), "Item 1 failed: death log still has 你的友好往來: " + deathLogs);
assert(!deathLogs.includes("你的仇視彼此"), "Item 1 failed: death log still has 你的仇視彼此: " + deathLogs);
assert(!deathLogs.includes("你的紅塵伴侶"), "Item 1 failed: death log has 你的紅塵伴侶: " + deathLogs);
assert(deathLogs.includes("【洛凝霜】（享年 73 歲）"), "Item 1 failed: missing clean 洛凝霜 log: " + deathLogs);
assert(deathLogs.includes("前塵恩怨隨風散"), "Item 1 failed: missing hostile farewell line: " + deathLogs);
assert(deathLogs.includes("紅塵伴侶【蘇月華】"), "Item 1 failed: spouse relationTag should remain: " + deathLogs);

// Auto grave visit log
resetUi();
player = makeBasePlayer();
player.age = 75;
player.month = 3;
player.bonds = [{ id: "c1", name: "洛凝霜", intimacyIndex: 3, relationTag: "", isDead: true, age: 73, deathAge: 73, restingPlace: "十里寒梅林" }];
Math.random = () => 0.001; // trigger deadCompanions auto visit check (<0.012) while avoiding age<16 and avoiding early bail
// Note: at roll 0.001, checkImmortalWon't trigger because wait - immortalChancePerMonth might be >= 0.001! Check safe values:
player.isImmortalUnlocked = true; // bypass immortal awakening check before grave visit
tickMortalMonth();
Math.random = origRandom;
const graveLogs = document.getElementById("log-container").innerHTML;
assert(!graveLogs.includes("已故友好往來") && !graveLogs.includes("友好往來"), "Item 1 failed: auto grave visit still includes 友好往來: " + graveLogs);

// Companion rescue modal
resetUi();
player = makeBasePlayer();
player.stats.wu = 10;
const rescueBond = { id: "c1", name: "洛凝霜", intimacyIndex: 3, relationTag: "", age: 40, isDead: false, restingPlace: "寒梅林" };
triggerCompanionRescueModal(rescueBond, { young: "與敵死戰" });
const rescueDesc = document.getElementById("ev-modal-desc").textContent;
assert(!rescueDesc.includes("你的友好往來") && rescueDesc.includes("故友【洛凝霜】"), "Item 1 failed: rescue modal desc uses old prefix: " + rescueDesc);
const failRescueBtn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("並肩死戰"));
assert(!!failRescueBtn, "Expected 並肩死戰 button");
failRescueBtn.click();
assert(!document.getElementById("log-container").innerHTML.includes("你的友好往來"), "Item 1 failed: failed rescue log uses old prefix");
report.item1 = true;

// ---------------- Item 2: Mount log simplified ----------------
resetUi();
player = makeBasePlayer();
player.age = 75;
player.mounts = [];
player.pendingMountQuest = {
  stage: 2,
  totalStages: 3,
  waitMonths: 0,
  savedLifeGain: 0,
  target: { id: "qingluan", name: "青鸞信使鳥", icon: "🕊️", title: "蓬萊仙羽", desc: "靈禽。" }
};
advancePendingMountQuest();
const mountBtn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("欣然收服"));
assert(!!mountBtn, "Item 2 failed: missing 欣然收服 button");
mountBtn.click();
const mountLog = document.getElementById("log-container").innerHTML;
assert(mountLog.includes("三番結緣 · 喜獲靈獸青鸞信使鳥"), "Item 2 failed: mount log missing title: " + mountLog);
assert(!mountLog.includes("已配給於右側") && !mountLog.includes("👥 羈絆") && !mountLog.includes("當前隨行"), "Item 2 failed: UI placement text still in log: " + mountLog);
assert(player.mounts.length === 1 && player.mounts[0].acquiredAtPlayerAge === 75 && player.mounts[0].yearsOwned === 0, "Item 2/6 failed: mount initial tracking missing");
report.item2 = true;

// ---------------- Item 3: Lifespan end rescue (chance, decay, cap, age>=119 skip, 7 scenarios) ----------------
// 3a. Age 119 non-immortal skips rescue even at roll=0.0001
resetUi();
player = makeBasePlayer();
player.age = 118;
player.month = 12;
player.maxLifespan = 119;
player.isImmortalUnlocked = false;
Math.random = () => 0.0001;
tickMortalMonth();
Math.random = origRandom;
assert(!document.getElementById("ev-modal-tag").textContent.includes("因果馳援") && !document.getElementById("ev-modal-tag").textContent.includes("大限"), "Actually check title not rescue:");
assert((player.usedLifespanRescues || []).length === 0, "Item 3 failed: age>=119 non-immortal should skip rescue modal, got " + JSON.stringify(player.usedLifespanRescues));

// 3b. lifespanRescueCount >= 3 skips rescue even at roll=0.0001
resetUi();
player = makeBasePlayer();
player.age = 81;
player.month = 12;
player.maxLifespan = 82;
player.lifespanRescueCount = 3;
Math.random = () => 0.0001;
tickMortalMonth();
Math.random = origRandom;
assert((player.usedLifespanRescues || []).length === 0, "Item 3 failed: rescueCount===3 should skip rescue modal");

// 3c. Probability reduced & decays by 0.5 per rescue: qing=100 => baseChance = min(0.35, 0.18 + 0.10) = 0.28
resetUi();
player = makeBasePlayer();
player.age = 81;
player.month = 12;
player.maxLifespan = 82;
player.stats.qing = 100;
Math.random = () => 0.40; // old 30%-65% (0.50) would trigger; new 0.28 must NOT trigger
tickMortalMonth();
Math.random = origRandom;
assert((player.usedLifespanRescues || []).length === 0, "Item 3 failed: roll=0.40 with baseChance=0.28 should not trigger rescue");

resetUi();
player = makeBasePlayer();
player.age = 84;
player.month = 12;
player.maxLifespan = 85;
player.stats.qing = 100;
player.lifespanRescueCount = 1; // effective chance = 0.28 * 0.5 = 0.14
Math.random = () => 0.20;
tickMortalMonth();
Math.random = origRandom;
assert((player.usedLifespanRescues || []).length === 0, "Item 3 failed: roll=0.20 with rescueCount=1 (eff 0.14) should not trigger");

// 3d. Test all 7 scenario IDs + Xiaoman age adaptation + non-repeat across 3 calls + cap<=120
const scenarioIds = [
  "rescue_living_bond",
  "rescue_xiaoman",
  "rescue_heir_ginseng",
  "rescue_zhongnan_taoist",
  "rescue_beast_nectar",
  "rescue_caravan_snowlotus",
  "rescue_monk_dahuandan"
];
scenarioIds.forEach(sid => {
  resetUi();
  player = makeBasePlayer();
  player.age = 82;
  player.maxLifespan = 82;
  player.cangzhouOutcome = "saved_xiaoman";
  player.bonds = [{ id: "b1", name: "沈寒舟", intimacyIndex: 4, isDead: false }];
  player.children = [{ name: "柳念安", orderLabel: "長子", isDead: false }];
  player.mounts = [{ name: "青鸞信使鳥", icon: "🕊️", isDead: false }];
  player.karmicSeeds = [{ who: "西域藥商一家" }];
  triggerLifespanEndRescueModal(sid);
  const title = document.getElementById("ev-modal-title").textContent;
  const desc = document.getElementById("ev-modal-desc").textContent;
  const btns = document.getElementById("ev-modal-choices").children;
  assert(btns.length === 2, "Item 3 failed: rescue scenario " + sid + " must have 2 choices");
  assert(!hasBrokenUnicode(title) && !hasBrokenUnicode(desc), "Broken unicode in rescue scenario " + sid);
  if (sid === "rescue_xiaoman") {
    assert(desc.includes("溫小滿") && desc.includes("逆天九針"), "Expected 溫小滿 at age 82");
  }
  if (sid === "rescue_zhongnan_taoist") assert(desc.includes("玄虛真人"), "Missing 玄虛真人");
  if (sid === "rescue_beast_nectar") assert(desc.includes("萬年地脈石鐘乳") && desc.includes("青鸞信使鳥"), "Missing beast nectar");
  if (sid === "rescue_caravan_snowlotus") assert(desc.includes("天山冰心雪蓮王"), "Missing caravan snowlotus");
  if (sid === "rescue_monk_dahuandan") assert(desc.includes("無相尊者") && desc.includes("菩提大還丹"), "Missing monk dahuandan");
  Math.random = () => 0.01;
  btns[0].click();
  Math.random = origRandom;
  assert(player.maxLifespan > 82 && player.lifespanRescueCount === 1, "Item 3 failed: rescue success did not extend maxLifespan/count for " + sid);
});

// Xiaoman at age 95 -> apprentice Wen Qinghe
resetUi();
player = makeBasePlayer();
player.age = 95;
player.cangzhouOutcome = "saved_xiaoman";
triggerLifespanEndRescueModal("rescue_xiaoman");
assert(document.getElementById("ev-modal-desc").textContent.includes("溫青禾") && !document.getElementById("ev-modal-desc").textContent.includes("小醫女【溫小滿】"), "Item 3 failed: age 95 xiaoman should use 溫青禾");

// Heir ginseng when all heirs dead -> grand-disciple
resetUi();
player = makeBasePlayer();
player.disciples = [{ name: "陸傳薪", title: "親傳弟子", isDead: true }];
triggerLifespanEndRescueModal("rescue_heir_ginseng");
assert(document.getElementById("ev-modal-desc").textContent.includes("再傳後輩"), "Item 3 failed: dead disciple should send 再傳後輩");

// Non-repeating 3 draws & cap at 120
resetUi();
player = makeBasePlayer();
player.age = 117;
player.maxLifespan = 117;
for (let i = 0; i < 3; i++) {
  triggerLifespanEndRescueModal();
}
assert(new Set(player.usedLifespanRescues).size === 3, "Item 3 failed: expected 3 distinct rescue scenarios, got " + JSON.stringify(player.usedLifespanRescues));
Math.random = () => 0.01;
document.getElementById("ev-modal-choices").children[0].click();
Math.random = origRandom;
assert(player.maxLifespan <= 120, "Item 3 failed: mortal maxLifespan exceeded 120: " + player.maxLifespan);
report.item3 = true;

// ---------------- Item 4: No broken surrogate characters in healing & injury origin ----------------
HEAVY_INJURY_CURE_SCENARIOS.forEach(sc => {
  const cleanTitle = String(sc.title || "").replace(/^[🩸🩹]\s*/u, "");
  assert(!hasBrokenUnicode(cleanTitle) && cleanTitle.length > 4 && !cleanTitle.startsWith(" "), "Item 4 heavy cleanTitle invalid: " + JSON.stringify(cleanTitle));
});
LIGHT_INJURY_CURE_SCENARIOS.forEach(sc => {
  const cleanTitle = String(sc.title || "").replace(/^[🩸🩹]\s*/u, "");
  assert(!hasBrokenUnicode(cleanTitle) && cleanTitle.length > 4 && !cleanTitle.startsWith(" "), "Item 4 light cleanTitle invalid: " + JSON.stringify(cleanTitle));
});
resetUi();
player = makeBasePlayer();
player.lightInjuries = 1;
player.heavyInjuries = 1;
player.injuries = 2;
player.lastEventContext = { title: "⚔️ 陰山血戰" };
addHeavyInjury(1);
assert(player.injuryHistory.length === 1 && !hasBrokenUnicode(player.injuryHistory[0].source) && player.injuryHistory[0].source === "陰山血戰", "Item 4 recordInjuryOrigin failed: " + JSON.stringify(player.injuryHistory));
triggerInjuryEvent();
document.getElementById("ev-modal-choices").children[0].click();
assert(!hasBrokenUnicode(document.getElementById("log-container").innerHTML), "Item 4 triggerInjuryEvent log has broken unicode");
report.item4 = true;

// ---------------- Item 5: 無門無派 · 授藝宗師 excluded from end_sect_bell ----------------
for (let i = 0; i < 50; i++) {
  resetUi();
  player = makeBasePlayer();
  player.sect = "無門無派 · 授藝宗師";
  player.title = "一代名師";
  player.isAllianceLeader = false;
  player.lifespanEndModalShown = false;
  triggerLifespanEndStoryModal(null, i === 0 ? "end_sect_bell" : null);
  const title = document.getElementById("ev-modal-title").textContent;
  const desc = document.getElementById("ev-modal-desc").textContent;
  assert(!desc.includes("無門無派 · 授藝宗師"), "Item 5 failed: desc contains 無門無派 · 授藝宗師: " + desc);
  if (i === 0) {
    assert(desc.includes("【山門大殿】"), "Item 5 failed: fallback placeName should be 山門大殿: " + desc);
  } else {
    assert(!title.includes("宗門鐘鳴"), "Item 5 failed: end_sect_bell should not be eligible for 無門無派 · 授藝宗師: " + title);
  }
}
report.item5 = true;

// ---------------- Item 6: Monument mounts, hostile bonds, dead heirs ----------------
player = makeBasePlayer();
player.age = 85;
player.mounts = [
  { name: "青鸞信使鳥", icon: "🕊️", title: "蓬萊仙羽", age: 17, initialAge: 5, maxLifespan: 37, acquiredAtPlayerAge: 73, yearsOwned: 12, isDead: false },
  { name: "赤電汗血寶馬", icon: "🐎", title: "汗血王駒", age: 25, initialAge: 4, maxLifespan: 25, deathAge: 25, deathPlayerAge: 70, acquiredAtPlayerAge: 50, yearsOwned: 20, isDead: true }
];
player.bonds = [
  { id: "b_hostile", name: "墨千機", intimacyIndex: 0, relationTag: "", isDead: true, deathAge: 72, restingPlace: "雁門亂石崗" },
  { id: "b_neutral", name: "李素衣", intimacyIndex: 2, relationTag: "", isDead: true, deathAge: 68, restingPlace: "九江渡" },
  { id: "b_friend", name: "沈寒舟", intimacyIndex: 4, relationTag: "", isDead: true, deathAge: 79, restingPlace: "滄江畔" }
];
player.children = [{ name: "柳念安", orderLabel: "長子", isDead: true, age: 75, maxLifespan: 75 }];
player.disciples = [{ name: "陸傳薪", title: "親傳弟子", isDead: true, age: 78, maxLifespan: 78 }];
const mData1 = buildEpilogueMonumentData("壽終正寢", [{ name: "煙雨過客", quote: "test" }]);
assert(mData1.allMounts.length === 2, "Item 6 failed: expected 2 mounts");
assert(mData1.allMounts[0].isAlive === true && mData1.allMounts[0].status.includes("相伴 12 載"), "Item 6 failed living mount years: " + JSON.stringify(mData1.allMounts[0]));
assert(mData1.allMounts[1].isAlive === false && mData1.allMounts[1].status.includes("相伴 20 載"), "Item 6 failed dead mount years: " + JSON.stringify(mData1.allMounts[1]));
assert(mData1.beastStory.includes("靈獸守塚") && mData1.beastStory.includes("青鸞信使鳥") && !mData1.beastStory.includes("赤電汗血寶馬"), "Item 6 failed beastStory: " + mData1.beastStory);
const aw = mData1.afterwordLines.join("\n");
assert(aw.includes("墨千機") && aw.includes("前塵恩怨皆隨黃土散盡，各赴來生") && !aw.includes("墨千機（先你而去 · 享年72歲）】已先一步長眠於【雁門亂石崗】，黃泉路上含笑相迎"), "Item 6 failed hostile bond line: " + aw);
assert(aw.includes("李素衣") && aw.includes("萍水相逢之緣至此畫下句點"), "Item 6 failed neutral bond line: " + aw);
assert(aw.includes("沈寒舟") && aw.includes("黃泉路上含笑相迎"), "Item 6 failed friendly bond line: " + aw);
assert(aw.includes("門下再傳後輩仍齊聚你的碑前") && !aw.includes("長子【柳念安】與親傳弟子【陸傳薪】跪於你的碑前"), "Item 6 failed dead heirs line: " + aw);

// When ALL mounts are dead
player.mounts[0].isDead = true;
player.mounts[0].deathAge = 37;
player.mounts[0].deathPlayerAge = 84;
const mDataAllDeadMounts = buildEpilogueMonumentData("壽終正寢", [{ name: "煙雨過客", quote: "test" }]);
assert(mDataAllDeadMounts.beastStory.includes("故獸重逢") && !mDataAllDeadMounts.beastStory.includes("靈獸守塚"), "Item 6 failed all dead mounts beastStory: " + mDataAllDeadMounts.beastStory);

// Mount yearsOwned increments in tickMortalMonth & tickImmortalYear
player = makeBasePlayer();
player.age = 40;
player.month = 12;
player.maxLifespan = 90;
player.mounts = [assignMountLifespan({ name: "黑雲追風駒", age: 4, maxLifespan: 28 })];
Math.random = () => 0.99;
tickMortalMonth();
assert(player.mounts[0].yearsOwned === 1 && player.mounts[0].age === 5, "Item 6 failed tickMortalMonth mount aging");
player.inImmortalPhase = true;
player.isImmortalUnlocked = true;
player.maxLifespan = 2000;
Math.random = () => 0.0; // stepYears = 5
tickImmortalYear();
Math.random = origRandom;
assert(player.mounts[0].yearsOwned === 6 && player.mounts[0].age === 10, "Item 6 failed tickImmortalYear mount aging: " + JSON.stringify(player.mounts[0]));
report.item6 = true;

// ---------------- Item 7: 武林盟主 seal requires actual title ----------------
player = makeBasePlayer();
player.stats.wu = 150;
player.stats.ming = 150;
player.isAllianceLeader = false;
player.title = "絕世宗師";
player.badges = [];
const sealsWithout = evaluatePosthumousSeals().map(s => s.name);
assert(!sealsWithout.includes("武林盟主"), "Item 7 failed: 武林盟主 seal misfired without alliance leader: " + JSON.stringify(sealsWithout));
player.isAllianceLeader = true;
const sealsWith = evaluatePosthumousSeals().map(s => s.name);
assert(sealsWith.includes("武林盟主"), "Item 7 failed: 武林盟主 seal missing when isAllianceLeader=true");
report.item7 = true;

// ---------------- Item 9: News variety + weapon sell price ----------------
player = makeBasePlayer();
player.worldHistory = [];
player.age = 20;
player.ganzhiIndex = 5;
Math.random = () => 0.7; // >= 0.35 so always records dynamic news; picks fixed index unless freshPool works!
for (let y = 0; y < 18; y++) {
  player.age = 20 + y;
  player.ganzhiIndex = (player.ganzhiIndex + 1) % 60;
  // Bypass DB.TIMELINE static entries by advancing to empty ganzhi if needed, just collect whatever dynamic adds
  if (!DB.TIMELINE[getCurrentGanzhi()]) {
    recordYearlyWorldNews(getCurrentGanzhi());
  }
}
Math.random = origRandom;
const seenNews = player.worldHistory.map(h => h.text);
assert(seenNews.length >= 10 && new Set(seenNews).size === seenNews.length, "Item 9 failed: duplicate dynamic world news: " + JSON.stringify(seenNews));

// Weapon sell price & wording check
resetUi();
player = makeBasePlayer();
player.stats.wu = 70; // allows tier 5 weapons (and let's remove lower tier weapons from ownedWeapons? Easier: put all tier<=4 weapons into sealedWeapons)
player.sealedWeapons = Object.values(WEAPONS_DB).filter(w => (w.tier || 1) < 5).map(w => ({ name: w.name }));
player.stats.cai = 80; // wealthy player!
triggerWeaponEncounter();
// Sequence for handleWeaponAcquireAttempt: roll=0.1 (<1/3) -> missScenarios idx = floor(0.55*4) = 2 (silverScenario)
const q = [0.1, 0.55];
let qiIdx = 0;
Math.random = () => q[qiIdx++] ?? 0.5;
document.getElementById("ev-modal-choices").children[0].click();
Math.random = origRandom;
const wLog = document.getElementById("log-container").innerHTML;
assert(!wLog.includes("囊中羞澀") && wLog.includes("識貨讓寶"), "Item 9 failed: rich player still got 囊中羞澀: " + wLog);
assert(player.stats.cai === 80 + 25 && wLog.includes("25 兩紋銀"), "Item 9 failed: tier-5 weapon sell silver expected +25, got cai=" + player.stats.cai + " log=" + wLog);
report.item9 = true;

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
