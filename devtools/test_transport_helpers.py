"""Reject invalid captures before they can become performance evidence."""
import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import run_profile, summarize_transport, build_transport_diagnostics as diagnostics

class CaptureContracts(unittest.TestCase):
    def test_production_cannot_request_counters(self):
        work=Path(__file__).resolve().parent/'work';work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as folder:
            target=Path(folder)
            (target/'inputs.json').write_text(json.dumps({'transport_diagnostics':False}))
            with patch.object(run_profile.subprocess,'Popen') as launch:
                with self.assertRaisesRegex(ValueError,'diagnostic artifact'):
                    run_profile.run(target,'java',counters=True)
                launch.assert_not_called()

    def test_requested_empty_counter_capture_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent/'work') as folder:
            target=Path(folder);instance=target/'instance';instance.mkdir()
            markers='PASS: transport subset\n'
            for i,name in enumerate(('nrd-pom-on','nrd-pt','outdoor-clear','outdoor-clouds')):
                markers+=f'frame={i*100} MEASURE_BEGIN {name}\nframe={i*100+90} MEASURE_END {name}\n'
            (instance/'lighting-progress.txt').write_text(markers)
            (instance/'gpu-timings-validation.csv').write_text('frame,recorded_ms\n')
            (target/'run-process.json').write_text(json.dumps({'counters_requested':True}))
            with self.assertRaisesRegex(ValueError,'capture is empty'):
                summarize_transport.summarize(target)

    def test_changed_source_seal_rejected_before_compilation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent/'work') as folder:
            jar=Path(folder)/'base.jar';jar.write_bytes(b'placeholder')
            jar.with_suffix('.build-manifest.json').write_text(json.dumps({
                'production_sha256':diagnostics.hashlib.sha256(jar.read_bytes()).hexdigest(),
                'sources':{'stale.slang':'old'}}))
            with patch.object(diagnostics.subprocess,'run') as compile:
                with self.assertRaisesRegex(ValueError,'sealed production build'):
                    diagnostics.build(jar,Path(folder)/'output')
                compile.assert_not_called()

if __name__=='__main__':unittest.main()
