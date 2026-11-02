/** Haul.FM OBS overlay metadata proxy.
 * Fixed upstreams only: prevents arbitrary URL proxying or SSRF.
 * No user identifiers are collected or stored.
 */
const STATUS_URL = 'http://stream.haul.fm:8000/status-json.xsl';
const STREAM_URL = 'http://stream.haul.fm:8000/haulmpfm.mp3';
const MOUNT = '/haulmpfm.mp3';
const REFRESH_MS = 15000;
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Cache-Control': 'no-store, max-age=0',
  'Content-Type': 'application/json; charset=utf-8',
  'X-Content-Type-Options': 'nosniff',
};
let cache = null;
let inflight = null;
let lastTrack = '';
let firstSeen = 0;
let artCache = new Map();

const jsonResponse = (body, status = 200) => new Response(JSON.stringify(body), {status, headers:CORS});
const norm = value => String(value || '').toLowerCase()
  .replace(/\([^)]*(?:feat\.?|ft\.?|remaster|radio edit|extended)[^)]*\)/g, '')
  .replace(/&/g,'and').replace(/[^a-z0-9]+/g,' ').trim();
function scoreMatch(a,b){
  const x=norm(a),y=norm(b);
  if(!x||!y)return 0;
  if(x===y)return 1;
  const xs=new Set(x.split(' ')),ys=new Set(y.split(' '));
  return [...xs].filter(w=>ys.has(w)).length / Math.max(xs.size,ys.size);
}
function parseSong(text){
  const raw=String(text || '').replace(/\s+/g,' ').trim();
  if(!raw || /^(?:-|unknown|n\/a|haulfm|haul fm|haulmpfm|haulmp fm)$/i.test(raw)) return {artist:'',title:''};
  const i=raw.indexOf(' - ');
  if(i>0&&i<raw.length-3) return {artist:raw.slice(0,i).trim(),title:raw.slice(i+3).trim()};
  return {artist:'',title:raw};
}
function validArtwork(url){
  if(typeof url!=='string')return null;
  try{
    const u=new URL(url);
    if(u.protocol!=='https:')return null;
    if(/\/brand\/|icon-96|wordmark-275/i.test(u.pathname))return null;
    return u.toString();
  }catch{return null;}
}
function pickStation(sources){
  const arr=Array.isArray(sources)?sources:sources&&typeof sources==='object'?[sources]:[];
  const source=arr.find(s=>s&&typeof s==='object' && ['listenurl','mount','server_url'].some(k=>String(s[k]||'').split('?')[0].includes(MOUNT)))
    || (arr.length===1?arr[0]:null);
  return source && typeof source==='object' ? source : null;
}
async function getIcecast(){
  const res=await fetch(STATUS_URL,{headers:{Accept:'application/json','User-Agent':'HaulFM-Overlay/2.0'},signal:AbortSignal.timeout(7000)});
  if(!res.ok)throw new Error('Icecast HTTP '+res.status);
  const data=await res.json();
  const source=pickStation(data?.icestats?.source);
  if(!source)return {online:false,raw:'',artwork:null};
  const artist=String(source.artist||'').trim();
  const raw=String(source.title||source.song||'').trim();
  return {
    online:true,
    raw:artist && raw && !raw.startsWith(artist+' - ')?artist+' - '+raw:raw,
    artwork:validArtwork(source.artwork||source.cover||source.album_art||source.image),
  };
}
async function getIcy(){
  // Read at most the first metadata block; do not rebroadcast or play audio.
  const res=await fetch(STREAM_URL,{
    headers:{'Icy-MetaData':'1','User-Agent':'HaulFM-Overlay/2.0'},
    signal:AbortSignal.timeout(9000)
  });
  if(!res.ok)throw new Error('ICY HTTP '+res.status);
  const interval=Number(res.headers.get('icy-metaint'));
  if(!Number.isInteger(interval)||interval<1||interval>262144 || !res.body){
    if(res.body)await res.body.cancel().catch(()=>{});
    return {online:true,raw:'',artwork:null};
  }
  const reader=res.body.getReader();
  let buf=new Uint8Array(0),limit=interval+1+4080;
  try{
    while(buf.length<interval+1 && limit>0){
      const {value,done}=await reader.read();
      if(done)break;
      const take=Math.min(value.length,limit);
      const next=new Uint8Array(buf.length+take);
      next.set(buf);next.set(value.slice(0,take),buf.length);buf=next;limit-=take;
    }
    if(buf.length<interval+1)return {online:true,raw:'',artwork:null};
    const blockLength=buf[interval]*16;
    while(buf.length<interval+1+blockLength&&limit>0){
      const {value,done}=await reader.read();
      if(done)break;
      const take=Math.min(value.length,limit);
      const next=new Uint8Array(buf.length+take);
      next.set(buf);next.set(value.slice(0,take),buf.length);buf=next;limit-=take;
    }
    const meta=new TextDecoder().decode(buf.slice(interval+1,interval+1+blockLength)).replace(/\0+$/,'');
    const match=meta.match(/StreamTitle\s*=\s*(['"])(.*?)\1\s*;?/i);
    return {online:true,raw:match?match[2]:'',artwork:null};
  }finally{
    await reader.cancel().catch(()=>{});
  }
}
async function searchCover(artist,title){
  const key=norm(artist+' '+title);
  if(!key)return {artwork:null,duration:null};
  const fromCache=artCache.get(key);
  if(fromCache && Date.now()-fromCache.when<60*60*1000)return fromCache.value;
  const out={artwork:null,duration:null};
  if(artist && title){
    try{
      const endpoint='https://itunes.apple.com/search?'+new URLSearchParams({term:artist+' '+title,entity:'song',limit:'8',country:'fi'});
      const res=await fetch(endpoint,{signal:AbortSignal.timeout(5500)});
      if(res.ok){
        const data=await res.json();
        let top=null,highest=0;
        for(const rec of data.results || []){
          const a=scoreMatch(artist,rec.artistName),t=scoreMatch(title,rec.trackName);
          if(a<.78||t<.84)continue;
          const score=a*.4+t*.6;
          if(score>highest){top=rec;highest=score;}
        }
        if(top){
          const raw=top.artworkUrl100||top.artworkUrl60;
          out.artwork=validArtwork(typeof raw==='string'?raw.replace(/\d+x\d+bb/,'600x600bb'):null);
          const d=Number(top.trackTimeMillis);
          out.duration=Number.isFinite(d) && d>=30000&&d<=1800000?Math.round(d/1000):null;
        }
      }
    }catch{ /* Artwork lookup is optional. */ }
  }
  artCache.set(key,{when:Date.now(),value:out});
  if(artCache.size>80)artCache.delete(artCache.keys().next().value);
  return out;
}
async function fetchNowPlaying(){
  let station;
  try{station=await getIcecast();}catch{station=null;}
  if(!station || !station.raw){
    try{const icy=await getIcy();if(!station || icy.raw || !station.online)station=icy;}catch{/* handled below */}
  }
  if(!station) return {status:'offline',title:'',artist:'',artwork:null,duration:null,first_seen:null,last_checked:Date.now()/1000};
  const {artist,title}=parseSong(station.raw);
  if(!title)return {status:station.online?'no_metadata':'offline',title:'',artist:'',artwork:null,duration:null,first_seen:null,last_checked:Date.now()/1000};
  const key=artist+'\u001f'+title;
  if(key!==lastTrack){lastTrack=key;firstSeen=Date.now()/1000;}
  const extra=await searchCover(artist,title);
  return {status:'live',title,artist,artwork:station.artwork||extra.artwork,duration:extra.duration,first_seen:firstSeen,last_checked:Date.now()/1000};
}
export default {
  async fetch(request){
    const url=new URL(request.url);
    if(request.method==='OPTIONS')return new Response(null,{status:204,headers:CORS});
    if(request.method!=='GET')return jsonResponse({error:'Method not allowed'},405);
    if(url.pathname!=='/api/nowplaying')return jsonResponse({error:'Not found. Use /api/nowplaying'},404);
    if(cache && Date.now()<cache.expires)return jsonResponse(cache.data);
    if(!inflight){
      inflight=fetchNowPlaying().then(data=>{
        cache={data,expires:Date.now()+REFRESH_MS};return data;
      }).finally(()=>{inflight=null;});
    }
    return jsonResponse(await inflight);
  }
};
