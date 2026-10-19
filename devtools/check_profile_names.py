"""Verify literal performance stages/counters match the diagnostic registry."""
from pathlib import Path
import json,re

root=Path(__file__).resolve().parents[1]/'mod/src/main/java'
registry=(root/'dev/comfyfluffy/caustica/rt/RtFrameStats.java').read_text()
stages,counters=re.search(r'FRAME = new Profile\("frame",\s*new String\[\] \{(.*?)\},\s*new String\[\] \{(.*?)\}',registry,re.S).groups()
names={'stage':set(re.findall(r'"([^\"]+)"',stages)),
       'count':set(re.findall(r'"([^\"]+)"',counters))}
calls=[]
for path in root.rglob('*.java'):
    for kind,name in re.findall(r'RtFrameStats\.FRAME\.(stage|count)\("([^\"]+)"',path.read_text()):
        if name not in names[kind]: raise AssertionError(f'{path}: unregistered {kind} {name}')
        calls.append((kind,name))
print(json.dumps({'literal_calls_checked':len(calls),'registered_stages':len(names['stage']),
                  'registered_counters':len(names['count']),'status':'PASS'},indent=2))
