"""Combine completed, unthrottled intervals from resumed isolated performance runs."""
from pathlib import Path
import argparse,csv,json,re,shutil

def combine(sources,destination):
    destination=destination.resolve()
    if not destination.is_relative_to(Path(__file__).resolve().parent/'work') or destination.exists():
        raise ValueError('Use a new destination inside devtools/work')
    instance=destination/'instance';instance.mkdir(parents=True)
    all_rows=[];all_markers=[];names=set();builds=[];telemetry=[];provenance=[]
    for index,source in enumerate(sources):
        source=source.resolve();p=source/'instance';offset=index*1000000
        marker=(p/'lighting-progress.txt').read_text();starts={};windows={}
        for frame,kind,name in re.findall(r'frame=(\d+) MEASURE_(BEGIN|END) (\S+)',marker):
            if kind=='BEGIN': starts[name]=int(frame)
            elif name in starts: windows[name]=(starts[name],int(frame))
        for name in windows:
            if name in names: raise AssertionError('Duplicate completed scene '+name)
            names.add(name)
            begin=re.search(r'frame='+str(windows[name][0])+r' MEASURE_BEGIN '+re.escape(name)+r'[^\n]*',marker).group()
            if 'limit=260 reason=NONE' not in begin: raise AssertionError('Unverified frame limiter '+name)
            shutil.copytree(p/'signals-locked'/name,instance/'signals-locked'/name)
        with (p/'gpu-timings-validation.csv').open() as f:
            for row in csv.DictReader(f):
                if any(a<int(row['frame'])<b for a,b in windows.values()):
                    row['frame']=str(int(row['frame'])+offset);all_rows.append(row)
        for line in marker.splitlines():
            if 'MEASURE_' in line and not any((' '+n+' ') in (line+' ') for n in windows): continue
            all_markers.append(re.sub(r'frame=(\d+)',lambda m:'frame='+str(int(m[1])+offset),line))
        build=p/'gpu-timings-validation.csv.build.csv'
        if build.exists(): builds.extend(csv.DictReader(build.open()))
        with (source/'nvidia-telemetry.csv').open() as f:
            telemetry.extend(r for r in csv.DictReader(f) if all(k is not None and v is not None for k,v in r.items()))
        if index==0:
            shutil.copyfile(p/'gpu-timings-validation.csv.metadata.properties',instance/'gpu-timings-validation.csv.metadata.properties')
            shutil.copyfile(p/'parallax-probe.txt',instance/'parallax-probe.txt')
        provenance.append({'source':str(source),'completed_scenes':list(windows),'frame_offset':offset,
                           'failure':(p/'lighting-failure.txt').read_text() if (p/'lighting-failure.txt').exists() else None})
    if len(names)!=16: raise AssertionError(f'Expected 16 unique completed scenes, got {len(names)}')
    if 'PASS: height probe and complete pass matrix' not in all_markers[-1]:
        if not any('PASS: height probe and complete pass matrix' in m for m in all_markers):raise AssertionError('Final resumed run did not finish')
    def write_csv(path,rows):
        if not rows:return
        with path.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write_csv(instance/'gpu-timings-validation.csv',all_rows)
    write_csv(instance/'gpu-timings-validation.csv.build.csv',builds)
    write_csv(destination/'nvidia-telemetry.csv',telemetry)
    (instance/'lighting-progress.txt').write_text('\n'.join(all_markers)+'\n')
    (destination/'capture-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(f'Combined {len(names)} unthrottled scenes, {len(all_rows)} GPU frames: {destination}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('sources',nargs='+',type=Path)
    a=p.parse_args();combine(a.sources,a.destination)
