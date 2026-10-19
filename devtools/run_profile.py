"""Run only the prepared isolated instance, recording system-wide NVIDIA telemetry."""
import argparse, hashlib, json, subprocess, time, zipfile
from pathlib import Path

def run(destination,java,resume_rr=False,transport_only=False,counters=False):
    destination=Path(destination).resolve()
    if not destination.is_relative_to(Path(__file__).resolve().parent/'work'):
        raise ValueError('Expected prepared devtools/work instance')
    instance=destination/'instance'
    inputs=json.loads((destination/'inputs.json').read_text())
    if counters and not inputs.get('transport_diagnostics',False):
        raise ValueError('Counter capture requires a verified transport diagnostic artifact')
    artifact=Path(inputs['artifact'])
    if hashlib.sha256(artifact.read_bytes()).hexdigest()!=inputs['artifact_sha256']:
        raise ValueError('Prepared artifact changed; prepare a new capture instance')
    if counters:
        with zipfile.ZipFile(artifact) as archive:
            if 'caustica-transport-diagnostics.json' not in archive.namelist():
                raise ValueError('Artifact does not contain transport diagnostics')
    telemetry=None
    try:
        telemetry=subprocess.Popen(['nvidia-smi',
            '--query-gpu=timestamp,name,driver_version,memory.total,memory.used,utilization.gpu,utilization.memory,temperature.gpu,power.draw,clocks.current.graphics,clocks.current.memory',
            '--format=csv,nounits','--loop=1','--filename='+str(destination/'nvidia-telemetry.csv')],
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        with (destination/'runtime.log').open('w',encoding='utf-8') as output:
            arguments=[java]+(['-Dcaustica.validation.resumeRr=true'] if resume_rr else [])+(['-Dcaustica.validation.transportOnly=true'] if transport_only else [])+(['-Dcaustica.rt.transportCounters='+str(instance/'transport-counts.csv')] if counters else [])+['@'+str(destination/'launch.args')]
            process=subprocess.Popen(arguments,cwd=instance,stdout=output,stderr=subprocess.STDOUT)
            (destination/'run-process.json').write_text(json.dumps({'pid':process.pid,'start_unix':time.time(),'java':java,'counters_requested':counters,'transport_only':transport_only}))
            code=process.wait()
        if code: raise RuntimeError(f'Validation process exit {code}; see runtime.log')
        if (instance/'lighting-failure.txt').exists(): raise RuntimeError((instance/'lighting-failure.txt').read_text())
        if counters and not (instance/'transport-counts.csv').exists():
            raise RuntimeError('Requested counter capture produced no counter file')
    finally:
        if telemetry is not None:
            telemetry.terminate();telemetry.wait(timeout=15)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--java',default='java');p.add_argument('--resume-rr',action='store_true');p.add_argument('--transport-only',action='store_true');p.add_argument('--counters',action='store_true');a=p.parse_args();run(a.destination,a.java,a.resume_rr,a.transport_only,a.counters)
