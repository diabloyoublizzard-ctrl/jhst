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

function makeImmortalPlayer() {
  return {
    name: "白寒舟",
    gender: "男",
    title: "築基道人",
    age: 130,
    month: 1,
    ganzhiIndex: 0,
    maxLifespan: 260,
    lifespanEndModalShown: false,
    sect: "霸刀門",
    tier: "超凡入聖",
    immortalStage: 1,
    bodyTierIndex: 1,
    rootTierIndex: 1,
    stats: { wu: 150, de: 120, ming: 120, qing: 120, cai: 50 },
    innateTalents: [{ name: "書香世家" }],
    qi: 50000,
    badges: [],
    titles: [],
    titleHistory: [],
    equippedWeapon: { name: "干將莫邪雙劍", tier: 5 },
    ownedWeapons: [],
    sealedWeapons: [],
    collectedManuals: [],
    weaponHistoryFlags: new Set(),
    artifacts: [{ id: "taixu_armor", name: "太虛神甲" }],
    comprehendedClassics: [],
    skills: [{ name: "太清黃庭內景經", isScripture: true, isLockedScripture: false }],
    scriptureUses: 5,
    scriptureLogs: [],
    bonds: [],
    children: [],
    disciples: [],
    mounts: [],
    karmicSeeds: [],
    injuryHistory: [],
    worldHistory: [],
    usedEvents: new Set(),
    usedEpochEvents: new Set(),
    usedImmortalEvents: new Set(),
    triggeredBattles: new Set(),
    triggeredAllianceLeaderEvents: new Set(),
    fakedDeath: false,
    inImmortalPhase: true,
    isImmortalUnlocked: true,
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

// 1. Validate DB.EVENTS.immortal_events catalog (40 total, 30 new across 5 themes x 6)
const immEvents = DB.EVENTS.immortal_events || [];
assert(immEvents.length === 40, "Expected 40 immortal_events, got " + immEvents.length);
const newIds = immEvents.map(e => e.id).filter(Boolean);
assert(newIds.length === 40 && new Set(newIds).size === 40, "Expected 40 unique ids");
const prefixes = ["imm_vein_", "imm_body_", "imm_root_", "imm_cult_", "imm_dao_"];
prefixes.forEach(pfx => {
  const grp = immEvents.filter(e => e.id && e.id.startsWith(pfx));
  assert(grp.length === 6, "Expected 6 events for prefix " + pfx + ", got " + grp.length);
});
immEvents.forEach(e => {
  assert(!hasBrokenUnicode(e.title) && !hasBrokenUnicode(e.desc), "Broken unicode in event " + e.id);
  assert(Array.isArray(e.choices) && e.choices.length >= 2, "Expected >=2 choices in " + e.id);
  e.choices.forEach(c => {
    assert(!hasBrokenUnicode(c.text) && !hasBrokenUnicode(c.result || ""), "Broken unicode in choice of " + e.id);
  });
});
report.catalog = { total: immEvents.length, newThemesOk: true };

// 2. Click through EVERY new event and ALL its choices (testing both success and failure rolls on riskRate choices)
const newEvents = immEvents.filter(e => !e.id.startsWith("imm_legacy_"));
assert(newEvents.length === 30, "Expected 30 new events");
newEvents.forEach(ev => {
  ev.choices.forEach((c, cIdx) => {
    resetUi();
    player = makeImmortalPlayer();
    player.qi = 10000;
    const ok = triggerImmortalStoryEvent({ forceEventId: ev.id });
    assert(ok, "Failed to open event " + ev.id);
    const btn = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes(c.text.slice(0, 12)));
    assert(!!btn, "Could not locate choice button for " + ev.id + " idx=" + cIdx);
    Math.random = () => 0.05; // success roll
    btn.click();
    Math.random = origRandom;
    assert(!hasBrokenUnicode(document.getElementById("log-container").innerHTML), "Broken unicode log for " + ev.id);

    if (typeof c.riskRate === "number") {
      resetUi();
      player = makeImmortalPlayer();
      player.maxLifespan = 260;
      triggerImmortalStoryEvent({ forceEventId: ev.id });
      const btnFail = document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes(c.text.slice(0, 12)));
      Math.random = () => 0.99; // fail roll
      btnFail.click();
      Math.random = origRandom;
      assert(!hasBrokenUnicode(document.getElementById("log-container").innerHTML), "Broken unicode fail log for " + ev.id);
    }
  });
});
report.all30EventsExecuted = true;

// 3. Non-repeating draw across 30 consecutive draws + earlyOnly subset check
player = makeImmortalPlayer();
const drawn30 = [];
for (let i = 0; i < 30; i++) {
  resetUi();
  triggerImmortalStoryEvent({ earlyOnly: false });
  drawn30.push(document.getElementById("ev-modal-title").textContent);
}
assert(new Set(drawn30).size === 30, "Expected 30 distinct non-repeating immortal events, got " + new Set(drawn30).size);

player = makeImmortalPlayer();
player.inImmortalPhase = false;
player.age = 45;
const earlyIdsExpected = immEvents.filter(e => e.earlyImmortal === true).map(e => e.title);
const drawnEarly = [];
for (let i = 0; i < earlyIdsExpected.length; i++) {
  resetUi();
  triggerImmortalStoryEvent({ earlyOnly: true });
  const ttl = document.getElementById("ev-modal-title").textContent.replace(/^✨ 仙途初探 · /, "");
  assert(earlyIdsExpected.includes(ttl), "Unexpected non-early event in mortal phase: " + ttl);
  drawnEarly.push(ttl);
}
assert(new Set(drawnEarly).size === earlyIdsExpected.length, "Expected all distinct earlyImmortal events");
report.nonRepeatingAndEarlySubset = { distinct30: 30, earlySubsetCount: earlyIdsExpected.length };

// 4. Mortal phase tickMortalMonth early immortal warmup check
resetUi();
player = makeImmortalPlayer();
player.inImmortalPhase = false;
player.isImmortalUnlocked = true;
player.age = 55;
player.month = 3;
player.maxLifespan = 120;
player.earlyImmortalCooldown = 0;
player.scriptureUses = 10;
// Pick a random sequence where earlier low-prob checks (0.012 grave/etc.) are skipped only if >= threshold? Wait: early check uses < 0.022 while earlier events might fire at 0.022!
// Drive random queue or verify via tickMortalMonth with no bonds/injuries/siblings:
player.bonds = [];
player.children = [];
player.disciples = [];
player.mounts = [];
player.stats.qing = 0; // skip qing gift (< 80) & hangout (< 100)
// What runs at age=55 month=4? Let's trace probabilities before 0.022:
// companionCooldown = 10 skips triggerCompanionEncounter; secretOrgId = "done" skips secretOrgInvitation & Mission? Wait: secretOrgMission runs if secretOrgId set!
// Instead check cooldown behavior directly: set Math.random = () => 0.021 vs 0.99
Math.random = () => 0.99; // first run doesn't trigger anything
Math.random = () => 0.021;
// Prevent sect event / selfKungfu / etc. by mocking minimal blocks or verify cooldown decrement:
player.sect = "無門無派";
player.adultProfession = "";
player.companionCooldown = 5;
player.hasCreatedOwnSkill = true;
player.lastSkillComprehendAge = 55;
player.secretOrgId = null; // 0.008 skips if roll >= 0.008 (0.021 >= 0.008 -> skipped!)
// bottle neck? 0.003 -> skipped! battle? age=55 skip! mythic? 0.002 -> skipped!
// Wait: bodyTemperEncounter is 0.003 -> skipped at 0.021! selfKungfu / random artifact etc.: let's check at 0.015 (which is <0.022 and >=0.008 & >=0.012? Wait: scripture 0.001 skipped!)
Math.random = () => 0.019;
tickMortalMonth();
Math.random = origRandom;
assert(player.earlyImmortalCooldown === 8 && document.getElementById("ev-modal-title").textContent.includes("仙途初探"), "Expected tickMortalMonth early immortal event trigger, got title=" + document.getElementById("ev-modal-title").textContent + " cooldown=" + player.earlyImmortalCooldown);
report.mortalWarmupTriggered = true;

// 5. Body Temper & Root Cleanse probability, failure penalty, no armor consumed, streak +8% up to +32%, bonus integration
// 5a. Mortal failure -> light injury +1, NO taixu_armor consumed, +8% streak, full qi spent
resetUi();
player = makeImmortalPlayer();
player.inImmortalPhase = false;
player.age = 55;
player.month = 6;
player.immortalStage = 0;
player.bodyTierIndex = 0; // next = 1 (銅皮鐵骨, base 0.80, cost 1800)
player.rootTierIndex = 0; // next = 1 (下品真靈根, base 0.80, cost 2600)
player.qi = 100000;
updateImmortalTabUI();
assert(document.getElementById("btn-temper-body").textContent.includes("80%"), "Expected 80% on body button, got: " + document.getElementById("btn-temper-body").textContent);
assert(document.getElementById("btn-cleanse-root").textContent.includes("80%"), "Expected 80% on root button, got: " + document.getElementById("btn-cleanse-root").textContent);

const baseBeforeFail = getBodyTemperRate();
assert(baseBeforeFail === 0.80, "Expected 0.80");
Math.random = () => 0.99; // fail!
attemptBodyTemper();
Math.random = origRandom;
assert(player.bodyTierIndex === 0, "Expected body tier unchanged on fail");
assert(player.qi === 100000 - 1800, "Expected full cost deducted on fail, got qi=" + player.qi);
assert(player.lightInjuries === 1, "Expected mortal fail light injury +1");
assert(hasArtifact("taixu_armor"), "Expected taixu_armor NOT consumed on body temper fail");
assert(player.bodyTemperFailStreak === 1 && getBodyTemperRate() === 0.88, "Expected +8% streak after 1 fail, got " + getBodyTemperRate());

// 5b. Immortal phase failure -> -5 maxLifespan, NO taixu_armor consumed, streak caps at 4 (+32%)
player = makeImmortalPlayer();
player.inImmortalPhase = true;
player.immortalStage = 0;
player.bodyTierIndex = 4; // next = 5 (荒古聖體, base 0.30, cost 400000)
player.rootTierIndex = 0;
player.qi = 3000000;
player.maxLifespan = 260;
const rStart = getBodyTemperRate();
assert(rStart === 0.30, "Expected 0.30 base for 荒古聖體, got " + rStart);
for (let f = 1; f <= 5; f++) {
  Math.random = () => 0.99;
  attemptBodyTemper();
  Math.random = origRandom;
}
assert(player.bodyTemperFailStreak === 4, "Expected fail streak capped at 4, got " + player.bodyTemperFailStreak);
assert(player.maxLifespan === 260 - 25, "Expected -5 lifespan per immortal fail (5 fails -> -25), got " + player.maxLifespan);
assert(hasArtifact("taixu_armor"), "Expected taixu_armor still intact");
assert(getBodyTemperRate() === 0.62, "Expected 0.30 + 0.32 = 0.62, got " + getBodyTemperRate());

// Add event bonus +15% -> button shows 含靈韻 and rate rises to 0.77, consumed after 1 attempt
player.bodyTemperBonus = 0.15;
updateImmortalTabUI();
assert(document.getElementById("btn-temper-body").textContent.includes("77%含靈韻"), "Expected 77%含靈韻 button label, got: " + document.getElementById("btn-temper-body").textContent);
Math.random = () => 0.01; // succeed!
attemptBodyTemper();
Math.random = origRandom;
assert(player.bodyTierIndex === 5 && player.bodyTemperFailStreak === 0 && player.bodyTemperBonus === 0 && player.maxLifespan === 235 + 15, "Expected success upgrade & reset");

// 5c. Root cleanse failure & success check
player = makeImmortalPlayer();
player.inImmortalPhase = true;
player.immortalStage = 0;
player.bodyTierIndex = 0;
player.rootTierIndex = 4; // next = 5 (混沌道胎靈根, base 0.26, cost 480000)
player.qi = 2000000;
player.maxLifespan = 260;
Math.random = () => 0.99;
attemptRootCleanse();
Math.random = origRandom;
assert(player.rootTierIndex === 4 && player.maxLifespan === 255 && player.rootCleanseFailStreak === 1 && hasArtifact("taixu_armor"), "Root cleanse immortal fail mismatch");
assert(getRootCleanseRate() === 0.34, "Expected 0.26 + 0.08 = 0.34, got " + getRootCleanseRate());
Math.random = () => 0.01;
attemptRootCleanse();
Math.random = origRandom;
assert(player.rootTierIndex === 5 && player.rootCleanseFailStreak === 0, "Root cleanse success upgrade mismatch");
report.temperAndRootMechanics = true;

// 6. Event bonus integration check via imm_body_05 & imm_root_03
resetUi();
player = makeImmortalPlayer();
player.bodyTierIndex = 0;
player.rootTierIndex = 0;
player.immortalStage = 0;
triggerImmortalStoryEvent({ forceEventId: "imm_body_05" });
document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("淬體靈韻")).click();
assert(Math.abs(player.bodyTemperBonus - 0.15) < 1e-6 && getBodyTemperRate() === 0.92, "Expected bodyTemperBonus +15% capped at 0.92");

resetUi();
triggerImmortalStoryEvent({ forceEventId: "imm_root_03" });
document.getElementById("ev-modal-choices").children.find(b => b.innerHTML.includes("洗髓靈韻")).click();
assert(Math.abs(player.rootCleanseBonus - 0.15) < 1e-6 && getRootCleanseRate() === 0.92, "Expected rootCleanseBonus +15% capped at 0.92");
report.eventBonusIntegration = true;

// 7. Epilogue monument root tier bugfix + scriptureUses >= 50 log silencing
player = makeImmortalPlayer();
player.rootTierIndex = 4; // 無垢仙靈根
player.bodyTierIndex = 4; // 太虛不滅軀
const mData = buildEpilogueMonumentData("壽終正寢", [{ name: "長生久視", quote: "test" }]);
assert(mData.uniqueCards[0].sub.includes("無垢仙靈根"), "Monument bugfix failed: expected 無垢仙靈根, got " + JSON.stringify(mData.uniqueCards[0]));

resetUi();
player = makeImmortalPlayer();
player.inImmortalPhase = true;
player.age = 200;
player.maxLifespan = 500;
player.scriptureUses = 55;
Math.random = () => 0.99; // trigger microPool instead of modal
tickImmortalYear();
Math.random = origRandom;
assert(!document.getElementById("log-container").innerHTML.includes("洞天道韻") && player.scriptureUses > 55, "Expected 洞天道韻 log suppressed when scriptureUses>=50");

resetUi();
player = makeImmortalPlayer();
player.inImmortalPhase = false;
player.isImmortalUnlocked = true;
player.age = 80;
player.month = 12;
player.maxLifespan = 120;
player.scriptureUses = 60;
Math.random = () => 0.99;
tickMortalMonth();
Math.random = origRandom;
assert(!document.getElementById("log-container").innerHTML.includes("歲末靈機") && player.scriptureUses > 60, "Expected 歲末靈機 log suppressed when scriptureUses>=50");
report.monumentAndScriptureLogFixes = true;

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
