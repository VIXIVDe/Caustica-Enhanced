"""Summarize only marked, warmed-up GPU frames; retain fused and overlapping work labels."""
from pathlib import Path
import argparse, csv, json, re
from datetime import datetime
import numpy as np
from exr_reader import read_exr

def summarize(instance):
    instance=Path(instance)
    rows=list(csv.DictReader((instance/'gpu-timings-validation.csv').open()))
    markers=(instance/'lighting-progress.txt').read_text()
    starts={}; intervals={}
    for frame,kind,name in re.findall(r'frame=(\d+) MEASURE_(BEGIN|END) (\S+)',markers):
        if kind=='BEGIN': starts[name]=int(frame)
        elif name in starts: intervals[name]=(starts[name],int(frame))
    if len(intervals)!=16 or 'PASS: height probe and complete pass matrix' not in markers:
        raise AssertionError('The complete 16-scene matrix must finish before summarizing')
    report={'scenes':{},'contracts':[
        'GPU timestamp intervals include dependencies/stalls within each interval, not exclusive shader instruction time.',
        'Material evaluation and inline sky/cloud/fog are fused with world tracing. POM on/off is an incremental controlled comparison, not full material time.',
        'Async upload/AS batch timings overlap graphics and must not be added to graphics frame time.',
        'CPU timeline, device idle/fence, and build submission waits are separate from GPU idle time.',
        'Between-region gaps include Minecraft, presentation, CPU pacing and semaphore waits; they are not proven GPU idle.',
        'Device-local VMA usage/budget may include other allocations; Caustica allocated bytes excludes Minecraft and native reconstruction allocators.'
    ]}
    metadata={}
    for line in (instance/'gpu-timings-validation.csv.metadata.properties').read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1);metadata[k]=v
    report['device_metadata']=metadata
    period=float(metadata['timestampPeriodNs'])
    mask=(1<<int(metadata['timestampValidBits']))-1
    for name,(begin,end) in intervals.items():
        selected=sorted([r for r in rows if begin<int(r['frame'])<end],key=lambda r:int(r['frame']))
        if len(selected)<20: raise AssertionError(f'Insufficient steady frames: {name}: {len(selected)}')
        stats={'frames':len(selected),'first_frame':begin,'last_frame':end}
        for key in selected[0]:
            if key=='frame' or key.endswith('_tick'): continue
            values=np.array([float(r[key]) for r in selected]);values=values[np.isfinite(values)]
            if len(values): stats[key]={'median':float(np.median(values)),'p95':float(np.percentile(values,95)),'max':float(np.max(values))}
        gaps=[]
        for a,b in zip(selected,selected[1:]):
            if int(b['frame'])==int(a['frame'])+1:
                gaps.append(((int(b['graphics_start_tick'])-int(a['graphics_end_tick']))&mask)*period/1e6)
        if gaps: stats['between_regions_ms']={'median':float(np.median(gaps)),'p95':float(np.percentile(gaps,95))}
        report['scenes'][name]=stats
    build=instance/'gpu-timings-validation.csv.build.csv'
    if build.exists():
        records=list(csv.DictReader(build.open()))
        report['async_build']={'batches':len(records),'jobs':sum(int(r['jobs']) for r in records)}
        for key in ('upload_and_as_gpu_ms','executor_completion_wait_ms'):
            values=[float(r[key]) for r in records]
            report['async_build'][key]={'median':float(np.median(values)),'p95':float(np.percentile(values,95)),'max':max(values)}
    names=('nrd-pom-on','nrd-pom-off','nrd-pom-on-repeat')
    images=[read_exr(instance/'signals-locked'/name/'normal-ggx.exr')[...,:3] for name in names]
    change=float(np.mean(np.abs(images[0]-images[1])))
    repeat=float(np.mean(np.abs(images[0]-images[2])))
    if change<1e-5: raise AssertionError('POM did not alter material normal sampling')
    report['parallax']={'on_off_normal_mean_absolute_change':change,'repeat_normal_mean_absolute_change':repeat,
        'gpu_solver_probe':(instance/'parallax-probe.txt').read_text()}
    scenes=report['scenes']
    def median(scene,key): return scenes[scene][key]['median']
    report['controlled_differences_ms']={
        'pom_primary_increment':(median('nrd-pom-on','primary_ms')+median('nrd-pom-on-repeat','primary_ms'))*.5-median('nrd-pom-off','primary_ms'),
        'pbr_primary_increment':(median('nrd-pom-off','primary_ms')+median('nrd-material-repeat','primary_ms'))*.5-median('nrd-material-bypass','primary_ms'),
        'contract':'Differences of warmed-up primary-dispatch medians in the same static scene. Incremental estimates, not exclusive material instruction times; includes changed traversal/shading interactions.'
    }
    telemetry=instance.parent/'nvidia-telemetry.csv'
    if telemetry.exists():
        samples=[{k.strip():v.strip() for k,v in r.items()} for r in csv.DictReader(telemetry.open()) if all(k is not None and v is not None for k,v in r.items())]
        report['system_telemetry']={'samples':len(samples),'contract':'System-wide samples include startup, captures, compiler stalls and all processes, not just marked steady rendering.'}
        for key in samples[0] if samples else []:
            values=[]
            for sample in samples:
                try: values.append(float(sample[key]))
                except ValueError: pass
            if values: report['system_telemetry'][key]={'median':float(np.median(values)),'p95':float(np.percentile(values,95)),'min':min(values),'max':max(values)}
        windows={};wall_starts={}
        for instant,kind,name in re.findall(r'time=(\S+) frame=\d+ MEASURE_(BEGIN|END) (\S+)',markers):
            stamp=datetime.fromisoformat(instant.replace('Z','+00:00')).timestamp()
            if kind=='BEGIN': wall_starts[name]=stamp
            elif name in wall_starts: windows[name]=(wall_starts[name],stamp)
        for name,(begin,end) in windows.items():
            selected=[]
            for sample in samples:
                try: stamp=datetime.strptime(sample['timestamp'],'%Y/%m/%d %H:%M:%S.%f').astimezone().timestamp()
                except (KeyError,ValueError): continue
                if begin<stamp<end: selected.append(sample)
            telemetry_stats={'samples':len(selected)}
            for key in samples[0] if samples else []:
                values=[]
                for sample in selected:
                    try: values.append(float(sample[key]))
                    except ValueError: pass
                if values: telemetry_stats[key]={'median':float(np.median(values)),'min':min(values),'max':max(values)}
            report['scenes'][name]['system_telemetry']=telemetry_stats
    destination=instance.parent/'performance-summary.json'
    destination.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'scenes':len(intervals),'parallax':report['parallax'],'output':str(destination)},indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('instance',type=Path)
    summarize(p.parse_args().instance)
