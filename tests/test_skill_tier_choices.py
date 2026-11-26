import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(name):
    with open(os.path.join(ROOT, name), "r", encoding="utf-8") as f:
        return f.read()

def extract_block(js, start_marker, end_marker):
    s = js.index(start_marker)
    e = js.index(end_marker, s)
    return js[s:e]

def main():
    index_html = read("index.html")
    data_js = read("data.js")
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", index_html, flags=re.S | re.I)
    main_js = max(scripts, key=len)

    # Extract actual implementation slices from index.html
    tier_and_skill_helpers = extract_block(
        main_js,
        "function getMasteredSkillsList()",
        "function syncPlayerInjuries()"
    )
    pick_and_personalize = extract_block(
        main_js,
        "function getSkillTierPriority(tier)",
        "// 檢查玩家是否已達成「招式、心法（內功）、輕功（身法）"
    )
    sanhua_helper = extract_block(
        main_js,
        "function getSanHuaZhenpaiStatus(excludeSelfCreated = false)",
        "// 觸發「自創武學」宗師頓悟事件"
    )
    companion_fn = extract_block(
        main_js,
        "function triggerCompanionEncounter(forcedCharId = null)",
        "// 各角色專屬「回眸離別」劇本庫"
    )
    enrich_and_dilemma = extract_block(
        main_js,
        "function enrichCrisisChoices(ev, mappedChoices)",
        "function triggerPatchedMajorEvent"
    )
    open_modal_fn = extract_block(
        main_js,
        "function openEventModal(title, tag, desc, rawChoices)",
        "const HOT_STORAGE_KEY"
    )

    test_harness = f"""
const window = {{}};
const console = {{ log(){{}}, warn(){{}}, error(){{}} }};
const elements = {{}};
function makeEl(id) {{
  if (!elements[id]) {{
    elements[id] = {{
      id,
      textContent: "",
      _innerHTML: "",
      children: [],
      get innerHTML() {{ return this._innerHTML; }},
      set innerHTML(v) {{
        this._innerHTML = v;
        if (v === "") this.children = [];
      }},
      classList: {{ add(){{}}, remove(){{}}, contains(){{ return false; }} }},
      appendChild(c) {{ this.children.push(c); }}
    }};
  }}
  return elements[id];
}}
const document = {{
  getElementById(id) {{ return makeEl(id); }},
  createElement(tag) {{
    return {{
      tagName: tag,
      className: "",
      disabled: false,
      innerHTML: "",
      listeners: {{}},
      addEventListener(ev, fn) {{ this.listeners[ev] = fn; }}
    }};
  }}
}};
function setTimeout() {{ return 1; }}
function clearTimeout() {{}}
let isAutoFate = false;
let userManualPaused = false;
function setPauseState() {{}}
function updateAllUI() {{}}
function renderBondsTab() {{}}
function addLog(msg) {{ logs.push(msg); }}
function modifyStats() {{ return ["武力+2"]; }}
function unlockBaixiao() {{}}
function unlockAchievement() {{}}
function assignMountLifespan() {{}}
function getActiveMounts() {{ return []; }}
function addLightInjury() {{}}
function hasForesight() {{ return true; }}
function buildSwornOrCloseReunionScenario() {{ return null; }}
function buildContextAwarePasserbyOptions() {{ return []; }}
let logs = [];
let player = null;

{data_js}

const DB = window.GAME_DATA;
const FALLBACK_DATA = window.GAME_DATA;
const CHARACTERS = DB.CHARACTERS;
const INTIMACY_LEVELS = ["點頭之交", "結伴同行", "友好往來", "肝膽相照", "親密無間", "生死至交"];
const BODY_TIERS = DB.BODY_TIERS || [{{name:"凡胎肉身"}}, {{name:"銅皮鐵骨"}}, {{name:"百脈通玄"}}];
const ROOT_TIERS = DB.ROOT_TIERS || [{{name:"凡俗靈根"}}];

{tier_and_skill_helpers}
{pick_and_personalize}
{sanhua_helper}
{companion_fn}
{enrich_and_dilemma}
{open_modal_fn}

function assert(cond, msg) {{
  if (!cond) throw new Error("ASSERT FAILED: " + msg);
}}

// --- Test 1: Helper filtering & tiers ---
player = {{
  age: 35,
  inImmortalPhase: false,
  stats: {{ wu: 95, de: 60, ming: 70, qing: 80, cai: 200 }},
  badges: ["因果窺探"],
  skills: [
    {{ name: "草上飛", type: "輕功", weapon: "身法", tier: "一般" }},
    {{ name: "虎嘯拳", type: "招式", weapon: "拳掌", tier: "進階" }},
    {{ name: "梯雲縱", type: "輕功", weapon: "身法", tier: "上乘" }},
    {{ name: "羅剎修羅槍", type: "招式", weapon: "槍棍", tier: "上乘" }},
    {{ name: "霸刀三式", type: "招式", weapon: "刀法", tier: "鎮派" }},
    {{ name: "萬刃歸元", type: "招式", weapon: "劍法", tier: "曠世" }},
    {{ name: "無相太虛訣", type: "內功", weapon: "心法", tier: "曠世" }},
    {{ name: "踏月留香縮地步", type: "輕功", weapon: "身法", tier: "自創曠世", isSelfCreated: true }},
    {{ name: "太虛劍典（未悟）", type: "招式", weapon: "劍法", tier: "鎮派", pendingEnlightenment: true }}
  ],
  bonds: [
    {{ id: "qiao_feng", name: "蕭烈山", intimacyIndex: 2, tacit: 2, usedEncounterIndices: [] }}
  ]
}};

const t3Light = getMasteredSkillsByMinTier(3, "輕功");
assert(t3Light.length === 2 && t3Light.some(s => s.name === "梯雲縱") && t3Light.some(s => s.name === "踏月留香縮地步"),
  "Expected 2 mastered tier>=3 light skills, got " + JSON.stringify(t3Light.map(s => s.name)));

const t4Atk = getMasteredSkillsByMinTier(4, "招式");
assert(t4Atk.length === 2 && t4Atk.some(s => s.name === "霸刀三式") && t4Atk.some(s => s.name === "萬刃歸元"),
  "Expected 2 mastered tier>=4 attack skills (excluding pendingEnlightenment and 上乘), got " + JSON.stringify(t4Atk.map(s => s.name)));

// --- Test 2: Companion Encounter qf_s3_1 with high-tier skills ---
const qf = CHARACTERS.find(c => c.id === "qiao_feng");
const qfS31Idx = qf.encounters.findIndex(e => e.id === "qf_s3_1");
assert(qfS31Idx >= 0, "qf_s3_1 not found");
player.bonds[0].usedEncounterIndices = qf.encounters.map((_, i) => i).filter(i => i !== qfS31Idx);
triggerCompanionEncounter("qiao_feng");
const btnsHigh = elements["ev-modal-choices"].children;
assert(btnsHigh.length === 3, "Expected 3 options for qf_s3_1 (no redundant canned 鎮派), got " + btnsHigh.length);
const highHtmls = btnsHigh.map(b => ({{ disabled: b.disabled, html: b.innerHTML }}));
assert(highHtmls.every(h => !h.disabled), "Expected all options enabled for skilled player, got: " + JSON.stringify(highHtmls));
assert(highHtmls.some(h => /✨ 【(上乘|自創曠世)輕功 · 《(梯雲縱|踏月留香縮地步)》】/.test(h.html) && h.html.includes("搶先破窗而入")),
  "Expected 上乘輕功 badge + skill name on破窗 option: " + JSON.stringify(highHtmls));

// --- Test 3: Companion Encounter qf_s3_1 with ONLY tier-1/2 skills + genuinely locked skills (locked visibility test) ---
player.skills = [
  {{ name: "草上飛", type: "輕功", weapon: "身法", tier: "一般" }},
  {{ name: "虎嘯拳", type: "招式", weapon: "拳掌", tier: "進階" }},
  {{ name: "未悟神功", type: "招式", weapon: "劍法", tier: "曠世", pendingEnlightenment: true, reqWu: 150, reqAge: 45 }},
  {{ name: "太古仙經", type: "內功", weapon: "心法", tier: "仙道經典", isLockedScripture: true }}
];
player.bonds[0].usedEncounterIndices = qf.encounters.map((_, i) => i).filter(i => i !== qfS31Idx);
triggerCompanionEncounter("qiao_feng");
const btnsLow = elements["ev-modal-choices"].children;
const lowHtmls = btnsLow.map(b => ({{ disabled: b.disabled, html: b.innerHTML }}));
const lockedLight = lowHtmls.find(h => h.html.includes("搶先破窗而入"));
assert(lockedLight && lockedLight.disabled && lockedLight.html.includes("🔒 【需上乘以上輕功】") && !lockedLight.html.includes("草上飛") && !lockedLight.html.includes("《輕功名》"),
  "Low-tier player must see locked 上乘輕功 without grass-step leak: " + JSON.stringify(lockedLight));
const enabledNormal = lowHtmls.filter(h => !h.disabled);
assert(enabledNormal.length === 2, "Expected 2 normal choices unlocked when 上乘輕功 is locked, got " + enabledNormal.length);

// --- Test 4: Player has ONLY 上乘 (no 鎮派) ---
player.skills.push({{ name: "梯雲縱", type: "輕功", weapon: "身法", tier: "上乘" }});
player.bonds[0].usedEncounterIndices = qf.encounters.map((_, i) => i).filter(i => i !== qfS31Idx);
triggerCompanionEncounter("qiao_feng");
const midHtmls = elements["ev-modal-choices"].children.map(b => ({{ disabled: b.disabled, html: b.innerHTML }}));
const midLight = midHtmls.find(h => h.html.includes("搶先破窗而入"));
assert(midLight && !midLight.disabled && midLight.html.includes("《梯雲縱》"),
  "上乘 player should unlock 梯雲縱 option: " + JSON.stringify(midLight));

// --- Test 5: Crisis enrichment + intrigue framing guard ---
const framingEv = {{ title: "皇綱失竊疑雲", desc: "官府誣指你與劫案有關" }};
const framingChoices = [{{ text: "據理力爭", onSelect(){{}} }}];
enrichCrisisChoices(framingEv, framingChoices);
assert(framingChoices.some(c => c.reqSkillTier === "上乘" && c.reqSkillCategory === "輕功"),
  "Framing event should add 上乘輕功 stealth tracking choice");
assert(!framingChoices.some(c => c.reqSkillTier === "鎮派"),
  "Framing event should NOT add violent 鎮派 combat choice");

const combatEv = {{ title: "夜半客棧伏擊", desc: "數十名黑衣殺手破窗圍攻" }};
const combatChoices = [{{ text: "奮力突圍", onSelect(){{}} }}, {{ text: "報出師承震懾", onSelect(){{}} }}];
enrichCrisisChoices(combatEv, combatChoices);
openEventModal("夜半客棧伏擊", "🌪️ 江湖風波", combatEv.desc, combatChoices);
const combatHtmls = elements["ev-modal-choices"].children.map(b => ({{ disabled: b.disabled, html: b.innerHTML }}));
assert(combatHtmls.some(h => h.disabled && h.html.includes("🔒 【需上乘以上招式】")),
  "Combat crisis should lock 上乘招式 when player only has light skill: " + JSON.stringify(combatHtmls));
assert(combatHtmls.some(h => h.disabled && h.html.includes("🔒 【需鎮派以上招式】")),
  "Combat crisis should lock 鎮派招式 for mid player: " + JSON.stringify(combatHtmls));

// Give mid player 羅剎修羅槍 (上乘 · 槍棍) and test combat crisis 上乘招式 -> 槍罡 substitution
player.skills = [{{ name: "羅剎修羅槍", type: "招式", weapon: "槍棍", tier: "上乘" }}];
openEventModal("夜半客棧伏擊", "🌪️ 江湖風波", combatEv.desc, combatChoices);
const spearHtmls = elements["ev-modal-choices"].children.map(b => ({{ disabled: b.disabled, html: b.innerHTML }}));
assert(spearHtmls.some(h => !h.disabled && h.html.includes("✨ 【上乘招式 · 《羅剎修羅槍》】") && h.html.includes("槍罡") && !h.html.includes("劍氣")),
  "Expected 上乘招式 & 槍罡 substitution for spear skill 羅剎修羅槍: " + JSON.stringify(spearHtmls));

// --- Test 6: triggerDynamicDilemma forwarding reqSkillTier / reqSkillCategory ---
DB.EVENTS.dynamic_dilemmas = [{{
  id: "test_zhenpai_internal",
  title: "寒淵閉氣試煉",
  desc: "玄冰古洞陰寒透骨",
  choices: [
    {{ text: "生火取暖緩緩前行", stats: {{ ming: 1 }}, result: "平安渡過" }},
    {{ text: "催動《內功名》護住丹田直穿冰窟", reqSkillTier: "鎮派", reqSkillCategory: "內功", stats: {{ wu: 3 }}, result: "功力精進" }}
  ]
}}];
DB.EVENTS.major_events = [];
player.usedEvents = new Set();
player.skills = [{{ name: "無相太虛訣", type: "內功", weapon: "心法", tier: "曠世" }}];
assert(triggerDynamicDilemma(true) === true, "triggerDynamicDilemma failed");
const dilemmaHtmls = elements["ev-modal-choices"].children.map(b => ({{ disabled: b.disabled, html: b.innerHTML }}));
assert(dilemmaHtmls.some(h => !h.disabled && h.html.includes("🔥 【曠世內功 · 《無相太虛訣》】") && h.html.includes("催動《無相太虛訣》")),
  "Expected triggerDynamicDilemma to forward reqSkillTier & substitute 無相太虛訣: " + JSON.stringify(dilemmaHtmls));

JSON.stringify({{
  ok: true,
  highSample: highHtmls.map(h => h.html),
  lowLockedLight: lockedLight.html,
  spearCombatSample: spearHtmls.find(h => h.html.includes("《羅剎修羅槍》")).html,
  dilemmaSample: dilemmaHtmls.find(h => h.html.includes("《無相太虛訣》")).html
}});
"""
    res = subprocess.run(
        ["/usr/bin/osascript", "-l", "JavaScript", "-"],
        input=test_harness,
        text=True,
        capture_output=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"JXA runtime test failed rc={res.returncode}: {res.stderr}")
    print(res.stdout.strip())

if __name__ == "__main__":
    main()
