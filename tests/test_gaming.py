import polars as pl
import pytest
from bonus_ab_test.config import SimulationConfig
from bonus_ab_test.simulate import simulate_players
from bonus_ab_test.gaming import validate,mean_effect,holm,gaming_summary,experiment_readout

def fixture(): return simulate_players(SimulationConfig(n_players=1000))
def test_reconciliation_and_nonplayers():
 d=fixture();validate(d)
 assert d.filter(~pl.col('reached_bet'))['stakes_30d'].sum()==0
 s=gaming_summary(d)
 assert s['ggr_30d'].sum()==pytest.approx(d['stakes_30d'].sum()-d['wins_30d'].sum())
def test_duplicate_and_broken_finance_fail():
 d=fixture()
 with pytest.raises(ValueError):validate(pl.concat([d,d.head(1)]))
 with pytest.raises(ValueError):validate(d.with_columns((pl.col('ggr_30d')+1).alias('ggr_30d')))
def test_holm_known_values(): assert holm([.01,.04,.03])==pytest.approx([.03,.06,.06])
def test_effect_direction_and_zero_variance():
 r=mean_effect([0,1,2,3],[10,11,12,13]);assert r['low']>0
 assert mean_effect([1,1],[1,1])['p']==1

def test_primary_uses_all_assigned_and_cost():
 d=fixture();r=experiment_readout(d)
 a=d.filter(pl.col('group')=='control');b=d.filter(pl.col('group')=='treatment')
 assert r['effect']==pytest.approx(b['contribution_30d'].mean()-a['contribution_30d'].mean())
 assert r['net_roi']==pytest.approx(r['effect']*b.height/b['bonus_cost'].sum())
