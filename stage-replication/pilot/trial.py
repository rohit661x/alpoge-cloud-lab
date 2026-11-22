"""Recoverable serial five-arm blocked trial. Launch one controller per host."""
import csv, fcntl, hashlib, json, math, os, platform, re, shutil, subprocess, sys, time
from array import array
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
ARMS=['old8','new8','old9','new9','common11']
def utc(): return datetime.now(timezone.utc).isoformat()
def digest(f):
    h=hashlib.sha256()
    with f.open('rb') as s:
        for chunk in iter(lambda:s.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temp.replace(path)
def frozen(path,val):
    if path.exists() and json.loads(path.read_text())!=val: raise RuntimeError(f'freeze changed {path}')
    if not path.exists(): save(path,val)
def invoke(cmd,log,cwd,env):
    with log.open('w') as f:
        subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,cwd=cwd,env=env,check=True)
def args(arm,dest):
    return [c[arm],dest]+([arm[-1]] if arm.startswith('new') else [])
def audit(dest,ref):
    rows=[]
    for layer in range(7):
        for phase in ['conv','post']:
            name=f'{phase}-{layer}.f64'
            v=[array('d',(p/name).read_bytes()) for p in (dest,ref)]
            if sys.byteorder!='little':
                for a in v:a.byteswap()
            if any(len(a)!=16384 for a in v): raise ValueError(name)
            err=[abs(x-y) for x,y in zip(*v)]
            if not all(map(math.isfinite,err)):raise ValueError(name+' nonfinite')
            rows.append(dict(name=name,rmse=math.sqrt(math.fsum(x*x for x in err)/len(err)),max_abs=max(err),decoded_sha256=digest(dest/name)))
    return rows
def order(block,roundno):
    # Five rotations cover each arm at each position per measured block.
    shifts=[0,1,4,2,3]
    seeded=sorted(ARMS,key=lambda arm:hashlib.sha256(('order-v1:2026-11-22|'+arm).encode()).digest())
    base=seeded if (block//5)%2==0 else seeded[::-1]
    return [base[(pos+block+shifts[(roundno-1)%5])%5] for pos in [0,1,4,2,3]]
def run():
    d=json.loads((HERE/'draw.json').read_text())
    images=[v['image'] for v in d['images']]
    # Distribute hosts' early completed blocks across both profiles, then both keys.
    blocks=[(im,p,k) for im in images for k in [1,2] for p in [2,3]]
    orders={f'{im}-p{p}-k{k}':[order(b,i) for i in range(6)] for b,(im,p,k) in enumerate(blocks)}
    frozen(out/'freeze.json',dict(images=d,order_seed="order-v1:2026-11-22",orders=orders,arm_names=ARMS,rounds=['warmup','r1','r2','r3','r4','r5'],primary_ratio_threshold=0.98,checkpoint_rmse_gate=0.01,checkpoint_max_abs_gate=0.05,gate_basis='Engineering feature tolerances, calibrated on independent cat/frog/truck worst checkpoint RMSE .004415 and absolute .025654; no classifier requirement supplied.',binaries={n:digest(Path(c[n])) for n in ['init','reference','pack',*ARMS]},driver=digest(Path(__file__)),hardware=platform.uname()._asdict(),omp_threads=int(env['OMP_NUM_THREADS'])))
    for v in d['images']:
        im=v['image']; photo=Path(c['fixtures'])/(im+'.jpg')
        if digest(photo)!=v['sha256']:raise ValueError(im)
        ref=out/'refs'/im;ref.mkdir(parents=True,exist_ok=True)
        if not (ref/'done.json').exists():
            invoke([c['pack'],photo,ref/'input.f64'],ref/'pack.log',ref,env)
            for p,degree in [(2,200),(3,119)]:
                invoke([c['reference'],c['weights'],ref/'input.f64',str(degree),ref/str(p)],ref/f'ref{p}.log',ref,env)
            save(ref/'done.json',{str(f.relative_to(ref)):digest(f) for f in ref.rglob('*.f64')})
    for b,(im,p,k) in enumerate(blocks):
        block=f'{im}-p{p}-k{k}'; dest=out/'blocks'/block;dest.mkdir(parents=True,exist_ok=True)
        priv=out/'private'/block; keydir=priv/f'stage-keys-p{p}'; cwd=priv/'run'
        reserve=c.get('reserve_first',False) and b in [0,1]
        def cleanup():
            if priv.exists() and not reserve and (priv/'owner').read_text()==block and priv.parent==out/'private':
                shutil.rmtree(priv)
        if (dest/'done.json').exists():cleanup();continue
        cwd.mkdir(parents=True,exist_ok=True)
        (priv/'owner').write_text(block)
        if not (priv/'weights').exists():(priv/'weights').symlink_to(Path(c['weights']))
        e=dict(env,STAGE_PROFILE=str(p))
        ref=out/'refs'/im
        if not (dest/'identity.json').exists():
            if keydir.exists():raise RuntimeError(f'partial initialization {keydir}; preserve and move aside before retry')
            if shutil.disk_usage(priv).free<45*1024**3:raise RuntimeError('insufficient space for map preparation')
            start=time.monotonic()
            invoke([c['init'],'init',Path(c['fixtures'])/(im+'.jpg')],dest/'init.log',cwd,e)
            names=['input.ct','input.f64','public-key.txt','crypto-context.txt','bootstrap-indices.txt']
            ident={n:digest(keydir/n) for n in names}
            if ident['input.f64']!=digest(ref/'input.f64'):raise ValueError('packing mismatch')
            shutil.copyfile(keydir/'bootstrap-indices.txt',dest/'bootstrap-indices.txt')
            save(dest/'identity.json',dict(image=im,profile=p,key=k,hashes=ident,init_seconds=time.monotonic()-start))
        boot=set(map(int,(dest/'bootstrap-indices.txt').read_text().split()))
        maps={}
        for arm in ARMS:
            extra=(33 if arm=='old8' or p==2 else 1) if arm.endswith('8') else None
            ids=sorted(boot|{pow(5,offset,131072) for offset in ([-1024,1024]+([extra] if extra else []))})
            filename='e'+str(extra)+'.bin';mp=keydir/('rot_'+filename)
            ee=dict(e,TRIAL_MAP=filename)
            if filename not in maps:
                log=dest/f'prepare-{filename}.log'
                if not mp.exists():invoke(args(arm,dest/'preparation'),log,cwd,dict(ee,TRIAL_PREPARE='1'))
                maps[filename]=sorted(map(int,re.findall(r'actual_index=(\d+)',log.read_text())))
                if maps[filename]!=ids:raise ValueError(f'pretrim mismatch {arm}: {set(ids)^set(maps[filename])}')
        for rr,arms in enumerate(orders[block]):
            r='warmup' if rr==0 else f'r{rr}'
            for pos,arm in enumerate(arms):
                root=dest/r/arm;root.mkdir(parents=True,exist_ok=True)
                if (root/'accepted.json').exists():continue
                attempts=len(list(root.glob('attempt-*')))
                dr=root/f'attempt-{attempts+1:03d}';dr.mkdir()
                extra=(33 if arm=='old8' or p==2 else 1) if arm.endswith('8') else None
                filename='e'+str(extra)+'.bin'
                start=time.monotonic();rec=dict(image=im,profile=p,key=k,arm=arm,round=r,position=pos+1,started=utc())
                try:
                    invoke(args(arm,dr),dr/'log.txt',cwd,dict(e,TRIAL_MAP=filename))
                    log=(dr/'log.txt').read_text()
                    ids=sorted(map(int,re.findall(r'actual_index=(\d+)',log)))
                    if ids!=maps[filename]:raise ValueError('incorrect map')
                    num,sz=map(int,re.search(r'full_map_keys=(\d+) full_map_bytes=(\d+)',log).groups())
                    if num!=len(ids) or sz!=(keydir/('rot_'+filename)).stat().st_size:raise ValueError('map size')
                    errs=audit(dr,ref/str(p))
                    tag=hashlib.sha256(re.search(r'key_tag=([0-9a-f]+)',log)[1].encode()).hexdigest()
                    frozen(dest/'tag.json',tag)
                    rec.update(status='complete',indices=ids,map_bytes=sz,map_deserialize_seconds=float(re.search(r'map_deserialize_seconds=([\d.eE+-]+)',log)[1]),key_tag_sha256=tag,checkpoints=errs,gate_pass=all(x['rmse']<=.01 and x['max_abs']<=.05 for x in errs))
                except Exception as exc:
                    rec.update(status='failed',reason=repr(exc));raise
                finally:
                    rec.update(finished=utc(),process_and_audit_seconds=time.monotonic()-start);save(dr/'record.json',rec)
                save(root/'accepted.json',dr.name)
            print(utc(),block,r,'completed',flush=True)
        ident=json.loads((dest/'identity.json').read_text())
        if any(digest(keydir/n)!=h for n,h in ident['hashes'].items()):raise ValueError('fixture changed')
        save(dest/'done.json',{'finished':utc(),'invocations':30})
        if reserve:
            for filename in maps:(keydir/('rot_'+filename)).unlink(missing_ok=True)
        cleanup()
    save(out/'complete.json',dict(blocks=len(blocks),finished=utc()))
if __name__=='__main__':
    os.umask(0o077)
    c=json.loads(Path(sys.argv[1]).read_text())
    out=Path(c['output']).resolve();out.mkdir(parents=True,exist_ok=True)
    lock=(out/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    env=dict(os.environ,OMP_NUM_THREADS=str(c.get('threads',6)),OMP_DYNAMIC='FALSE',OMP_MAX_ACTIVE_LEVELS='1',VECLIB_MAXIMUM_THREADS='1',**c.get('environment',{}))
    run()
