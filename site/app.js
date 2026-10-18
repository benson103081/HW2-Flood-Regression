'use strict';
const $=id=>document.getElementById(id);
const labels=['季風強度','地形排水','河川管理','森林砍伐','都市化','氣候變遷','水壩品質','淤積','農業活動','土地侵占','災害準備不足','排水系統','海岸脆弱度','山崩','集水區','基礎設施劣化','人口分數','濕地流失','規劃不足','政治因素'];
let data;
function fmt(n,d=5){return n!==0&&Math.abs(n)<10**(-d)?Number(n).toExponential(2):Number(n).toFixed(d)}
function predict(){
 const name=$('model-select').value,model=data.exports[name];
 const values=data.features.map((f,i)=>Number($('n'+i).value));
 if(values.some((v,i)=>!Number.isFinite(v)||$('n'+i).value.trim()==='')){ $('prediction-value').textContent='—';$('prediction-message').textContent='請填入全部 20 個有效數值。';$('prediction-interval').textContent='—';$('meter-fill').style.width='0%';return;}
 const value=model.intercept+values.reduce((sum,v,i)=>sum+v*model.coef[i],0);
 $('prediction-value').textContent=(value*100).toFixed(2)+'%';$('meter-fill').style.width=Math.min(100,Math.max(0,value*100))+'%';
 const out=values.some((v,i)=>v<data.feature_summary[data.features[i]].min||v>data.feature_summary[data.features[i]].max);
 $('prediction-message').textContent=out?'輸入超出訓練範圍，屬於外推；結果需審慎解讀。':value<0||value>1?'線性模型輸出超出 0–1 範圍，已保留原值，不能解讀為有效機率。':'這是資料集目標的預測分數，不是已校準的真實事件機率。';
 if(model.interval){const z=[1,...values],q=model.interval;let h=0;for(let i=0;i<z.length;i++)for(let j=0;j<z.length;j++)h+=z[i]*q.xtx_inverse[i][j]*z[j];const width=q.t_critical*Math.sqrt(q.sigma2*(1+h));$('prediction-interval').textContent=((value-width)*100).toFixed(2)+'% – '+((value+width)*100).toFixed(2)+'%';}else $('prediction-interval').textContent='殘差退化，不提供區間';
 $('equation').textContent='ŷ = '+fmt(model.intercept,7)+model.coef.map((c,i)=>c===0?'':` ${c>=0?'+':'−'} ${fmt(Math.abs(c),7)} × ${data.features[i]}`).join('');
}
function preset(direction=0){data.features.forEach((f,i)=>{const s=data.feature_summary[f];const value=Math.min(s.max,Math.max(s.min,s.median+direction*s.std));$('n'+i).value=value.toFixed(2);$('s'+i).value=value;});predict();}
async function start(){
 try{const response=await fetch('assets/results.json');if(!response.ok)throw Error('HTTP '+response.status);data=await response.json();
 $('load-status').hidden=true;const best=data.models.find(m=>m.name===data.recommended_linear);$('rows').textContent=data.rows.toLocaleString();$('r2').textContent=fmt(best.test.r2,4);$('rmse').textContent=fmt(best.test.rmse,5);$('recommended').textContent=best.name+' · CV 推薦';
 $('finding').textContent=`CV 推薦線性模型：${best.name}。全部 50,000 筆目標皆等於 20 個輸入分數總和 ÷ 200，因此 R² = 1 反映確定性公式，並非真實洪水預測能力。精簡特徵會丟失公式所需資訊。`;
 $('model-table').innerHTML=data.models.map(m=>`<tr class="${m.name===best.name?'recommended':''}"><td>${m.name}${m.name===best.name?' ✓':''}</td><td>${fmt(m.cv_rmse)} ± ${fmt(m.cv_sd)}</td><td>${fmt(m.test.rmse)}</td><td>${fmt(m.test.mae)}</td><td>${fmt(m.test.r2,4)}</td><td>${m.nonzero??'—'}</td></tr>`).join('');
 $('model-select').innerHTML=Object.keys(data.exports).map(n=>`<option>${n}</option>`).join('');$('model-select').value=best.name;
 $('inputs').innerHTML=data.features.map((f,i)=>{const s=data.feature_summary[f];return `<div class="input-item"><label for="n${i}">${labels[i]}</label><small>${f}</small><div class="input-row"><input id="s${i}" type="range" min="${s.min}" max="${s.max}" step="0.01" aria-label="${labels[i]}滑桿"><input id="n${i}" type="number" step="any" required aria-label="${labels[i]}數值"></div><small>訓練範圍 ${s.min}–${s.max}</small></div>`;}).join('');
 data.features.forEach((_,i)=>{$('s'+i).addEventListener('input',()=>{$('n'+i).value=$('s'+i).value;predict()});$('n'+i).addEventListener('input',()=>{$('s'+i).value=$('n'+i).value;predict()})});
 $('reset').addEventListener('click',()=>preset());document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>preset(b.dataset.preset==='low'?-1:1)));$('model-select').addEventListener('change',predict);$('predict-form').addEventListener('submit',e=>{e.preventDefault();predict()});
 const d=data.diagnostics;const p=x=>x===null?'不適用（殘差退化）':x<.0001?'< 0.0001':fmt(x,4);
 $('diagnostic-list').replaceChildren();
 [['線性','RESET p '+p(d.reset_p)+'；搭配殘差圖判讀。'],['等變異','Breusch–Pagan p '+p(d.breusch_pagan_p)+'。'],['殘差常態','Jarque–Bera p '+p(d.jarque_bera_p)+'；搭配 Q-Q 圖。'],['無嚴重共線性','最大 VIF '+fmt(d.max_vif,3)+'。'],['觀測獨立','無時間／地區識別資訊，無法確認。']].forEach(([k,v])=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=v;$('diagnostic-list').append(dt,dd)});
 preset();
 }catch(error){$('load-status').textContent='無法載入分析結果。請透過網站伺服器開啟，或稍後重試。';console.error(error);}
}
start();
