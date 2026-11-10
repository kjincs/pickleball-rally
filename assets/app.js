'use strict';
const $ = s => document.querySelector(s);
const escape = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let config, editions = [], edition, filter = 'All', language = 'en';
const translated = (s,key) => language === 'zh' ? (s[key+'_zh'] || s[key]) : s[key];
const categoriesZH = {'Style':'穿搭与装备','Community':'人物与社群','News':'重要新闻','Trends':'新兴趋势','Paddle knowledge':'球拍知识'};
const category = s => language === 'zh' ? categoriesZH[s.category] : s.category;
const sourceTypes = {official:['Official source','官方来源'],reporting:['Reporting','媒体报道'],brand:['Brand perspective','品牌观点'],forum:['Community perspective · forum','社区观点 · 论坛'],social:['Community perspective · social','社区观点 · 社交媒体']};
const sourceContext = s => { const type = sourceTypes[s.source_type] || sourceTypes.reporting; return escape(type[language === 'zh' ? 1 : 0]) + ' · ' + (s.source_language === 'zh' ? '中文原文' : 'English original') + ((language === 'zh' ? s.source_language !== 'zh' : s.source_language === 'zh') ? (language === 'zh' ? ' · 译文摘要' : ' · Translated summary') : ''); };

const validRepo = value => /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(value || '');
const safeURL = value => { try { const u = new URL(value); return u.protocol === 'https:' ? u.href : '#process'; } catch { return '#process'; } };
function reviewURL(story) {
  if (!validRepo(config.repository)) return '#process';
  const params = new URLSearchParams({template:'review.yml', title:`[Review] ${edition.id} / ${story ? story.id : 'edition'}`, edition:edition.id, story:story ? story.id : 'edition'});
  return `https://github.com/${config.repository}/issues/new?${params}`;
}
function link(url, label, cls = 'textbtn') { return `<a class="${cls}" href="${escape(safeURL(url))}" target="_blank" rel="noopener noreferrer">${escape(label)}</a>`; }
function visual(s) { return art(s.category === 'Style' ? 'style' : s.category === 'Community' ? 'people' : s.category === 'Trends' ? 'trend' : 'club'); }
function metadata(s) { return `${escape(s.source)} · ${s.published_at ? escape(s.published_at) : (language === 'zh' ? '发布日期未注明' : 'Publication date not stated')} · ${s.kind === 'evergreen' ? (language === 'zh' ? '背景阅读' : 'EVERGREEN') : (language === 'zh' ? '新闻' : 'NEWS')}`; }
function actions(s) { return `<div class="actions">${link(s.url, language === 'zh' ? '阅读原文 ↗' : 'Read the original ↗')}${link(reviewURL(s), language === 'zh' ? '留言反馈 ↗' : 'Leave feedback ↗', 'review-link')}</div>`; }
function matches(s, q) { return (filter === 'All' || s.category === filter) && `${s.title} ${s.summary} ${s.title_zh || ""} ${s.summary_zh || ""} ${s.category} ${s.source}`.toLowerCase().includes(q); }
function renderEdition() {
  $('#edition-meta').textContent = `${edition.stories.length} reads · ${edition.date}`;
  $('#changes').textContent = translated(edition,'feedback_note');
  $('#changes').hidden = !edition.feedback_note;
  $('#review-edition').href = $('#bottom-review').href = reviewURL();
  const s = edition.stories[0];
  $('#hero').innerHTML = s ? `<div class="court">${visual(s)}<span class="artlabel">ORIGINAL RALLY ILLUSTRATION</span></div><div class="feature-copy"><span class="tag">${language === "zh" ? "本期精选" : "THE FEATURE"} · ${escape(category(s))}</span><h2>${escape(translated(s,"title"))}</h2><p>${escape(translated(s,"summary"))}</p><p class="why">${language === "zh" ? "推荐理由：" : "Why it matters: "}${escape(translated(s,"why"))}</p><div class="meta">${metadata(s)}</div><div class="source-kind">${sourceContext(s)}</div>${actions(s)}</div>` : '<p class="empty">The next edition is on its way.</p>';
  renderCards();
  const last = editions[0];
  $('#notice').textContent = `${edition.seed ? 'FOUNDING EDIT · Source-linked starter collection' : 'THE DAILY EDIT · AI-assisted research'} · ${edition.date}${edition.id !== last.id ? ' · You’re reading a previous edition' : ''}`;
}
function renderCards() {
  const q = $('#search').value.toLowerCase();
  const filtered = filter !== 'All' || q;
  const list = (filtered ? edition.stories : edition.stories.slice(1)).filter(s => matches(s,q));
  $('#stories').innerHTML = list.map(s => `<article class="card"><div class="visual">${visual(s)}</div><span class="tag">${escape(category(s))}</span><h3>${escape(translated(s,"title"))}</h3><p>${escape(translated(s,"summary"))}</p><p class="story-why">${language === "zh" ? "推荐理由：" : "Why it matters: "}${escape(translated(s,"why"))}</p><div class="meta">${metadata(s)}</div><div class="source-kind">${sourceContext(s)}</div>${actions(s)}</article>`).join('') || '<p class="empty">No matching stories. Try another topic or search.</p>';
  $('#hero').hidden = filtered;
}
function renderLibrary() {
  const q = $('#library-search').value.toLowerCase();
  const seen = new Set();
  const list = editions.flatMap(e => e.stories.map(s => ({...s, edition:e.id}))).filter(s => {if(seen.has(s.url)) return false; seen.add(s.url); return `${s.title} ${s.summary} ${s.title_zh || ""} ${s.summary_zh || ""} ${s.category}`.toLowerCase().includes(q);});
  $('#library-count').textContent = `${list.length} source-linked stories across ${editions.length} editions`;
  $('#library-results').innerHTML = list.map(s => `<article class="library-row"><span class="tag">${escape(category(s))}</span><div><h3>${escape(translated(s,"title"))}</h3><p>${escape(translated(s,"summary"))}</p><div class="meta">${metadata(s)}</div><div class="source-kind">${sourceContext(s)}</div><div class="actions">${link(s.url,language === 'zh' ? '阅读原文 ↗' : 'Read the original ↗')}<button class="textbtn" data-edition="${escape(s.edition)}">View its edition ↗</button></div></div></article>`).join('') || '<p class="empty">No stories match your search.</p>';
}
function showPage(page) {
  ['edition','library','process'].forEach(p => $(`#${p}-page`).style.display = p === page ? 'block' : 'none');
  document.querySelectorAll('[data-page]').forEach(b => b.classList.toggle('active', b.dataset.page === page));
  if(page === 'library') renderLibrary();
}
async function loadJSON(path) { const response = await fetch(path, {cache:'no-cache'}); if(!response.ok) throw new Error(`Could not load ${path}`); return response.json(); }
async function init() {
  try {
    config = await loadJSON('config.json');
    const index = await loadJSON('data/index.json');
    editions = await Promise.all(index.editions.map(id => { if(!/^[a-zA-Z0-9_-]+$/.test(id)) throw new Error('Invalid edition ID'); return loadJSON(`data/editions/${id}.json`); }));
    if(!editions.length) throw new Error('No editions available');
    edition = editions[0];
    $('#edition-select').innerHTML = editions.map(e => `<option value="${escape(e.id)}">${escape(e.date)}${e.seed ? ' · Founding edit' : ''}</option>`).join('');
    if(validRepo(config.repository)) {
      $('#all-reviews').href = `https://github.com/${config.repository}/issues?q=${encodeURIComponent('is:issue "[Review]" in:title')}`;
      $('#run-workflow').href = `https://github.com/${config.repository}#daily-publication`;
      $('#setup-note').textContent = 'Reviewing uses your GitHub account. In this pilot, comments from any GitHub user inform the next edition; scores and preferences are optional. Codex prepares each edition on the local computer; GitHub publishes the saved files automatically.';
    } else $('#setup-note').textContent = 'Local preview: set the repository in config.json and deploy to activate GitHub review links. No feedback is submitted from this preview.';
    renderEdition();
    showPage(location.hash === '#library' ? 'library' : location.hash === '#process' ? 'process' : 'edition');
  } catch(error) { $('#notice').textContent = 'The edit could not be loaded. Please refresh to try again.'; $('#hero').innerHTML = '<p class="error">Please serve this folder over HTTP, rather than opening index.html directly. Try: python3 -m http.server 4173</p>'; console.error(error); }
}
$('#language').addEventListener('change', e => { language=e.target.value; $('#hero').lang=language; $('#stories').lang=language; $('#library-results').lang=language; if(edition){renderEdition();renderLibrary();} });
$('#search').addEventListener('input',()=>edition && renderCards());
$('#library-search').addEventListener('input',renderLibrary);
$('#edition-select').addEventListener('change',e => {edition=editions.find(x=>x.id===e.target.value);renderEdition();});
window.addEventListener('hashchange',()=>{if(edition)showPage(location.hash==='#library'?'library':location.hash==='#process'?'process':'edition');});
document.addEventListener('click',e => {
  const page = e.target.closest('[data-page]'); if(page) {location.hash=page.dataset.page;showPage(page.dataset.page);}
  const f=e.target.closest('[data-filter]'); if(f && edition){filter=f.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b===f));renderCards();}
  const ed=e.target.closest('[data-edition]'); if(ed){edition=editions.find(x=>x.id===ed.dataset.edition);$('#edition-select').value=edition.id;filter='All';$('#search').value='';document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b.dataset.filter==='All'));renderEdition();location.hash='edition';showPage('edition');window.scrollTo(0,0);}
});
init();
