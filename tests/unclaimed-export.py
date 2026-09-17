"""Use the app's real snapshots and embedded exporter, without saving any workbook."""
import io,json,pathlib,re,subprocess
import openpyxl
ROOT=pathlib.Path(__file__).resolve().parents[1]
source=(ROOT/'index.html').read_text(encoding='utf-8')
code=json.loads(re.search(r'const XLSX_BUILDER_PY=(.*?);\n',source).group(1))
scope={};exec(compile(code,'embedded_workbook.py','exec'),scope)
cases=json.loads(subprocess.check_output(['node',str(ROOT/'tests/unclaimed-flash.js'),'--json']))
def row_value(w,label,column):
    matches=[row[column-1].value for row in w if row[0].value==label]
    assert len(matches)==1,(w.title,label,matches)
    return matches[0]
baseline={}
for case in cases:
    s=case['snap'];t=s['totals']; reduction=abs(case['value'])
    w=openpyxl.load_workbook(io.BytesIO(scope['build'](s,None)),data_only=True)
    assert w['Paymaster']['B24'].value==-reduction
    assert w['Paymaster']['C24'].value=='deducted from payouts'
    assert row_value(w['Summary'],'Flash Game Payout Un-Claimed',3)==-reduction
    assert row_value(w['Payouts'],'Flash Game Payout Un-Claimed',3)==-reduction
    assert row_value(w['Summary'],'TOTAL PAYOUTS',3)==t['payouts']
    assert w['Paymaster']['B45'].value==t['stationOS']['Paymaster']
    flash_total=next(row[4].value for row in w['Summary'] if len(row)>5 and row[5].value=='Flash Total')
    if not reduction: baseline[case['hall']]=(w['Paymaster']['B43'].value,flash_total)
    assert w['Paymaster']['B43'].value==baseline[case['hall']][0]+reduction
    assert flash_total==baseline[case['hall']][1]-reduction
print('PASS Excel: Paymaster, Summary, Payouts, Flash Total, expected cash and over/short agree for both halls and both input signs')
