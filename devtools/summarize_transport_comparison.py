"""Report repeated paired GPU differences; snapshots are checks, not a converged quality reference."""
import argparse, csv, datetime as dt, json, re
from pathlib import Path
import numpy as np

def summarize(folder):
    folder=Path(folder);visits=json.loads((folder/'comparison-visits.json').read_text())
    if len(visits)!=6:raise ValueError('Require all three completed pairs')
    pairs={};artifacts={};contexts=[]
    for visit in visits:
        target=Path(visit['path']);inputs=json.loads((target/'inputs.json').read_text())
        summary=json.loads((target/'transport-summary.json').read_text())
        artifact=inputs['artifact_sha256']
        if visit['version'] in artifacts and artifacts[visit['version']]!=artifact:
            raise ValueError('Artifact changed across visits')
        artifacts[visit['version']]=artifact
        for name,scene in summary['scenes'].items():
            for dimension in ('internal_width','internal_height'):
                expected=854 if dimension=='internal_width' else 480
                if scene['gpu'][dimension]['median']!=expected or scene['gpu'][dimension]['p95']!=expected:
                    raise ValueError('Resolution mismatch')
        pairs.setdefault(visit['pair'],{})[visit['version']]=summary
        with (target/'nvidia-telemetry.csv').open() as source:
            telemetry=[{k.strip():v.strip() for k,v in row.items()} for row in csv.DictReader(source)]
        spans={};begins={}
        markers=(target/'instance/lighting-progress.txt').read_text()
        for timestamp,kind,name in re.findall(r'time=(\S+) frame=\d+ MEASURE_(BEGIN|END) (\S+)',markers):
            time=dt.datetime.fromisoformat(timestamp.replace('Z','+00:00')).timestamp()
            if kind=='BEGIN':begins[name]=time
            elif name in begins:spans[name]=(begins[name],time)
        sampled={}
        for name,(lo,hi) in spans.items():
            rows=[r for r in telemetry if lo<dt.datetime.strptime(r['timestamp'],'%Y/%m/%d %H:%M:%S.%f').timestamp()<hi]
            sampled[name]={'samples':len(rows)}
            for key in ('temperature.gpu','clocks.current.graphics [MHz]','memory.used [MiB]','utilization.gpu [%]'):
                values=[]
                for row in rows:
                    try:values.append(float(row[key]))
                    except ValueError:pass
                if values:sampled[name][key]={'median':float(np.median(values)),'max':max(values)}
        contexts.append({**visit,'artifact':artifact,'telemetry':sampled})
    report={'artifacts':artifacts,'visits':contexts,'scenes':{},'limits':[
        'Three visits per version are the replicate unit; individual frames are correlated.',
        'Fixed 854x480 internal/output resolution, 1 SPP and 2 bounces; not a city/DH or high-resolution result.',
        'Raw/reconstructed finite snapshots and native energy regressions do not establish converged noise, detail or dynamic ghosting equivalence.',
        'No hardware profiler attribution is available; work counters are separately captured.'
    ]}
    for name in pairs[1]['baseline']['scenes']:
        entries={}
        for key in ('recorded_ms','graphics_measured_ms','indirect_ms','pt_initial_ms','pt_temporal_ms','pt_shifts_ms','pt_spatial_ms','pt_resolve_ms'):
            if key not in pairs[1]['baseline']['scenes'][name]['gpu']:continue
            entry={}
            for statistic in ('median','p95'):
                base=[];current=[];changes=[]
                for pair in sorted(pairs):
                    b=pairs[pair]['baseline']['scenes'][name]['gpu'][key][statistic]
                    c=pairs[pair]['current']['scenes'][name]['gpu'][key][statistic]
                    base.append(b);current.append(c);changes.append(100*(c/b-1))
                entry[statistic]={'baseline_ms':base,'current_ms':current,
                    'paired_change_percent':changes,'median_change_percent':float(np.median(changes))}
            entries[key]=entry
        report['scenes'][name]=entries
    (folder/'paired-summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({name:data['recorded_ms'] for name,data in report['scenes'].items()},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);summarize(p.parse_args().folder)
