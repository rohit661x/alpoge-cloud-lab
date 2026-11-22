"""One paired P2 or P3 image/key block, using one pretrimmed map on disk at a time."""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from capacity_guard import memory, run as guarded
from trial import ARMS, audit, digest, order, save, utc

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--image-index',type=int,default=0,choices=range(8))
parser.add_argument('--profile',type=int,choices=[2,3],default=3)
parser.add_argument('--attempt',type=int,default=1,choices=[1,2])
parser.add_argument('--key',type=int,choices=[1,2],default=1)
parser.add_argument('--timed-rounds',type=int,choices=range(1,6),default=5)
parser.add_argument('--build',type=Path,default=Path('/tmp/stage-native'))
parser.add_argument('--private',type=Path,default=Path('/tmp/stage-pilot-private'))
parser.add_argument('--evidence',type=Path,required=True)
params=parser.parse_args()
os.umask(0o077)
build=params.build.resolve()
p=params.profile
entry=json.loads((HERE/'draw.json').read_text())['images'][params.image_index]
im=entry['image']; photo=HERE/'fixtures'/(im+'.jpg')
assert digest(photo)==entry['sha256']
key=params.key
block=f'{im}-p{p}-k{key}'
evidence=params.evidence.resolve()/(block if params.attempt==1 else block+'-attempt-002')
evidence.mkdir(parents=True,exist_ok=False)
private=params.private.resolve()/block
private.mkdir(parents=True,exist_ok=False)
cwd=private/'run';cwd.mkdir()
(private/'weights').symlink_to(build/'app/weights')
keydir=private/f'stage-keys-p{p}'
cache_maps=shutil.disk_usage(private).free>55*1024**3
env=dict(os.environ,MALLOC_ARENA_MAX='2',OMP_NUM_THREADS='4',OMP_DYNAMIC='FALSE',OMP_MAX_ACTIVE_LEVELS='1',STAGE_PROFILE=str(p),LD_LIBRARY_PATH=str(build/'install/lib'))
if params.attempt==2:
    env.update(MALLOC_ARENA_MAX='1',MALLOC_MMAP_THRESHOLD_='65536',MALLOC_TRIM_THRESHOLD_='0')
exe=dict(old8=build/'arms/old8/stage_ninth',old9=build/'arms/old9/stage_ninth',new8=build/'arms/parents/stage_ninth',new9=build/'arms/parents/stage_ninth',common11=build/'arms/common11/stage_portable')
index=params.image_index*4+(key-1)*2+(p-2)
orders=[order(index,i) for i in range(params.timed_rounds+1)]
def journal(rec):
    with (evidence/'resources.jsonl').open('a') as f: f.write(json.dumps(dict(time=utc(),**rec))+'\n')
def stage_args(arm, dest):
    return [exe[arm],dest]+([arm[-1]] if arm.startswith('new') else [])
def run(args,log,environment,estimate):
    guarded(args,log,cwd,environment,estimate,journal)
def mapname(arm):
    return ('e33.bin' if arm=='old8' or p==2 else 'e1.bin') if arm.endswith('8') else 'eNone.bin'
def expected(arm):
    steps=[-1024,1024]
    if arm.endswith('8'): steps.append(33 if arm=='old8' or p==2 else 1)
    return sorted(boot|{pow(5,v,131072) for v in steps})
def commit_progress(label):
    repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
    evidence.relative_to(repo)
    subprocess.run(['git','add','--',str(evidence.relative_to(repo))],cwd=repo,check=True)
    subprocess.run(['git','commit','-qm',f'{block}: {label}'],cwd=repo,check=True)
    subprocess.run(['git','push','origin','HEAD'],cwd=repo,check=True)
ref=evidence/'reference'
ref.mkdir()
subprocess.run([build/'pack',photo,ref/'input.f64'],check=True)
subprocess.run([build/'reference',build/'app/weights',ref/'input.f64',str({2:200,3:119}[p]),ref/'stage'],check=True)
manifest=HERE/'weight-manifest.csv'
with manifest.open() as f:
    declared={row['path']:row['sha256'] for row in csv.DictReader(f) if row['path'].startswith('weights/') or row['path']=='src/stb_image.h'}
assert len(declared)==1016 and all(digest(build/'app'/name)==want for name,want in declared.items())
snapshot={str(n):digest(path) for n,path in dict(**exe,init=build/'harness/stage_native',pack=build/'pack',reference=build/'reference').items()}
save(evidence/'freeze.json',dict(block=block,image=entry,profile=p,key=key,threads=4,orders=orders,binaries=snapshot,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),primary_ratio_threshold=.98,checkpoint_rmse_gate=.01,checkpoint_max_abs_gate=.05,diagnostics=dict(architecture=os.uname().machine,cpu_info=subprocess.check_output(['lscpu'],text=True),cgroup_memory_limit=(Path('/sys/fs/cgroup/memory.max').read_text().strip()),cgroup_cpu_limit=Path('/sys/fs/cgroup/cpu.max').read_text().strip(),compiler=subprocess.check_output(['g++-12','--version'],text=True).splitlines()[0],allocator={k:env[k] for k in env if k.startswith('MALLOC_')},attempt=params.attempt,weight_manifest_sha256=digest(manifest),verified_weight_files=1015,arm_compile_flags={name:(build/'arms'/name/'CMakeFiles'/('stage_portable.dir' if name=='common11' else 'stage_ninth.dir')/'flags.make').read_text() for name in ['old8','old9','parents','common11']},openfhe_commit=subprocess.check_output(['git','-C',build/'openfhe','rev-parse','HEAD'],text=True).strip(),upstream_commit=subprocess.check_output(['git','-C',build/'app','rev-parse','HEAD'],text=True).strip()),cache_all_trimmed_maps=cache_maps,setup_mode='physical keygen without bootstrap matrix precomputation; exact serialized maps',start=utc()))
try:
    # Earlier full P3 master map serializes to 9.966 GB; keygen omits the
    # transform plaintexts, while the numerical evaluator loads them normally.
    setup_est={2:12_700_000_000,3:10_500_000_000}[p]
    stage_est={2:16_430_000_000,3:13_670_000_000}[p]
    if params.attempt==2 and p==3:
        # The first native attempt reached 12.968 GB. This is a bounded
        # feasibility retry with a higher host reserve, not a prediction of completion.
        stage_est=13_100_000_000
    for baseline, expected_size in [(private, {2:24_000_000_000,3:20_100_000_000}[p])]:
        if shutil.disk_usage(baseline).free < expected_size+1024**3:
            raise RuntimeError(f'insufficient disk for original master and one active map: {shutil.disk_usage(baseline).free}')
    run([build/'harness/stage_native','init',photo],evidence/'init.log',env,setup_est)
    assert digest(keydir/'input.f64')==digest(ref/'input.f64')
    ids_file=keydir/'bootstrap-indices.txt'
    shutil.copyfile(ids_file,evidence/ids_file.name)
    boot=set(map(int,ids_file.read_text().split()))
    assert boot==set(map(int,(HERE/f'bootstrap-p{p}.txt').read_text().split()))
    identity={n:digest(keydir/n) for n in ['input.ct','input.f64','public-key.txt','crypto-context.txt','bootstrap-indices.txt']}
    save(evidence/'identity.json',identity)
    tag=None;active_file=None
    for r,arms in enumerate(orders):
        label='warmup' if r==0 else f'r{r}'
        for position,arm in enumerate(arms,1):
            dest=evidence/label/arm;dest.mkdir(parents=True)
            filename=mapname(arm);map_path=keydir/('rot_'+filename); wanted=expected(arm)
            ee=dict(env,TRIAL_MAP=filename)
            if not map_path.exists():
                if active_file and not cache_maps: active_file.unlink()
                run(stage_args(arm,dest),dest/'prepare.log',dict(ee,TRIAL_PREPARE='1'),setup_est)
                found=sorted(map(int,re.findall(r'actual_index=(\d+)',(dest/'prepare.log').read_text())))
                assert found==wanted
                active_file=map_path
            run(stage_args(arm,dest),dest/'log.txt',ee,stage_est)
            raw=(dest/'log.txt').read_text()
            ids=sorted(map(int,re.findall(r'actual_index=(\d+)',raw)))
            num,sz=map(int,re.search(r'full_map_keys=(\d+) full_map_bytes=(\d+)',raw).groups())
            assert ids==wanted and len(ids)==num and sz==map_path.stat().st_size
            this_tag=hashlib.sha256(re.search(r'key_tag=([0-9a-f]+)',raw)[1].encode()).hexdigest()
            if tag is None: tag=this_tag
            assert tag==this_tag
            checkpoints=audit(dest,ref/'stage')
            assert len(checkpoints)==14
            with (dest/'stage.csv').open() as f: row=next(csv.DictReader(f))
            save(dest/'record.json',dict(arm=arm,round=label,position=position,indices=ids,map_bytes=sz,map_deserialize_seconds=float(re.search(r'map_deserialize_seconds=([\d.eE+-]+)',raw)[1]),key_tag_sha256=tag,stage=row,checkpoints=checkpoints,gate_pass=all(v['rmse']<=.01 and v['max_abs']<=.05 for v in checkpoints)))
        commit_progress(label)
    assert all(h==digest(keydir/n) for n,h in identity.items())
    save(evidence/'complete.json',dict(block=block,finished=utc(),timed_rounds=params.timed_rounds))
    commit_progress('complete')
except Exception as e:
    save(evidence/'failure.json',dict(reason=repr(e),time=utc()))
    commit_progress('admission or execution failure')
    raise
finally:
    # All keys and ciphertexts were generated within this unique invocation directory.
    shutil.rmtree(private)
