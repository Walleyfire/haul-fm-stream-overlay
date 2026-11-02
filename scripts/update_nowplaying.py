#!/usr/bin/env python3
"""Fetch current Haul.FM metadata for static GitHub Pages deployment."""
import json, re, time, logging
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"docs"/"nowplaying.json"
STREAM="http://stream.haul.fm:8000/haulmpfm.mp3"
STATUS="http://stream.haul.fm:8000/status-json.xsl"
PREVIOUS="https://walleyfire.github.io/haul-fm-stream-overlay/nowplaying.json"
logging.basicConfig(level=logging.INFO)
def fetch(url,headers=None,limit=400000,timeout=8):
    req=Request(url,headers={"User-Agent":"HaulFM-Overlay-GitHub/2.1",**(headers or {})})
    with urlopen(req,timeout=timeout) as r:
        return r.read(limit)
def station():
    try:
        data=json.loads(fetch(STATUS,{"Accept":"application/json"}))
        sources=data.get("icestats",{}).get("source",[])
        sources=[sources] if isinstance(sources,dict) else sources
        src=next((s for s in sources if "/haulmpfm.mp3" in str(s.get("listenurl",s.get("mount","")))),None)
        if src is None and len(sources)==1: src=sources[0]
        if src:
            title=str(src.get("title") or src.get("song") or "")
            artist=str(src.get("artist") or "")
            if artist and title and not title.lower().startswith(artist.lower()+" - "): title=artist+" - "+title
            return title
    except Exception as e: logging.warning("Icecast unavailable: %s",e)
    try:
        req=Request(STREAM,headers={"Icy-MetaData":"1","User-Agent":"HaulFM-Overlay-GitHub/2.1"})
        with urlopen(req,timeout=10) as res:
            n=int(res.headers.get("icy-metaint","0"))
            if not 0<n<=262144:return ""
            first=res.read(n+1)
            if len(first)<n+1:return ""
            meta=res.read(first[n]*16).decode("utf-8","replace")
            found=re.search(r"StreamTitle\s*=\s*(['\"])(.*?)\1",meta)
            return found.group(2) if found else ""
    except Exception as e: logging.warning("ICY unavailable: %s",e)
    return None
def normalize(s):
    return re.sub(r"[^a-z0-9]+"," ",str(s or "").lower()).strip()
def match(a,b):
    a,b=normalize(a),normalize(b)
    if not a or not b:return 0
    if a==b:return 1
    aa,bb=set(a.split()),set(b.split())
    return len(aa&bb)/max(len(aa),len(bb))
def itunes(artist,title):
    if not (artist and title):return None,None
    try:
        url="https://itunes.apple.com/search?"+urlencode({"term":artist+" "+title,"entity":"song","limit":8,"country":"fi"})
        results=json.loads(fetch(url,timeout=7)).get("results",[])
        matches=[(match(artist,r.get("artistName"))*.4+match(title,r.get("trackName"))*.6,r) for r in results if match(artist,r.get("artistName"))>=.78 and match(title,r.get("trackName"))>=.84]
        if not matches:return None,None
        rec=max(matches,key=lambda x:x[0])[1]
        image=rec.get("artworkUrl100")
        if isinstance(image,str):image=re.sub(r"\d+x\d+bb","600x600bb",image)
        if not isinstance(image,str) or not image.startswith("https://"):image=None
        duration=round(float(rec.get("trackTimeMillis") or 0)/1000)
        return image,duration if 30<=duration<=1800 else None
    except Exception as e:logging.warning("iTunes unavailable: %s",e)
    return None,None
def main():
    now=int(time.time())
    result={"status":"offline","title":"","artist":"","artwork":None,"duration":None,"first_seen":None,"last_checked":now}
    raw=station()
    if raw is not None:
        raw=re.sub(r"\s+"," ",str(raw)).strip()[:300]
        if raw and raw.lower() not in ("unknown","haul.fm","-"):
            artist,title=raw.split(" - ",1) if " - " in raw else ("",raw)
            artist,title=artist.strip()[:150],title.strip()[:180]
            prev={}
            try:
                prev=json.loads(fetch(PREVIOUS+"?t="+str(now),timeout=5))
                if now-float(prev.get("last_checked") or 0)>1800:prev={}
            except Exception:pass
            same=prev.get("status")=="live" and prev.get("title")==title and prev.get("artist")==artist
            started=int(prev.get("first_seen") or now) if same else now
            if started>now or now-started>3600:started=now
            image,duration=itunes(artist,title)
            if same:
                image=image or prev.get("artwork")
                duration=duration or prev.get("duration")
            result.update(status="live",title=title,artist=artist,artwork=image,duration=duration,first_seen=started)
        else:result["status"]="no_metadata"
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    logging.info("metadata: %s %s",result["status"],result["title"])
if __name__=="__main__":main()
