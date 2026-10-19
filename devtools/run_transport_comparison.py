"""Three paired production captures with reversed version order; never change quality budgets."""
import argparse, json, subprocess, time
from pathlib import Path
import setup_validation, run_profile, summarize_transport, check_signals

ROOT=Path(__file__).resolve().parent.parent

def run(baseline,current,output,java):
    output=Path(output).resolve()
    if not output.is_relative_to(ROOT/'devtools/work') or output.exists():
        raise ValueError('Use a new comparison directory in devtools/work')
    output.mkdir(parents=True)
    order=((current,baseline),(baseline,current),(current,baseline))
    captures=[]
    for pair,visits in enumerate(order,1):
        for visit,artifact in enumerate(visits,1):
            version='current' if artifact==current else 'baseline'
            target=output/f'pair-{pair}-{visit}-{version}'
            # Return CPU/GPU control to the fixture; only this isolated process is launched.
            setup_validation.prepare(ROOT/'mod',ROOT/'toolchain',target,None,artifact)
            setup_validation.enable_profile(target)
            setup_validation.compile_helpers(target)
            print(f'CAPTURE_BEGIN pair={pair} visit={visit} version={version}',flush=True)
            run_profile.run(target,java,transport_only=True)
            summarize_transport.summarize(target)
            quality=check_signals.check(target/'instance/signals-locked',4)
            (target/'instance/signal-validation.json').write_text(json.dumps(quality,indent=2))
            captures.append({'pair':pair,'visit':visit,'version':version,'path':str(target)})
            (output/'comparison-visits.json').write_text(json.dumps(captures,indent=2))
            print(f'CAPTURE_END pair={pair} visit={visit} version={version}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baseline',type=Path);p.add_argument('current',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--java',required=True);a=p.parse_args();run(a.baseline.resolve(),a.current.resolve(),a.output,a.java)
