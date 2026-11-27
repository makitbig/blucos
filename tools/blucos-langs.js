// Language picker, the same in every Blucos game (user, 2026-11-27: "1번으로"; Asian languages in CJK order the same day).
// COPIED into each game's www/ by blucos/tools/sync.py. Do not edit in a game repo: edit it in the blucos repo.
//
// The standard:
//   1. A list in a modal (each game draws it in its own style), never a dropdown <select>.
//   2. First row "Automatic (<device language>)": the default, follows the phone's language, can be picked
//      again at any time. Stored as the game already does ('auto' or null). An unsupported device language
//      falls back to English.
//   3. Then the languages in one fixed order: Latin-script languages alphabetical by their own names, then the
//      Asian ones in CJK order (alphabetical by English name: Chinese, Japanese, Korean):
//      Deutsch, English, Español, Français, Italiano, Português, 简体中文, 繁體中文, 日本語, 한국어.
//      A language the game doesn't have is left out (Market Trip: English, 한국어).
//
//   BlucosLangs.list(supported)            -> the game's codes in the standard order
//   BlucosLangs.device(supported)          -> the game code that matches the phone's languages, else 'en'
//   BlucosLangs.name(code)                 -> the language's own name ('한국어', 'Deutsch', ...)
//   BlucosLangs.autoLabel(uiLang, supported) -> 'Automatic (English)', '자동 (한국어)', ... in the UI language
//   BlucosLangs.rows(uiLang, supported, chosen) -> [{ code: 'auto' | code, label, on }], ready to draw:
//      chosen is what the game stored ('auto', null or '' all mean automatic)
//
// supported: the game's own language codes, e.g. ['en', 'ko', 'ja', 'zh-Hans', 'zh-Hant', ...]. A game that
// calls Simplified Chinese 'zh' (Hatch Bingo) can pass 'zh': it sorts and matches like 'zh-Hans'.
'use strict';
window.BlucosLangs = (() => {
  const ORDER = ['de', 'en', 'es', 'fr', 'it', 'pt', 'zh-Hans', 'zh-Hant', 'ja', 'ko'];
  const NAMES = {
    de: 'Deutsch', en: 'English', es: 'Español', fr: 'Français', it: 'Italiano', pt: 'Português',
    ja: '日本語', ko: '한국어', 'zh-Hans': '简体中文', 'zh-Hant': '繁體中文',
  };
  const AUTO = {
    de: 'Automatisch ({name})', en: 'Automatic ({name})', es: 'Automático ({name})', fr: 'Automatique ({name})',
    it: 'Automatico ({name})', pt: 'Automático ({name})', ja: '自動（{name}）', ko: '자동 ({name})',
    'zh-Hans': '自动（{name}）', 'zh-Hant': '自動（{name}）',
  };
  const std = (c) => (c === 'zh' ? 'zh-Hans' : c);   // a game's own code -> the standard one

  function list(supported) {
    return supported.slice().sort((a, b) => ORDER.indexOf(std(a)) - ORDER.indexOf(std(b)));
  }

  // A phone tag like 'pt-BR', 'zh-TW', 'zh-Hant-HK' or 'ko-KR' -> one of the game's codes, or null.
  function match(tag, supported) {
    const t = String(tag || '').toLowerCase(), base = t.split(/[-_]/)[0];
    const has = (c) => supported.find((s) => std(s) === c) || null;
    if (base === 'zh') return /hant|-tw|-hk|-mo|_tw|_hk|_mo/.test(t) ? has('zh-Hant') : has('zh-Hans');
    return has(ORDER.find((c) => c === base));
  }

  function device(supported) {
    const tags = (typeof navigator !== 'undefined' && (navigator.languages || [navigator.language])) || [];
    for (const tag of tags) { const c = match(tag, supported); if (c) return c; }
    return supported.find((s) => s === 'en') || supported[0];
  }

  const name = (code) => NAMES[std(code)] || code;
  const autoLabel = (uiLang, supported) => (AUTO[std(uiLang)] || AUTO.en).replace('{name}', name(device(supported)));

  function rows(uiLang, supported, chosen) {
    const auto = !chosen || chosen === 'auto';
    return [{ code: 'auto', label: autoLabel(uiLang, supported), on: auto },
      ...list(supported).map((c) => ({ code: c, label: name(c), on: !auto && c === chosen }))];
  }

  return { ORDER, list, device, match, name, autoLabel, rows };
})();
