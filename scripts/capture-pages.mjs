#!/usr/bin/env node
/** Capture planned public routes (Lusion, plus brand homepages discovered through the Refero index),
 * including virtual scroll. No site code/assets are copied.
 * node scripts/capture-pages.mjs [--id lusion-home] [--group refero] [--force] [--mobile]
 * Requires Node 22+, Chrome, ffmpeg. Sources, failures and limitations stay in each record.
 */
import { readFile, writeFile, mkdir, mkdtemp, rm, access } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launchBrowser, pause } from './lib/browser.mjs';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const args = process.argv.slice(2);
const option = name => args.includes(name) ? args[args.indexOf(name) + 1] : undefined;
const mobile = args.includes('--mobile');
const viewport = mobile ? { width: 390, height: 844, deviceScaleFactor: 1, mobile: true }
  : { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false };
const plan = JSON.parse(await readFile(join(ROOT, 'data/capture-plan.json'), 'utf8'));
const selected = plan.items.filter(item => (!option('--id') || item.id === option('--id')) && (!args.includes('--only-live') || item.id.startsWith('live-')) && (!args.includes('--only-labs') || item.id.startsWith('labs-')) && (!args.includes('--only-projects') || item.id.startsWith('project-')) && (!option('--group') || (item.group || 'lusion') === option('--group')));
if (!selected.length) throw new Error('No matching capture ID');
const policy = new Map();

async function allowed(url) {
  const parsed = new URL(url);
  // the plan itself is the allowlist: only hosts that a reviewed plan entry names can be captured
  if (!plan.items.some(item => new URL(item.url).hostname === parsed.hostname)) throw new Error('Capture host is not in the source allowlist');
  if (!policy.has(parsed.origin)) {
    const response = await fetch(`${parsed.origin}/robots.txt`, { signal: AbortSignal.timeout(20000) });
    if (![200, 404].includes(response.status)) throw new Error(`robots.txt returned ${response.status}; stopping`);
    const body = await response.text();
    const groups = [];
    let group = { agents: [], rules: [] };
    for (const line of body.split('\n')) {
      const match = line.replace(/#.*/, '').match(/^\s*(user-agent|allow|disallow)\s*:\s*(.*?)\s*$/i);
      if (!match) continue;
      const [, key, value] = match;
      if (key.toLowerCase() === 'user-agent') {
        if (group.rules.length) { groups.push(group); group = { agents: [], rules: [] }; }
        group.agents.push(value.toLowerCase());
      } else group.rules.push({ allow: key.toLowerCase() === 'allow', path: value });
    }
    groups.push(group);
    // the strictest applicable AI-crawler group wins: any ClaudeBot / anthropic-ai / GPTBot rule applies
    const specific = groups.filter(g => g.agents.some(a => ['claudebot', 'anthropic-ai', 'claude-web', 'gptbot'].includes(a)));
    policy.set(parsed.origin, { url: `${parsed.origin}/robots.txt`, checkedAt: new Date().toISOString(),
      rules: (specific.length ? specific : groups.filter(g => g.agents.includes('*'))).flatMap(g => g.rules),
      status: response.status, htmlFallback: /^\s*<!doctype|^\s*<html/i.test(body) });
  }
  const record = policy.get(parsed.origin);
  const matching = record.rules.filter(rule => rule.path && parsed.pathname.startsWith(rule.path))
    .sort((a, b) => b.path.length - a.path.length || Number(b.allow) - Number(a.allow));
  if (matching.length && !matching[0].allow) throw new Error('robots.txt disallows this route for AI crawlers');
  return record;
}

// DOM structure and style facts, rather than a copy of page prose or compiled JS.
const inspect = `(() => {
  const rect = e => { const r=e.getBoundingClientRect(); return {x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)}; };
  const style = e => { const s=getComputedStyle(e); return {fontFamily:s.fontFamily,fontSize:s.fontSize,lineHeight:s.lineHeight,fontWeight:s.fontWeight,color:s.color,backgroundColor:s.backgroundColor,transform:s.transform,position:s.position}; };
  const page=document.querySelector('#page-container-inner')||document.querySelector('#detail-content')||document.querySelector('main')||document.body;
  const sections=[...page.children].flatMap(e => e.children.length && /^(home|about|project|projects)$/.test(e.id) ? [...e.children] : [e]);
  return {url:location.href,title:document.title,documentHeight:document.documentElement.scrollHeight,
    contentHeight:Math.round(Math.max(page.getBoundingClientRect().height,page.scrollHeight,document.querySelector('#page-container')?.getBoundingClientRect().height||0,document.documentElement.scrollHeight)),
    contentTop:Math.round(page.getBoundingClientRect().top),
    scrollY,ready:document.documentElement.className,bodyStyle:style(document.body),
    pageTransform:getComputedStyle(page).transform,
    sections:sections.filter(e=>e.id).map(e=>({id:e.id,tag:e.tagName,rect:rect(e),style:style(e)})),
    typography:[...document.querySelectorAll('h1,h2,h3,h4,h5')].slice(0,24).map(e=>({tag:e.tagName,id:e.id,characters:e.textContent.trim().length,rect:rect(e),style:style(e)})),
    canvases:[...document.querySelectorAll('canvas')].map(e=>({id:e.id,width:e.width,height:e.height,rect:rect(e)})),
    links:[...document.querySelectorAll('a[href]')].map(e=>e.href).filter(u=>/^https?:/.test(u)),
    media:[...document.querySelectorAll('video,img,source,iframe')].map(e=>({tag:e.tagName,url:e.currentSrc||e.src||'',poster:e.poster||'',width:e.videoWidth||e.naturalWidth||0,height:e.videoHeight||e.naturalHeight||0})).filter(e=>e.url),
    animations:document.getAnimations().slice(0,40).map(a=>({type:a.constructor.name,playState:a.playState,duration:a.effect?.getTiming().duration,iterations:String(a.effect?.getTiming().iterations)})),
    loadingOverlays:[...document.querySelectorAll('#overlay--preloader,#preloader,#loader,.loader')].filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.height>20&&r.y<innerHeight&&r.bottom>0&&r.x<innerWidth&&r.right>0&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)>.05}).map(e=>({id:e.id,classes:String(e.className),rect:rect(e)})),
    brokenImages:[...document.images].filter(e=>e.currentSrc&&e.complete&&e.naturalWidth===0).map(e=>({url:e.currentSrc,rect:rect(e)})),
    reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches};
})()`;

let currentSite = 'lusion.co';
const siteOf = host => host.replace(/^www\./, '').split('.').slice(-2).join('.');
const sameSite = host => (currentSite === 'lusion.co' && host === 'lusion.dev') || host === currentSite || host.endsWith('.' + currentSite);
const RIGHTS = {
  lusion: 'Reference screenshots and recordings of Lusion work; original rights retained. No reusable asset licence granted.',
  refero: 'Reference screenshots and recordings of a public brand homepage discovered through the Refero Styles index; the site owner retains all rights. No reusable asset licence granted.',
};
const browser = await launchBrowser();
const responseMap = new Map();
let runtimeErrors = [];
browser.listeners.add(message => {
  if (message.method === 'Network.responseReceived') {
    const r = message.params.response;
    try {
      const u = new URL(r.url);
      // Exclude analytics, user-specific requests and all URL query parameters.
      if (sameSite(u.hostname)) {
        u.search = ''; u.hash = '';
        responseMap.set(u.href, { url: u.href, status: r.status, mimeType: r.mimeType, type: message.params.type });
      }
    } catch { /* non-HTTP browser resource */ }
  }
  if (message.method === 'Runtime.exceptionThrown') runtimeErrors.push(message.params.exceptionDetails.text);
});

try {
  for (const item of selected) {
    const id = item.id + (mobile ? '-mobile' : '');
    const group = item.group || 'lusion';
    currentSite = siteOf(new URL(item.url).hostname);
    const folder = join(ROOT, 'captures', group, id);
    const recordPath = join(folder, 'page.json');
    try {
      await access(recordPath);
      const previous = JSON.parse(await readFile(recordPath,'utf8'));
      if (!args.includes('--force') && previous.status === 'captured' && (previous.scroll?.coverage >= .9 || previous.scroll?.mode === 'scene-sequence') && previous.captureAlgorithm === 2) { console.log(`skip ${id}`); continue; }
    } catch { /* first capture or incomplete record */ }
    await mkdir(folder, { recursive: true });
    let robots;
    try { robots = await allowed(item.url); }
    catch (error) {
      const denied = {version:1,group,id,name:item.name,url:item.url,source:item.source,kind:item.kind,capturedAt:new Date().toISOString(),viewport,
        status:'failed',error:error.message,rights:'All source work retains its original rights.',limitations:['No page capture: source access or robots check failed.'],checkpoints:[],resources:[],files:[]};
      await writeFile(recordPath,JSON.stringify(denied,null,2)+'\n');
      console.error(`not captured ${id}: ${error.message}`);
      continue;
    }
    const framesFolder = await mkdtemp(join(tmpdir(), 'frontend-frames-'));
    responseMap.clear(); runtimeErrors = [];
    const record = { version: 1, captureAlgorithm:2, id, name: item.name, url: item.url, source: item.source,
      kind: item.kind, capturedAt: new Date().toISOString(), viewport, robots,
      group, rights: RIGHTS[group] || RIGHTS.refero,
      status: 'captured', limitations: ['A recorded browser traversal, not an offline copy of the site.',
        'Shader source, models, textures and original media are inventoried by URL only.',
        'Audio is muted. Scroll checkpoints do not enumerate every possible interaction.',
        'A canvas does not by itself prove Three.js or any particular rendering technique.',
        ...(group === 'refero' ? ['Cookie/consent banners were left untouched (nothing accepted), so they may cover part of a checkpoint.'] : [])],
      checkpoints: [], resources: [], files: [] };
    try {
      await browser.send('Emulation.setDeviceMetricsOverride', viewport);
      await browser.send('Page.navigate', { url: item.url });
      await pause(item.id === 'lusion-home' ? 11000 : group === 'refero' ? 5000 : 6000);
      for (let i = 0; i < 60; i++) {
        if (await browser.evaluate(`document.readyState==='complete' && !document.documentElement.className.includes('is-loading') && ![...document.querySelectorAll('#overlay--preloader,#preloader,.loader')].some(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return r.height>20&&r.y<innerHeight&&r.bottom>0&&r.x<innerWidth&&r.right>0&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)>.05})`)) break;
        await pause(500);
      }
      const initial = await browser.evaluate(inspect);
      record.initial = initial;
      if (!initial.title || /404|not found|access denied/i.test(initial.title)) record.status = 'needs-review';
      const maxTravel = Math.max(0, initial.contentHeight - viewport.height - 160);
      const sceneSequence = maxTravel === 0 && initial.canvases.some(c=>c.rect.height>viewport.height*.6) && initial.links.length>0;
      record.scroll = { mode: sceneSequence ? 'scene-sequence' : initial.contentHeight > initial.documentHeight + 500 ? 'virtual' : 'native', requestedTravel: maxTravel };
      const totalFrames = item.id === 'lusion-home' ? 120 : 24;
      const wheelsPerFrame = Math.max(4,Math.min(12,Math.ceil(maxTravel/(totalFrames-7)/220)));
      const frameTimes = [];
      const checkpointIndices = new Set([0, ...[.2,.4,.6,.8,1].map(p => Math.round(p * (totalFrames-1)))]);
      for (let i = 0; i < totalFrames; i++) {
        const start = Date.now();
        if (i > 5 && sceneSequence) {
          await browser.send('Input.dispatchMouseEvent',{type:'mouseWheel',x:Math.round(viewport.width*.55),y:Math.round(viewport.height*.65),deltaX:0,deltaY:viewport.height*.45});
        } else if (i > 5 && maxTravel) {
          const currentTop = await browser.evaluate(`(document.querySelector('#page-container-inner')||document.querySelector('#detail-content')||document.querySelector('main')||document.body).getBoundingClientRect().top`);
          const actualTravel = record.scroll.mode === 'virtual' ? initial.contentTop-currentTop : await browser.evaluate('scrollY');
          const desiredTravel = maxTravel * Math.min(1,(i-5)/(totalFrames-8));
          // Read actual content movement: wheel input can be scaled/damped by the site.
          for (let wheel = 0; wheel < wheelsPerFrame; wheel++) {
            await browser.send('Input.dispatchMouseEvent', { type:'mouseWheel', x:Math.round(viewport.width*.55), y:Math.round(viewport.height*.65), deltaX:0, deltaY:Math.max(0,desiredTravel-actualTravel)*1.8/wheelsPerFrame });
            await pause(30);
          }
        }
        await browser.send('Input.dispatchMouseEvent', { type:'mouseMoved', x:Math.round(viewport.width*(.5+Math.sin(i*.19)*.22)), y:Math.round(viewport.height*.42) });
        await pause(100);
        const shot = await browser.send('Page.captureScreenshot', { format:'jpeg', quality:72, captureBeyondViewport:false });
        const bytes = Buffer.from(shot.data, 'base64');
        const frameName = `frame-${String(i).padStart(4,'0')}.jpg`;
        await writeFile(join(framesFolder,frameName),bytes);
        frameTimes.push(Date.now());
        if (checkpointIndices.has(i)) {
          const filename = `checkpoint-${String(record.checkpoints.length).padStart(2,'0')}.jpg`;
          await writeFile(join(folder, filename), bytes);
          record.checkpoints.push({ file: filename, frame:i, elapsedMs:frameTimes[i]-frameTimes[0], requestedProgress:Math.round(i/(totalFrames-1)*100)/100,
            state: await browser.evaluate(`({url:location.href,scrollY,contentTop:Math.round((document.querySelector('#page-container-inner')||document.querySelector('#detail-content')||document.querySelector('main')||document.body).getBoundingClientRect().top),pageTransform:getComputedStyle(document.querySelector('#page-container')||document.body).transform,visibleIds:[...document.querySelectorAll('[id]')].filter(e=>{const r=e.getBoundingClientRect();return r.height>100&&r.y<innerHeight&&r.bottom>0}).map(e=>e.id).slice(0,45)})`) });
        }
        await pause(Math.max(0, 166-(Date.now()-start)));
      }
      record.final = await browser.evaluate(inspect);
      if (!record.final.url.startsWith('https://') || /(?:^|\s)(offline|not-supported)(?:\s|$)/.test(record.final.ready)) {
        record.status = 'needs-review';
        record.limitations.push('The browser displayed an offline/error or unsupported state; this recording is not evidence of a working source page.');
      }
      if (!record.final.typography.length && !record.final.links.length) {
        record.status = 'needs-review';
        record.limitations.push('No page headings or links were present after capture; the page may be incomplete or a standalone canvas experience. Inspect it before using this reference.');
      }
      if (record.final.loadingOverlays.length) {
        record.status = 'needs-review';
        record.limitations.push('A loading overlay remained visible at the end; the entered experience is not verified.');
      }
      if (record.final.brokenImages.some(image=>image.rect.width>100&&image.rect.height>100)) {
        record.status = 'needs-review';
        record.limitations.push('At least one content image failed to load; inspect brokenImages before using the reference.');
      }
      record.scroll.actualTravel = record.scroll.mode === 'virtual' ? initial.contentTop-record.final.contentTop : record.final.scrollY;
      record.scroll.coverage = maxTravel ? Math.min(1,Math.round(record.scroll.actualTravel/maxTravel*1000)/1000) : 1;
      if (sceneSequence) {
        record.scroll.coverage = null;
        record.scroll.actualTravel = null;
        record.limitations.push('Fixed-canvas scene sequence: wheel input was sampled, but complete scene coverage cannot be measured from document geometry.');
      }
      if (record.scroll.coverage !== null && record.scroll.coverage < .9) {
        record.status = 'needs-review';
        record.limitations.push('Traversal did not reach 90% of measured content travel; deeper sections need a follow-up capture.');
      }
      if (new URL(record.final.url).pathname.replace(/\/$/,'') !== new URL(item.url).pathname.replace(/\/$/,'')) {
        record.limitations.push(`Traversal navigated to ${record.final.url}; inspect checkpoint URLs before comparing.`);
      }
      record.resources = [...responseMap.values()].sort((a,b)=>a.url.localeCompare(b.url));
      record.runtimeErrors = [...new Set(runtimeErrors)];
      const concat = frameTimes.map((time,i) => `file 'frame-${String(i).padStart(4,'0')}.jpg'\nduration ${i<frameTimes.length-1?(frameTimes[i+1]-time)/1000:1/6}`).join('\n');
      await writeFile(join(framesFolder,'frames.txt'),concat+'\n');
      execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',join(framesFolder,'frames.txt'),
        '-vf',`scale=${Math.min(960,viewport.width)}:-2`,'-vsync','vfr','-c:v','libx264','-crf','27','-pix_fmt','yuv420p','-movflags','+faststart',join(folder,'traversal.mp4')]);
      record.video = { file:'traversal.mp4', durationMs:frameTimes.at(-1)-frameTimes[0], frames:totalFrames, timing:'Variable frame durations from wall-clock capture timestamps; no audio.' };
      record.preview = 'checkpoint-00.jpg';
      for (const filename of [...record.checkpoints.map(c=>c.file),record.video.file]) {
        const bytes = await readFile(join(folder,filename));
        record.files.push({file:filename,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
      }
      console.log(`captured ${id}: ${record.checkpoints.length} checkpoints, ${record.resources.length} resources, ${Math.round(record.video.durationMs/1000)}s video`);
    } catch(error) {
      record.status='failed'; record.error=String(error.message); console.error(`${id}: ${record.error}`);
    } finally {
      await writeFile(recordPath,JSON.stringify(record,null,2)+'\n');
      await rm(framesFolder,{recursive:true,force:true});
    }
    await pause(800);
  }
} finally { await browser.close(); }
