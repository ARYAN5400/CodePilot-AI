import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, rm} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {build} from 'esbuild';
import {JSDOM} from 'jsdom';
import React, {act} from 'react';
import {createRoot} from 'react-dom/client';

test('frontend regression suite', async t=>{
 const cache=await mkdtemp(resolve('.frontend-test-'));
 const dom=new JSDOM('<!doctype html><div id="root"></div>',{url:'http://localhost/'});
 const originals=new Map();
 function global(name,value){originals.set(name,Object.getOwnPropertyDescriptor(globalThis,name));Object.defineProperty(globalThis,name,{value,writable:true,configurable:true})}
 global('window',dom.window);global('document',dom.window.document);global('navigator',dom.window.navigator);global('HTMLElement',dom.window.HTMLElement);global('IS_REACT_ACT_ENVIRONMENT',true);global('requestAnimationFrame',fn=>{fn();return 0});
 let topCalls=0,anchorCalls=0;window.scrollTo=()=>topCalls++;dom.window.HTMLElement.prototype.scrollIntoView=()=>anchorCalls++;
 dom.window.HTMLDialogElement.prototype.showModal=function(){this.open=true};dom.window.HTMLDialogElement.prototype.close=function(){this.open=false};
 global('IntersectionObserver',class{observe(){}unobserve(){}disconnect(){}});
 const button=name=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===name);
 const click=async el=>{assert.ok(el,'control exists');await act(async()=>el.click())};
 let root;
 try{
  await build({entryPoints:['src/DebugWorkspace.jsx'],bundle:true,format:'esm',platform:'node',external:['react','react-dom','react-dom/client'],loader:{'.css':'empty'},outfile:cache+'/workspace.mjs'});
  const {default:Workspace}=await import(pathToFileURL(cache+'/workspace.mjs'));
  root=createRoot(document.getElementById('root'));await act(async()=>root.render(React.createElement(Workspace,{onBack:()=>{}})));
  await t.test('empty form cannot submit',()=>assert.equal(button('Analyze with AI →').disabled,true));
  await t.test('practice flow shows honest prepared solution and comparison',async()=>{await click(button('Try JavaScript'));await click(button('Reveal practice solution'));assert.match(document.body.textContent,/Prepared example — not AI analysis/);await click(button('Compare'));assert.match(document.querySelector('[role="tabpanel"]').textContent,/item.price \* item.quantity/);assert.match(document.body.textContent,/Not test-verified/)});
  await t.test('tabs support keyboard navigation',async()=>{const tab=document.getElementById('tab-compare');await act(async()=>tab.dispatchEvent(new window.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true})));assert.equal(document.getElementById('tab-tests').getAttribute('aria-selected'),'true');assert.equal(document.activeElement.id,'tab-tests')});
  await t.test('consent required before provider request',async()=>{await click(button('Analyze with AI →'));assert.match(document.querySelector('[role="alert"]').textContent,/Confirm/)});
  await t.test('API language IDs and structured errors work',async()=>{await click(document.querySelector('input[type="checkbox"]'));let sent;global('fetch',async(url,options)=>{sent=JSON.parse(options.body);return {ok:false,json:async()=>({error:{code:'not_configured',message:'The debugging service is not configured.'}})}});await click(button('Analyze with AI →'));assert.equal(sent.language,'javascript');assert.equal(document.querySelector('[role="alert"]').textContent,'The debugging service is not configured.')});
  await t.test('valid AI response renders proposed code',async()=>{globalThis.fetch=async()=>({ok:true,json:async()=>({summary:'Fix quantity',rootCause:'Quantity ignored',fixedCode:'return price * quantity;',explanation:['Multiply price by quantity.'],suggestedTests:['Check quantity 3.'],verification:'not_run'})});await click(button('Analyze with AI →'));assert.match(document.body.textContent,/Fix quantity/);await click(button('Proposed code'));assert.equal(document.querySelector('[role="tabpanel"] pre').textContent,'return price * quantity;')});
  await t.test('invalid provider result does not crash rendering',async()=>{globalThis.fetch=async()=>({ok:true,json:async()=>({summary:'Bad',fixedCode:'x',rootCause:'x',explanation:[{}],suggestedTests:[],verification:'not_run'})});await click(button('Analyze with AI →'));assert.match(document.querySelector('[role="alert"]').textContent,/incomplete response/)});
  await t.test('clear resets code, issue and result',async()=>{await click(button('Clear'));assert.equal(document.getElementById('source-code').value,'');assert.equal(document.getElementById('bug-issue').value,'');assert.equal(button('Analyze with AI →').disabled,true)});
  await act(async()=>root.unmount());root=null;
  await build({entryPoints:['src/main.jsx'],bundle:true,format:'esm',platform:'node',external:['react','react-dom','react-dom/client'],loader:{'.css':'empty'},outfile:cache+'/main.mjs'});
  await act(async()=>{await import(pathToFileURL(cache+'/main.mjs'))});
  await t.test('landing uses workspace entry instead of unconfigured sign-in',()=>{assert.equal(button('Sign In'),undefined);assert.ok(button('Open workspace'))});
  await t.test('section navigation does not force scroll back to top',async()=>{const before=topCalls;await act(async()=>{window.location.hash='features';window.dispatchEvent(new window.HashChangeEvent('hashchange'));await new Promise(r=>setTimeout(r,5))});assert.equal(topCalls,before)});
  await t.test('workspace entry and back navigation render correct pages',async()=>{await click(button('Open workspace'));await act(async()=>{window.dispatchEvent(new window.HashChangeEvent('hashchange'));await new Promise(r=>setTimeout(r,5))});assert.ok(document.getElementById('source-code'));await click(document.querySelector('.debug-brand'));await act(async()=>{window.dispatchEvent(new window.HashChangeEvent('hashchange'));await new Promise(r=>setTimeout(r,5))});assert.ok(document.getElementById('home'));assert.ok(anchorCalls>0)});
 }finally{if(root)await act(async()=>root.unmount());dom.window.close();for(const[name,descriptor]of originals){if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name]}await rm(cache,{recursive:true,force:true})}
});
