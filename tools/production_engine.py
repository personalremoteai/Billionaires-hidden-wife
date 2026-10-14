#!/usr/bin/env python3
"""Validate, batch-generate, and prepare prompts for a 70-episode vertical drama."""
import argparse, json, os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production' / 'episode_outputs'
MODEL_DEFAULT = 'gemini-2.5-flash'

def read(p):
    try: return p.read_text(encoding='utf-8')
    except FileNotFoundError: return ''

def canon():
    parts=[]
    for rel in ('story_bible/series_bible.md','characters/character_bible.md','production/series_brief.md'):
        s=read(ROOT/rel)
        if s.strip(): parts.append(f'--- {rel} ---\n{s[:16000]}')
    return '\n\n'.join(parts)

def ep_path(n): return OUT / f'episode_{n:03d}.json'

def validate(o, n=None):
    e=[]
    if not isinstance(o,dict): return ['top level must be an object']
    for k in ('episode_number','title','logline','previously_established','scenes','cliffhanger'):
        if k not in o: e.append('missing '+k)
    if n is not None and o.get('episode_number') != n: e.append(f'episode_number must be {n}')
    ss=o.get('scenes')
    if not isinstance(ss,list) or not 3 <= len(ss) <= 5: e.append('scenes must contain 3–5 scene objects')
    else:
        for i,s in enumerate(ss,1):
            if not isinstance(s,dict): e.append(f'scene {i} must be an object'); continue
            for k in ('location','time','visual_action','dialogue','image_prompt'):
                if k not in s: e.append(f'scene {i} missing {k}')
            if not isinstance(s.get('dialogue',[]),list): e.append(f'scene {i} dialogue must be a list')
    if not isinstance(o.get('cliffhanger'),str) or len(o.get('cliffhanger','').strip())<8: e.append('cliffhanger must be specific')
    return e

def prompt(n, prev, bible):
    continuity = 'This is episode 1: establish the premise and cast.' if not prev else f"Previous episode #{prev.get('episode_number')} — {prev.get('title')}\nCliffhanger: {prev.get('cliffhanger')}\nContinuity: {prev.get('continuity_notes','')}\nPay off or directly acknowledge this cliffhanger."
    return f'''You are head writer for an original vertical micro-drama, The Billionaire's Hidden Wife. Return valid JSON only for episode {n}. Canon (preserve names, relationships, timeline and facts):\n{bible[:24000]}\n\nContinuity: {continuity}\n\nRequirements: 60–120 seconds, around 180–300 spoken words, exactly 3–5 scenes, immediate hook, escalating conflict, natural concise dialogue, strong concrete cliffhanger. Each scene must have scene_number (integer), location, time, visual_action, dialogue (array of {{speaker,line}}), narration, image_prompt. Image prompt: one photorealistic cinematic vertical 9:16 frame, face/expression, wardrobe, lighting, location, camera framing and character traits; no rendered text. Top-level fields: episode_number ({n}), title, logline, previously_established (array), scenes, cliffhanger, continuity_notes, new_facts (array), characters_present (array). Do not copy existing shows or use real actors. Return parseable JSON only.'''

def generate(n, client, model, bible, overwrite):
    OUT.mkdir(parents=True,exist_ok=True); path=ep_path(n)
    if path.exists() and not overwrite: print('SKIP existing',path.relative_to(ROOT)); return
    prev=None
    if n>1 and ep_path(n-1).exists():
        try: prev=json.loads(read(ep_path(n-1)))
        except Exception: pass
    resp=client.models.generate_content(model=model,contents=prompt(n,prev,bible),config={'response_mime_type':'application/json','temperature':0.8})
    raw=(getattr(resp,'text','') or '').strip(); raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I)
    obj=json.loads(raw); errors=validate(obj,n)
    if errors: raise ValueError('; '.join(errors))
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CREATED',path.relative_to(ROOT),'-',obj.get('title'))

def prepare():
    promptroot=OUT/'prompts'; promptroot.mkdir(parents=True,exist_ok=True); count=0
    for p in sorted(OUT.glob('episode_[0-9][0-9][0-9].json')):
        try: o=json.loads(read(p)); errs=validate(o)
        except Exception as ex: print('FAIL',p.name,ex); continue
        if errs: print('FAIL',p.name,'; '.join(errs)); continue
        folder=promptroot/f"episode_{int(o['episode_number']):03d}"; folder.mkdir(parents=True,exist_ok=True)
        for i,s in enumerate(o['scenes'],1):
            (folder/f'scene_{i:02d}_image_prompt.txt').write_text(s['image_prompt'].strip()+'\n',encoding='utf-8')
            lines=[f"{d.get('speaker','VOICE')}: {d.get('line','')}" for d in s.get('dialogue',[]) if isinstance(d,dict)]
            if s.get('narration','').strip(): lines.append('NARRATION: '+s['narration'].strip())
            (folder/f'scene_{i:02d}_voiceover.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8'); count+=1
    print(f'Prepared {count} scenes under {promptroot.relative_to(ROOT)}')

def main():
    a=argparse.ArgumentParser(); a.add_argument('--start',type=int,default=1); a.add_argument('--count',type=int,default=1); a.add_argument('--dry-run',action='store_true'); a.add_argument('--overwrite',action='store_true'); a.add_argument('--prepare-prompts',action='store_true'); a.add_argument('--validate-all',action='store_true'); x=a.parse_args()
    if x.prepare_prompts: prepare(); return 0
    if x.validate_all:
        ps=sorted(OUT.glob('episode_[0-9][0-9][0-9].json')); bad=0
        for p in ps:
            try: errs=validate(json.loads(read(p)),int(p.stem.split('_')[1]))
            except Exception as ex: errs=[str(ex)]
            print(('FAIL' if errs else 'PASS'),p.name,('; '.join(errs) if errs else ''))
            bad += bool(errs)
        print(f'Validated {len(ps)} file(s); failures: {bad}'); return int(bool(bad))
    if x.start<1 or x.count<1 or x.start+x.count-1>70: a.error('select episode numbers within 1–70')
    nums=range(x.start,x.start+x.count)
    if x.dry_run:
        print('DRY RUN — no API calls or files written')
        for n in nums: print(f'Episode {n:03d}: '+('replace' if x.overwrite and ep_path(n).exists() else ('skip' if ep_path(n).exists() else 'generate')))
        return 0
    key=os.getenv('GEMINI_API_KEY')
    if not key: print('Set GEMINI_API_KEY as an environment variable; never commit it.',file=sys.stderr); return 2
    try: from google import genai
    except ImportError: print('Install dependencies: python -m pip install -r requirements-engine.txt',file=sys.stderr); return 2
    client=genai.Client(api_key=key); model=os.getenv('GEMINI_MODEL',MODEL_DEFAULT); bible=canon()
    for n in nums:
        try: generate(n,client,model,bible,x.overwrite)
        except Exception as ex: print(f'ERROR episode {n}: {ex}',file=sys.stderr); return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
