"""HW2 reproducible regression analysis. Run from any directory with Python 3.12+."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
from pathlib import Path
import hashlib, json, platform, csv
from decimal import Decimal
import numpy as np
import pandas as pd
import scipy.stats as stats
import sklearn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, linear_reset
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.feature_selection import RFE, SelectKBest, f_regression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

ROOT = Path(__file__).resolve().parent
SEED = 711405612
TARGET = 'FloodProbability'

def metrics(y, pred):
    return dict(rmse=float(np.sqrt(mean_squared_error(y,pred))), mae=float(mean_absolute_error(y,pred)), mse=float(mean_squared_error(y,pred)), r2=float(r2_score(y,pred)))

def pipeline(model, selection='passthrough'):
    return Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('select',selection),('model',model)])

def candidates():
    return [
        ('Mean baseline',pipeline(DummyRegressor()),{}),
        ('OLS',pipeline(LinearRegression()),{}),
        ('Ridge',pipeline(Ridge()),{'model__alpha':[0.01,1,100,1000]}),
        ('Lasso',pipeline(Lasso(max_iter=20000,tol=1e-9)),{'model__alpha':[1e-6,1e-5,1e-4,1e-3,1e-2]}),
        ('SelectKBest + OLS',pipeline(LinearRegression(),SelectKBest(f_regression)),{'select__k':[5,10,14,16,18,20]}),
        ('RFE + OLS',pipeline(LinearRegression(),RFE(LinearRegression(),step=1)),{'select__n_features_to_select':[5,10,14,16,18,20]}),
        ('Histogram boosting',pipeline(HistGradientBoostingRegressor(random_state=SEED,early_stopping=True,max_iter=200)),{'model__max_leaf_nodes':[15,31]})
    ]

def main():
    for directory in ['reports','site/assets','site/downloads']:
        (ROOT/directory).mkdir(parents=True,exist_ok=True)
    raw = (ROOT/'data/flood.csv').read_bytes()
    source = json.loads((ROOT/'data/source.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(raw).hexdigest() == source['sha256'], 'Dataset fingerprint differs'
    df = pd.read_csv(ROOT/'data/flood.csv')
    assert TARGET in df and df.shape[1]==21
    if not all(pd.api.types.is_numeric_dtype(df[c]) for c in df):
        raise ValueError('Expected numeric dataset')
    if np.isinf(df.to_numpy()).any():
        raise ValueError('Infinite values')
    initial_rows=len(df)
    duplicates=int(df.duplicated().sum())
    missing=df.isna().sum().to_dict()
    df=df.drop_duplicates().dropna(subset=[TARGET])
    assert df[TARGET].between(0,1).all()
    X,y=df.drop(columns=TARGET),df[TARGET]
    train_idx,test_idx=train_test_split(np.arange(len(df)),test_size=.2,random_state=SEED)
    Xtr,Xte,ytr,yte=X.iloc[train_idx],X.iloc[test_idx],y.iloc[train_idx],y.iloc[test_idx]
    cv=list(KFold(5,shuffle=True,random_state=SEED).split(Xtr))
    results=[]; searches={}; cv_rows=[]
    for name,est,grid in candidates():
        print('Fitting:',name,flush=True)
        search=GridSearchCV(est,grid,cv=cv,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise',return_train_score=True)
        search.fit(Xtr,ytr)
        searches[name]=search
        i=search.best_index_
        results.append({'name':name,'cv_rmse':float(-search.best_score_),'cv_sd':float(search.cv_results_['std_test_score'][i]),'params':search.best_params_})
        for j,p in enumerate(search.cv_results_['params']):
            cv_rows.append({'name':name,'params':p,'rmse':float(-search.cv_results_['mean_test_score'][j]),'sd':float(search.cv_results_['std_test_score'][j]),'fold_rmse':[float(-search.cv_results_[f'split{k}_test_score'][j]) for k in range(5)]})
    # Lock the choice before reading held-out metrics.
    winner=min([r for r in results if r['name'] not in ['Mean baseline','Histogram boosting']],key=lambda r:r['cv_rmse'])['name']
    overall=min(results,key=lambda r:r['cv_rmse'])['name']
    exports={}
    predictions=pd.DataFrame({'csv_row':df.index[test_idx]+2,'actual':yte.to_numpy()})
    for r in results:
        est=searches[r['name']].best_estimator_
        pred=est.predict(Xte)
        r['test']=metrics(yte,pred)
        r['train']=metrics(ytr,est.predict(Xtr))
        predictions[r['name']]=pred
        model=est.named_steps['model']
        if not hasattr(model,'coef_'): continue
        selector=est.named_steps['select']
        mask=np.ones(X.shape[1],dtype=bool) if selector=='passthrough' else selector.get_support()
        coefficients=np.zeros(X.shape[1]); coefficients[mask]=model.coef_
        scale=est.named_steps['scale']
        raw_coef=coefficients/scale.scale_
        intercept=float(model.intercept_-np.dot(raw_coef,scale.mean_))
        np.testing.assert_allclose(Xte.to_numpy()@raw_coef+intercept,pred,atol=1e-12)
        r['selected']=X.columns[mask].tolist()
        r['nonzero']=int(np.count_nonzero(coefficients))
        r['adjusted_train_r2']=float(1-(1-r['train']['r2'])*(len(Xtr)-1)/(len(Xtr)-int(mask.sum())-1)) if isinstance(model,LinearRegression) else None
        exports[r['name']]={'coef':raw_coef.tolist(),'intercept':intercept,'selected':r['selected'],'medians':est.named_steps['impute'].statistics_.tolist()}
    # Full prespecified OLS diagnostic reference; selected model inference is not substituted.
    ols=sm.OLS(ytr.to_numpy(),sm.add_constant(Xtr.to_numpy())).fit()
    np.testing.assert_allclose(ols.predict(sm.add_constant(Xte.to_numpy())),searches['OLS'].predict(Xte),atol=1e-10)
    exog=sm.add_constant(Xtr.to_numpy())
    bp=het_breuschpagan(ols.resid,exog)
    jb=stats.jarque_bera(ols.resid)
    reset=linear_reset(ols,power=2,use_f=True)
    vif=[float(variance_inflation_factor(exog,i+1)) for i in range(X.shape[1])]
    diagnostic={'breusch_pagan_p':float(bp[1]),'jarque_bera_p':float(jb.pvalue),'reset_p':float(reset.pvalue),'vif':dict(zip(X.columns,vif)),'max_vif':max(vif),'durbin_watson':float(sm.stats.durbin_watson(ols.resid)), 'independence_note':'No time/location/group identifiers; independence cannot be established. Durbin-Watson follows shuffled training order only and is not evidence of temporal independence.'}
    # Detect degenerate residuals: floating-point noise is not an uncertainty model.
    degenerate = bool(np.std(ols.resid) < 1e-10)
    diagnostic['degenerate_residuals'] = degenerate
    if degenerate:
        diagnostic['numerical_only_do_not_interpret'] = {k: diagnostic[k] for k in ['breusch_pagan_p','jarque_bera_p','reset_p','durbin_watson']}
        for k in ['breusch_pagan_p','jarque_bera_p','reset_p','durbin_watson']:
            diagnostic[k] = None
    # Calculate intervals for verification only; suppress if noise variance is degenerate.
    sf=ols.get_prediction(sm.add_constant(Xte.to_numpy())).summary_frame(alpha=.05)
    predictions['OLS_PI_low']=sf.obs_ci_lower.to_numpy(); predictions['OLS_PI_high']=sf.obs_ci_upper.to_numpy()
    diagnostic['ols_pi_coverage']=float(np.mean((yte.to_numpy()>=sf.obs_ci_lower.to_numpy())&(yte.to_numpy()<=sf.obs_ci_upper.to_numpy())))
    diagnostic['ols_pi_mean_width']=float(np.mean(sf.obs_ci_upper-sf.obs_ci_lower))
    if not degenerate:
        exports['OLS']['interval']={'xtx_inverse':ols.normalized_cov_params.tolist(),'sigma2':float(ols.mse_resid),'t_critical':float(stats.t.ppf(.975,ols.df_resid))}
    else:
        predictions.drop(columns=['OLS_PI_low','OLS_PI_high'], inplace=True)
        diagnostic['ols_pi_coverage']=None
        diagnostic['ols_pi_mean_width']=None
    # Post-fit forensic audit: exact decimal arithmetic, not used to select or fit models.
    records=list(csv.DictReader(raw.decode('utf-8').splitlines()))
    formula_errors=[abs(sum(Decimal(v) for k,v in row.items() if k!=TARGET)/Decimal(200)-Decimal(row[TARGET])) for row in records]
    formula_audit={'formula':'FloodProbability = sum(all 20 input scores) / 200','exact_matches':sum(e==0 for e in formula_errors),'checked_rows':len(records),'max_decimal_error':str(max(formula_errors)),'timing':'Post-fit data audit; not used for model training or selection','interpretation':'All supplied rows obey a deterministic rule; this does not establish the original collection/generation process or real-world validity.'}
    report={'student_id':'7114056126','seed':SEED,'source':{k:v for k,v in source.items() if k!='metadata'},'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__},'initial_rows':initial_rows,'rows':len(df),'duplicates_removed':duplicates,'missing':missing,'train_n':len(Xtr),'test_n':len(Xte),'features':list(X.columns),'recommended_linear':winner,'best_overall_cv':overall,'models':results,'cv_candidates':cv_rows,'diagnostics':diagnostic,'exports':exports,'feature_summary':{c:{'min':float(Xtr[c].min()),'max':float(Xtr[c].max()),'mean':float(Xtr[c].mean()),'median':float(Xtr[c].median()),'std':float(Xtr[c].std()),'train_correlation':float(Xtr[c].corr(ytr))} for c in X},'preview':df.head(8).to_dict(orient='records')}
    report['formula_audit']=formula_audit
    (ROOT/'reports/results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (ROOT/'site/assets/results.json').write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    (ROOT/'reports/splits.json').write_text(json.dumps({'seed':SEED,'train_csv_rows':(df.index[train_idx]+2).tolist(),'test_csv_rows':(df.index[test_idx]+2).tolist(),'cv_validation_train_positions':[v.tolist() for _,v in cv]}),encoding='utf-8')
    predictions.to_csv(ROOT/'reports/test_predictions.csv',index=False)
    Xtr.describe().T.to_csv(ROOT/'reports/train_data_summary.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140,'axes.titleweight':'bold'})
    def save(name):
        plt.tight_layout(); plt.savefig(ROOT/f'site/assets/{name}.png',bbox_inches='tight'); plt.close()
    fig,ax=plt.subplots(figsize=(9,4.5)); names=[r['name'] for r in results]; vals=[r['test']['rmse'] for r in results]
    ax.barh(names,vals,color=['#96a5ae' if n!=winner else '#137f78' for n in names]); ax.set_xlabel('Held-out RMSE (lower is better)'); ax.set_title('Same 10,000-row test set'); save('comparison')
    pred=predictions[winner].to_numpy(); residual=yte.to_numpy()-pred
    fig,axes=plt.subplots(1,2,figsize=(10,4)); axes[0].hexbin(yte,pred,gridsize=40,cmap='YlGnBu',mincnt=1); axes[0].plot([.2,.85],[.2,.85],color='#dc8055',lw=1); axes[0].set(xlabel='Actual',ylabel='Predicted',title=winner)
    axes[1].scatter(pred[::10],residual[::10],s=5,alpha=.3,color='#137f78'); axes[1].axhline(0,color='#dc8055'); axes[1].set(xlabel='Predicted',ylabel='Actual minus predicted',title='Residuals (every 10th test row)'); save('predictions')
    fig,axes=plt.subplots(1,2,figsize=(10,4)); stats.probplot(ols.resid,dist='norm',plot=axes[0]); axes[0].set_title('Full OLS training residual Q-Q'); axes[1].hist(ols.resid,bins=50,color='#137f78'); axes[1].set_title('Full OLS training residual distribution'); save('diagnostics')
    fig,ax=plt.subplots(figsize=(8,4));
    for name,param in [('SelectKBest + OLS','select__k'),('RFE + OLS','select__n_features_to_select')]:
        rows=[r for r in cv_rows if r['name']==name]; ax.errorbar([r['params'][param] for r in rows],[r['rmse'] for r in rows],yerr=[r['sd'] for r in rows],marker='o',capsize=3,label=name)
    ax.set(xlabel='Number of selected input features',ylabel='5-fold CV RMSE',title='Selection is repeated inside every training fold'); ax.legend(); save('selection')
    fig,ax=plt.subplots(figsize=(10,8)); corr=Xtr.corr(); im=ax.imshow(corr,vmin=-1,vmax=1,cmap='BrBG'); ax.set_xticks(range(20),X.columns,rotation=90,fontsize=7); ax.set_yticks(range(20),X.columns,fontsize=7); fig.colorbar(im,ax=ax,shrink=.7); ax.set_title('Training features only / Pearson correlation'); save('correlation')
    fig,ax=plt.subplots(figsize=(9,6)); coef=np.asarray(exports['OLS']['coef']); order=np.argsort(coef); ax.barh(np.asarray(X.columns)[order],coef[order],color='#137f78'); ax.set(xlabel='Raw-scale OLS coefficient',title='Association holding other input scores fixed'); save('coefficients')
    print(json.dumps({'recommended':winner,'results':results,'diagnostics':diagnostic},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
