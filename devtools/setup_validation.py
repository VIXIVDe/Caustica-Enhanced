"""Prepare and optionally compile/run the maintained synthetic validation fixture."""
from pathlib import Path
import argparse
import json
import hashlib
import zipfile
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def java_arg(value):
    return '"' + str(value).replace('\\', '/').replace('"', '\\"') + '"'


def prepare(repo, toolchain, destination, assets, jar_override=None):
    repo, toolchain, destination = map(lambda p: Path(p).resolve(), (repo, toolchain, destination))
    if not destination.is_relative_to(HERE.resolve()):
        raise ValueError('Validation output must remain inside devtools.')
    if destination.exists():
        raise ValueError(f'Output already exists: {destination}. Choose a new --output to preserve captures.')
    manifest = json.loads((HERE / 'templates/runtime.json').read_text(encoding='utf-8-sig'))
    props = dict(line.split('=', 1) for line in (repo / 'gradle.properties').read_text().splitlines()
                 if '=' in line and not line.startswith('#'))
    jar = repo / 'build/libs' / f"{props['archives_base_name']}-{props['mod_version']}.jar"
    if not jar.exists():
        jar = repo / 'build/libs' / f"{props['archives_base_name']} v.{props['mod_version'].rsplit('.', 1)[-1]}.jar"
    if jar_override is not None: jar=Path(jar_override).resolve()
    mod, instance = destination / 'mod', destination / 'instance'
    cp = []
    for entry in manifest['classpath']:
        entry = entry.format(repo=repo.as_posix(), toolchain=toolchain.as_posix(), mod=mod.as_posix())
        path = Path(entry)
        if '/build/libs/' in entry and entry.endswith('.jar') and path.is_relative_to(repo):
            path = jar
        if path != mod and not path.exists():
            raise FileNotFoundError(f'Classpath input missing: {path}. Build the current repository first.')
        cp.append(path.as_posix())
    assets = Path(assets or manifest['assets_directory']).resolve()
    if not assets.is_dir():
        raise FileNotFoundError(f'Minecraft asset directory missing: {assets}; pass --assets.')
    destination.mkdir(parents=True)
    shutil.copytree(HERE / 'fixture', instance, ignore=shutil.ignore_patterns('session.lock'))
    shutil.copytree(HERE / 'templates', mod, ignore=shutil.ignore_patterns('runtime.json'))
    (mod / 'fabric.mod.json').write_text(json.dumps({
        'schemaVersion': 1, 'id': 'caustica_validation', 'version': '1.0', 'environment': 'client',
        'entrypoints': {'client': ['dev.comfyfluffy.caustica.rt.terrain.ValidationClient']},
        'mixins': ['benchmark.mixins.json']}, indent=2), encoding='utf-8')
    classpath = ';'.join(cp)
    compile_classpath = ';'.join(entry for entry in cp
                                 if not ('/org.lwjgl/' in entry and '-natives-' in entry))
    compile_args = ['--release', '25', '-cp', java_arg(compile_classpath), '-d', java_arg(mod)]
    compile_args += [java_arg(mod / name) for name in
                     ('ValidationClient.java', 'ValidationProbe.java', 'BenchmarkCameraMixin.java', 'ParallaxProbe.java', 'PerformanceLimiterMixin.java')]
    launch_args = [
        '-Dcaustica.rt.gpuTimings=gpu-timings-validation.csv', '-Xmx4G', '-Xss16m',
        '--enable-native-access=ALL-UNNAMED', '-Dfabric.development=true',
        '-Dcaustica.validation.probeShader=' + java_arg(mod / 'gi_probe.spv'),
        '-Dcaustica.validation.parallaxShader=' + java_arg(mod / 'parallax_probe.spv'),
        '-Dcaustica.rt.frameStats=true',
        '-cp', java_arg(classpath), 'net.fabricmc.loader.impl.launch.knot.KnotClient',
        '--username', manifest['username'], '--accessToken', '0',
        '--version', props['minecraft_version'], '--assetIndex', manifest['asset_index'],
        '--assetsDir', java_arg(assets), '--graphicsBackend', 'vulkan',
        '--width', str(manifest['width']), '--height', str(manifest['height'])]
    (destination / 'compile.args').write_text('\n'.join(compile_args) + '\n', encoding='utf-8')
    (destination / 'launch.args').write_text('\n'.join(launch_args) + '\n', encoding='utf-8')
    with zipfile.ZipFile(jar) as archive:
        artifact_version=json.loads(archive.read('fabric.mod.json'))['version']
        diagnostic='caustica-transport-diagnostics.json' in archive.namelist()
    (destination / 'inputs.json').write_text(json.dumps({
        'repository': str(repo), 'version': artifact_version, 'toolchain': str(toolchain),
        'artifact':str(jar),'artifact_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
        'transport_diagnostics':diagnostic,
        'assets': str(assets), 'classpath': cp, 'fixture': str(HERE / 'fixture')}, indent=2), encoding='utf-8')
    return destination


def compile_helpers(destination):
    inputs = json.loads((destination / 'inputs.json').read_text(encoding='utf-8'))
    toolchain = Path(inputs['toolchain'])
    candidates = {'javac': shutil.which('javac'),
                  'slangc': toolchain / 'slang/bin/slangc.exe',
                  'spirv-val': toolchain / 'spirv-nmake/tools/spirv-val.exe'}
    programs = {}
    for name, candidate in candidates.items():
        if candidate and Path(candidate).is_file():
            programs[name] = str(candidate)
        else:
            programs[name] = shutil.which(name)
        if not programs[name]:
            raise FileNotFoundError(f'{name} is unavailable. Check --toolchain and use Java 25.')
    mod = destination / 'mod'
    shader_root = Path(inputs['repository']) / 'shaders'
    includes = [item for folder in sorted({source.parent for source in shader_root.rglob('*.slang')})
                for item in ('-I', str(folder))]
    for shader in ('gi_probe', 'parallax_probe'):
        subprocess.run([programs['slangc'], str(mod / (shader + '.comp.slang')), *includes,
                        '-target', 'spirv', '-profile', 'spirv_1_5', '-matrix-layout-column-major',
                        '-warnings-as-errors', 'all', '-warnings-disable', '41012',
                        '-o', str(mod / (shader + '.spv'))], check=True)
        subprocess.run([programs['spirv-val'], '--target-env', 'vulkan1.2', str(mod / (shader + '.spv'))], check=True)
    compile_paths = [entry for entry in inputs['classpath']
                     if not ('/org.lwjgl/' in entry and '-natives-' in entry)]
    compile_args = ['--release', '25', '-cp', java_arg(';'.join(compile_paths)), '-d', java_arg(mod)]
    compile_args += [java_arg(mod / name) for name in
                     ('ValidationClient.java', 'ValidationProbe.java', 'BenchmarkCameraMixin.java', 'ParallaxProbe.java', 'PerformanceLimiterMixin.java')]
    (destination / 'compile.args').write_text('\n'.join(compile_args) + '\n', encoding='utf-8')
    completed = subprocess.run([programs['javac'], '@' + str(destination / 'compile.args')],
                               capture_output=True, text=True, check=False)
    if completed.stdout:
        print(completed.stdout, end='')
    if completed.stderr:
        print(completed.stderr, end='', file=sys.stderr)
        if 'An exception has occurred in the compiler' in completed.stderr:
            raise RuntimeError('Java compiler reported an internal exception.')
    completed.check_returncode()
    for relative in ('dev/comfyfluffy/caustica/rt/terrain/ValidationClient.class',
                     'dev/comfyfluffy/caustica/rt/terrain/ValidationProbe.class',
                     'dev/comfyfluffy/caustica/validation/mixin/BenchmarkCameraMixin.class'):
        data = (mod / relative).read_bytes()
        if data[:4] != b'\xca\xfe\xba\xbe' or int.from_bytes(data[6:8], 'big') != 69:
            raise RuntimeError(f'Expected Java 25 helper class: {relative}')


def enable_profile(destination):
    shutil.copyfile(HERE / 'templates/PerformanceClient.java', destination / 'mod/ValidationClient.java')
    launch=destination/'launch.args'
    launch.write_text('-Dcaustica.validation.performance=true\n'+launch.read_text())
    options=destination / 'instance/options.txt'
    options.write_text(options.read_text().replace('enableVsync:true','enableVsync:false').replace('maxFps:120','maxFps:260').replace('inactivityFpsLimit:"afk"','inactivityFpsLimit:"minimized"'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT / 'mod')
    parser.add_argument('--toolchain', type=Path, default=ROOT / 'toolchain')
    parser.add_argument('--output', type=Path, default=HERE / 'work/current')
    parser.add_argument('--assets', type=Path)
    parser.add_argument('--compile', action='store_true', help='Compile helpers and validate probe shader.')
    parser.add_argument('--jar',type=Path,help='Frozen comparison artifact; source is not modified.')
    parser.add_argument('--profile', action='store_true', help='Use the timed PBR/reconstruction/cloud/fog pass matrix.')
    parser.add_argument('--run', action='store_true', help='Compile and launch the isolated synthetic fixture.')
    args = parser.parse_args()
    destination = prepare(args.repo, args.toolchain, args.output, args.assets,args.jar)
    if args.profile:
        enable_profile(destination)
    print(f'Prepared synthetic validation: {destination}', flush=True)
    if args.compile or args.run:
        compile_helpers(destination)
        print('Compiled Java helpers and validated GI shader.', flush=True)
    if args.run:
        subprocess.run(['java', '@' + str(destination / 'launch.args')], cwd=destination / 'instance', check=True)


if __name__ == '__main__':
    main()
