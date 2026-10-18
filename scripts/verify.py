"""Independent numeric and artifact checks; fails loudly instead of repairing results."""
from pathlib import Path
import csv,json,hashlib
from decimal import Decimal
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'reports/results.json').read_text(encoding='utf8'))
df=pd.read_csv(ROOT/'data/flood.csv')
split=json.loads((ROOT/'reports/splits.json').read_text(encoding='utf8'))
assert len(set(split['train_csv_rows'])&set(split['test_csv_rows']))==0
assert set(split['train_csv_rows'])|set(split['test_csv_rows'])==set(range(2,len(df)+2))
assert sorted(x for fold in split['cv_validation_train_positions'] for x in fold)==list(range(d['train_n']))
assert hashlib.sha256((ROOT/'data/flood.csv').read_bytes()).hexdigest()==d['source']['sha256']
assert len(d['features'])==20 and 'FloodProbability' not in d['features']
p=pd.read_csv(ROOT/'reports/test_predictions.csv')
X=df.iloc[p.csv_row.to_numpy()-2][d['features']].to_numpy()
for name,m in d['exports'].items():
    np.testing.assert_allclose(X@np.array(m['coef'])+m['intercept'],p[name],atol=1e-12)
    r=next(r for r in d['models'] if r['name']==name)
    err=p.actual-p[name]
    assert abs(np.sqrt(np.mean(err**2))-r['test']['rmse'])<1e-12
    assert abs(np.mean(abs(err))-r['test']['mae'])<1e-12
assert d['diagnostics']['degenerate_residuals']
assert 'interval' not in d['exports']['OLS']
assert all(d['diagnostics'][key] is None for key in ['breusch_pagan_p','jarque_bera_p','reset_p','ols_pi_coverage'])
assert 'OLS_PI_low' not in p
records=csv.DictReader((ROOT/'data/flood.csv').open(encoding='utf8'))
assert all(sum(Decimal(v) for k,v in r.items() if k!='FloodProbability')/200==Decimal(r['FloodProbability']) for r in records)
checks=['disjoint and exhaustive split','five fold coverage','dataset hash','no target in features','all linear export predictions','independent RMSE/MAE','degenerate inference suppression','50000 exact Decimal formula checks']
out={'passed':True,'checks':checks,'models_checked':len(d['exports']),'test_rows':len(p)}
(ROOT/'reports/verification.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out,indent=2))
