"""Summarize matched transport captures without treating sampled counts as full-frame totals."""
from pathlib import Path
import argparse, csv, json, re
import numpy as np

def summarize(destination):
    destination=Path(destination)
    instance=destination/'instance'
    markers=(instance/'lighting-progress.txt').read_text()
    starts={};intervals={}
    for frame,kind,name in re.findall(r'frame=(\d+) MEASURE_(BEGIN|END) (\S+)',markers):
        if kind=='BEGIN': starts[name]=int(frame)
        elif name in starts: intervals[name]=(starts[name],int(frame))
    if 'PASS: transport subset' not in markers or len(intervals)!=4:
        raise ValueError('Transport subset incomplete')
    with (instance/'gpu-timings-validation.csv').open() as source:timings=list(csv.DictReader(source))
    counts=[]
    requested=json.loads((destination/'run-process.json').read_text()).get('counters_requested',False)
    if (instance/'transport-counts.csv').exists():
        with (instance/'transport-counts.csv').open() as source:counts=list(csv.DictReader(source))
    if requested and not counts:raise ValueError('Requested sampled-work capture is empty')
    report={'scenes':{},'contracts':[
        'Counters are opt-in caller-side sampled work, not full-frame exact totals or hardware stall measurements.',
        'Each pixel participates once per 1024 frames; short captures sample part of the rotating strata.',
        'Report sum of calls / sum of sampled pixels; do not multiply a partial edge stratum by 1024.',
        'PT material_retraces counts replay entry calls, including early invalid identities; pt_surface_rays counts actual dispatched rays, including transmittance crossings.',
        'BSDF/PDF/environment counters currently cover explicit PT adapter calls; RIS candidates also cover shared surface RIS. Child hit/miss invocations do not inherit raygen counter state.',
        'Shadow_queries counts shared visibility entry calls; inline_queries is its optional opaque pretest. These overlap, not additive ray totals.',
        'Formal timing comparisons require counters disabled; diagnostic times are reported separately.'
    ]}
    for name,(lo,hi) in intervals.items():
        rows=[r for r in timings if lo<int(r['frame'])<hi]
        if len(rows)<20:raise ValueError(f'{name}: fewer than 20 steady frames')
        scene={'frames':len(rows),'gpu':{},'work':{}}
        for key in rows[0]:
            if key=='frame' or key.endswith('_tick'):continue
            data=np.array([float(r[key]) for r in rows]);data=data[np.isfinite(data)]
            if len(data):scene['gpu'][key]={'median':float(np.median(data)),'p95':float(np.percentile(data,95))}
        for stage in sorted({r['stage'] for r in counts}):
            work=[r for r in counts if r['stage']==stage and lo<int(r['frame'])<hi]
            samples=sum(int(r['sampled_pixels']) for r in work)
            if not samples:continue
            scene['work'][stage]={'sampled_pixels':samples,'sampled_frames':len(work),
                'calls_per_sampled_pixel':{key:sum(int(r[key]) for r in work)/samples for key in work[0]
                    if key not in ('frame','width','height','stage','sampled_pixels')}}
        report['scenes'][name]=scene
        expected={'primary'}
        if 'pt' in name:expected|={'pt_initial','pt_temporal','pt_shifts','pt_spatial','pt_resolve'}
        else:expected.add('indirect')
        if requested and not expected.issubset(scene['work']):
            raise ValueError(f'{name}: missing requested sampled stages {expected-set(scene["work"])}')
    (destination/'transport-summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:{'frames':v['frames'],'recorded_ms':v['gpu']['recorded_ms'],'work':v['work']} for k,v in report['scenes'].items()},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path)
    summarize(parser.parse_args().destination)
