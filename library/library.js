/* All text is rendered through DOM APIs. Catalogs contain external, untrusted metadata. */
'use strict';
const files = { captures:'landing-pages.json', styles:'refero-styles.json', lusion:'lusion.json',
  motion:'motion-examples.json', transitions:'transitions.json', godly:'godly.json', fonts:'envato-award-fonts.json',
  'design-md':'design-md.json',codrops:'codrops-webgl.json','media-resources':'video-resources.json' };
const labels = { captures:'Captured page',styles:'Refero style',lusion:'Lusion index',motion:'Motion example',transitions:'UI transition',godly:'Godly reference',fonts:'Font',
  'design-md':'DESIGN.md analysis',codrops:'Codrops reference','media-resources':'Media & design resource' };
const grid = document.querySelector('#grid');
const status = document.querySelector('#status');
const search = document.querySelector('#search');
const collection = document.querySelector('#collection');
const theme = document.querySelector('#theme');
const more = document.querySelector('#more');
let records = [];
let shown = 36;
let ready = false;
const params = new URLSearchParams(location.search);
search.value = params.get('q') || '';
if (params.get('type') === 'all' || files[params.get('type')]) collection.value = params.get('type');
if (['dark','light','mixed'].includes(params.get('theme'))) theme.value = params.get('theme');

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function safeUrl(value) {
  if (typeof value !== 'string' || !value) return null;
  if (value.startsWith('//')) return null;
  try {
    const url = new URL(value, new URL('../', location.href));
    return ['http:','https:'].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}

function link(text, value) {
  const anchor = node('a', '', text);
  anchor.href = safeUrl(value) || '#';
  if (new URL(anchor.href).origin !== location.origin) { anchor.target = '_blank'; anchor.rel = 'noopener noreferrer'; }
  return anchor;
}

function placeholder(item) {
  const visual = node('div','visual-placeholder');
  visual.append(node('small','',labels[item.collection]));
  if (item.colors?.length) {
    const palette = node('div','palette');
    for (const color of item.colors.slice(0,5)) {
      const swatch = node('span','swatch');
      if (/^#[a-f\d]{3,8}$/i.test(color.hex)) swatch.style.backgroundColor = color.hex;
      palette.append(swatch);
    }
    visual.append(palette);
  } else visual.append(node('span','placeholder-initial',item.name.slice(0,2).toUpperCase()));
  return visual;
}

function card(item) {
  const article = node('article','card');
  const visual = link('',item.guide || item.localDesignPath || item.url);
  visual.className = 'card-visual';
  visual.setAttribute('aria-label',`View ${item.name}`);
  // Only actual local captures are presented as screenshots. Style cards show factual palettes.
  if (item.collection === 'captures' && safeUrl(item.preview)) {
    const img = node('img'); img.src=safeUrl(item.preview); img.alt=`Captured viewport of ${item.name}`;
    if (item.viewport?.mobile) img.className='mobile-capture';
    img.loading='lazy'; img.decoding='async';
    img.addEventListener('error',()=>img.replaceWith(placeholder(item)),{once:true});
    visual.append(img);
  } else visual.append(placeholder(item));
  const body = node('div','card-body');
  const top = node('div','card-top');
  top.append(node('span','',item.kind || labels[item.collection]));
  top.append(node('span',item.collection==='captures'&&item.status==='captured'?'verified':'',item.collection==='captures'?item.status:item.localDesignPath?'Local analysis':'Link index'));
  body.append(top,node('h2','',item.name));
  const tags = [...(item.tags||[]),item.category,item.theme,...(item.fonts||[])].filter(Boolean).slice(0,5);
  const details=tags.join(' · ') || item.description?.slice(0,110) || labels[item.collection];
  body.append(node('div','tags',(item.viewport?`${item.viewport.width} × ${item.viewport.height} · `:'')+details));
  const links = node('div','card-links');
  if (item.video) links.append(link('Watch motion ↗',item.video));
  if (item.record) links.append(link('Evidence JSON',item.record));
  if (item.localDesignPath) links.append(link('Read DESIGN.md',item.localDesignPath));
  if (item.demo) links.append(link('Live demo ↗',item.demo));
  links.append(link('Source ↗',item.url));
  body.append(links); article.append(visual,body);
  return article;
}

function render() {
  if (!ready) return;
  const words=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const matching=records.filter(item=>(collection.value==='all'||item.collection===collection.value)
    &&(!theme.value||item.theme===theme.value)&&words.every(word=>item.searchText.includes(word)));
  grid.replaceChildren(...matching.slice(0,shown).map(card));
  if (!matching.length) grid.append(node('p','empty','No references match these filters. Try a broader search or another collection.'));
  status.textContent=`${matching.length.toLocaleString()} references · ${Math.min(shown,matching.length).toLocaleString()} shown`;
  more.hidden=shown>=matching.length;
  const query=new URLSearchParams();
  if (search.value) query.set('q',search.value);
  if (collection.value!=='captures') query.set('type',collection.value);
  if (theme.value) query.set('theme',theme.value);
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:''));
}

document.querySelector('#filters').addEventListener('submit',event=>event.preventDefault());
for (const element of [search,collection,theme]) element.addEventListener(element===search?'input':'change',()=>{shown=36;render();});
more.addEventListener('click',()=>{shown+=36;render();});
document.addEventListener('keydown',event=>{
  if (event.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) { event.preventDefault(); search.focus(); }
});

async function loadCatalogs() {
  const collections=[];
  // Keep local servers and proxy connections responsive; no burst of ten large fetches.
  for (const [kind,file] of Object.entries(files)) {
    const response=await fetch(`../data/${file}`);
    if (!response.ok) throw new Error(`Could not load ${file} (${response.status})`);
    const data=await response.json();
    collections.push(data.items.map(item=>({...item,collection:kind,searchText:JSON.stringify(item).toLowerCase()})));
  }
  records=collections.flat();ready=true;render();
}
loadCatalogs().catch(error=>{
  status.textContent='Collection unavailable';
  const message=document.querySelector('#error');message.hidden=false;
  message.textContent=`${error.message}. Serve the repository with “python3 -m http.server 8000” and open http://localhost:8000/library/.`;
});
