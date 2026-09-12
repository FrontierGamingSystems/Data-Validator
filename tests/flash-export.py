"""Exercise the workbook code actually embedded in index.html. Requires openpyxl."""
import io,json,pathlib,re,subprocess,copy
import openpyxl
ROOT=pathlib.Path(__file__).resolve().parents[1]
source=ROOT.joinpath('index.html').read_text(encoding='utf-8')
builder=json.loads(re.search(r'const XLSX_BUILDER_PY=(.*?);\n',source).group(1))
scope={};exec(compile(builder,'embedded_workbook.py','exec'),scope)
snap=json.loads(subprocess.check_output(['node',str(ROOT/'tests/export-fixture.js')]))
def workbook(s):return openpyxl.load_workbook(io.BytesIO(scope['build'](s,None)),data_only=True)
def values(w):return {r[0].value:r[3].value for r in w['Flash Runners'] if len(r)>3 and r[0].value}
for legacy in (False,True):
    s=copy.deepcopy(snap)
    if legacy:s.pop('flash_presales')
    w=workbook(s);v=values(w)
    assert v['Sold during pre-orders']==220==snap['totals']['fxSoldPre']
    assert v['Remainder']==5695==snap['totals']['fxRemainder']
    assert v['Over/(Short) dollars']==0==snap['totals']['fxOverShort']
    details=[tuple(c.value for c in r[:3]) for r in w['Flash Runners']]
    assert ('Casino City',80,160) in details
    assert ('Big Fish',60,60) in details
s=copy.deepcopy(snap);s['state']['runners'][0]['checkouts']=[5600]
w=workbook(s)
assert values(w)['Over/(Short) dollars']==-95
# The audit must not claim flash balances when the money differs.
audit=[tuple(c.value for c in row) for row in w['Audit']]
flash=[r for r in audit if 'Flash tickets reconcile' in r]
assert flash and any('95' in str(x) for x in flash[0]),flash
assert flash[0][1]=='FAIL',flash
print('PASS exported report: $1/$2 amounts match the app, quantities stay separate, older files work, shortages are reported')

historical=json.loads(subprocess.check_output(['node',str(ROOT/'tests/export-fixture.js'),'--historical']))
for legacy in (False,True):
    s=copy.deepcopy(historical)
    if legacy:s.pop('flash_presales')
    w=workbook(s)
    assert values(w)['Sold during pre-orders']==400==historical['totals']['fxSoldPre']
    details=[tuple(c.value for c in r[:3]) for r in w['Flash Runners']]
    assert ('Diamonds & Emeralds',40,80) in details
print('PASS real August 4 export and older saved files: $2 flash sales retain their correct value')
