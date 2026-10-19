"""Build an optional sampled-work JAR from a production artifact and maintained Slang sources."""
from pathlib import Path
import argparse, hashlib, json, subprocess, zipfile

ROOT=Path(__file__).resolve().parent.parent

def source_fingerprint(repo):
    files=list((repo/'shaders').rglob('*.slang'))+list((repo/'src/main').rglob('*'))
    files += [repo/'build.gradle',repo/'gradle.properties']
    return {str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files) if p.is_file()}

def seal(jar):
    jar=Path(jar).resolve();repo=ROOT/'mod'
    props=dict(line.split('=',1) for line in (repo/'gradle.properties').read_text().splitlines()
               if '=' in line and not line.startswith('#'))
    expected=repo/'build/libs'/f"{props['archives_base_name']}-{props['mod_version']}.jar"
    if jar!=expected:raise ValueError('Seal only the current completed production build')
    sources=source_fingerprint(repo)
    if any((repo/p).stat().st_mtime>jar.stat().st_mtime for p in sources):
        raise ValueError('Production inputs changed after artifact; rebuild before sealing')
    with zipfile.ZipFile(jar) as archive:
        if json.loads(archive.read('fabric.mod.json'))['version']!=props['mod_version']:
            raise ValueError('Artifact version does not match current inputs')
        if 'dev/comfyfluffy/caustica/rt/RtTransportCounters.class' not in archive.namelist():
            raise ValueError('Production artifact lacks diagnostic integration')
    jar.with_suffix('.build-manifest.json').write_text(json.dumps({
        'production_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),'sources':sources},indent=2))

def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    repo=ROOT/'mod'
    sealed=json.loads(jar.with_suffix('.build-manifest.json').read_text())
    if sealed['production_sha256']!=hashlib.sha256(jar.read_bytes()).hexdigest() or sealed['sources']!=source_fingerprint(repo):
        raise ValueError('Diagnostic sources do not match the sealed production build')
    if not output.is_relative_to(ROOT/'devtools/work') or output.exists():
        raise ValueError('Use a new devtools/work diagnostic destination')
    output.mkdir(parents=True)
    repo=ROOT/'mod';source=repo/'shaders'
    includes=sorted({p.parent for p in source.rglob('*.slang')})
    names=['primary.rgen','indirect.rgen','restir_temporal.rgen','restir_gi_initial.rgen',
           'restir_gi_temporal.rgen']+[f'restir_pt_{stage}.rgen' for stage in ('initial','temporal','shifts','spatial','resolve')]
    replacements={};commands=[]
    for name in names:
        src=source/'pipelines/world'/f'{name}.slang';target=output/f'{name}.spv'
        flags=['-O3','-g1'] if name.startswith('restir_pt_') else []
        command=['slangc',str(src),'-target','spirv','-profile','spirv_1_5',
                 '-matrix-layout-column-major','-warnings-as-errors','all','-warnings-disable','41012','-g',
                 '-DCAUSTICA_TRANSPORT_DIAGNOSTICS']
        for inc in [src.parent]+[p for p in includes if p!=src.parent]:command+=['-I',str(inc)]
        command+=flags+['-o',str(target)];commands.append(command)
        subprocess.run(command,check=True)
        subprocess.run(['spirv-val','--target-env','vulkan1.2',str(target)],check=True)
        replacements[f'caustica/shaders/pipelines/world/{name}.spv']=target.read_bytes()
        print('Validated diagnostic shader:',name,flush=True)
    manifest={'production_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
              'scope':'Ordinary fallback NRD, DI/GI and PT; cache/RR/SER indirect variants remain uninstrumented.',
              'define':'CAUSTICA_TRANSPORT_DIAGNOSTICS',
              'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*.slang')},
              'commands':commands}
    diagnostic=output/f'{jar.stem}-transport-diagnostics.jar'
    with zipfile.ZipFile(jar) as original,zipfile.ZipFile(diagnostic,'w',zipfile.ZIP_DEFLATED) as result:
        for entry in original.infolist():
            contents=replacements.pop(entry.filename,None)
            if contents is None:contents=original.read(entry.filename)
            if entry.filename=='fabric.mod.json':
                mod=json.loads(contents);mod['version']+='-transport-diagnostics';contents=json.dumps(mod).encode()
            result.writestr(entry,contents)
        if replacements:raise ValueError('Shader resource missing in base JAR: '+str(list(replacements)))
        result.writestr('caustica-transport-diagnostics.json',json.dumps(manifest,indent=2))
    manifest['diagnostic_sha256']=hashlib.sha256(diagnostic.read_bytes()).hexdigest()
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(diagnostic,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('jar',type=Path);parser.add_argument('output',type=Path,nargs='?');parser.add_argument('--seal',action='store_true')
    args=parser.parse_args()
    if args.seal:seal(args.jar)
    elif args.output is not None:build(args.jar,args.output)
    else:parser.error('Provide output or --seal')
