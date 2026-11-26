"""The credit limit must cover concurrent calls, restarts and uncertain deliveries."""
import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pytest

from atlas.budget import CreditBudget, BudgetExceeded, cost_report, request


def test_fractional_guard_rounds_up_and_is_immutable_on_resume(tmp_path):
    b=CreditBudget(tmp_path,"0.000002",fractional=True)
    b.reserve("embeddings",3,0)
    b=CreditBudget(tmp_path,"0.000002")
    b.reserve("labels",2,0)
    with pytest.raises(BudgetExceeded):b.reserve("embeddings",1,0)
    report=cost_report(tmp_path)
    assert report["reserved_usd"]==.000002 and report["reservation_rates_usd_per_million"]["labels"]==[.5,1.]


def test_concurrent_reservations_cannot_cross_the_cap(tmp_path):
    a=CreditBudget(tmp_path,Decimal("0.001"))
    b=CreditBudget(tmp_path,Decimal("0.001"))
    def try_call(budget):
        try:return budget.reserve("embeddings",600,0)
        except BudgetExceeded:return None
    with ThreadPoolExecutor(max_workers=2) as workers: tickets=list(workers.map(try_call,[a,b]))
    assert sum(t is not None for t in tickets)==1
    with pytest.raises(BudgetExceeded):CreditBudget(tmp_path,Decimal("0.001")).reserve("embeddings",401,0)
    with pytest.raises(ValueError):CreditBudget(tmp_path,Decimal("0.01"))


def test_receipts_and_unsettled_attempt_are_reported_separately(tmp_path):
    b=CreditBudget(tmp_path,Decimal("1"))
    b.reserve("embeddings",1000,0)
    ticket=b.reserve("labels",10000,100)
    usage=dict(input_tokens=1000,output_tokens=80,input_tokens_details=dict(cached_tokens=200,cache_write_tokens=300,
               cache_write_tokens_details=dict(ttl_30m_tokens=200,ttl_12h_tokens=100)))
    (tmp_path/"api-usage.jsonl").write_text(json.dumps(dict(phase="labels",model="gpt-6-luna",reservation=ticket,usage=usage))+"\n")
    report=cost_report(tmp_path)
    assert report["estimated_usd"]==pytest.approx(.000142)
    assert report["unconfirmed_attempts"]==1 and report["unconfirmed_bound_usd"]==.001
    assert report["reserved_usd"]==.0213


def test_retry_cannot_transmit_without_another_reservation(tmp_path,monkeypatch):
    import httpx
    from openai import APIConnectionError
    monkeypatch.setattr("atlas.budget.time.sleep",lambda n:None)
    calls=[]
    def timeout():
        calls.append(True)
        raise APIConnectionError(request=httpx.Request("POST","https://api.openai.com/v1/embeddings"))
    budget=CreditBudget(tmp_path,Decimal("0.001"))
    with pytest.raises(BudgetExceeded):request(budget,"embeddings",600,0,timeout)
    assert calls==[True]
    with pytest.raises(BudgetExceeded):request(CreditBudget(tmp_path,"0.001"),"embeddings",600,0,timeout)
    assert calls==[True] and cost_report(tmp_path)["unconfirmed_attempts"]==1


def test_cli_forwards_a_lower_credit_limit(tmp_path,monkeypatch):
    import sys
    from atlas import cli,io
    args=[]
    monkeypatch.setattr(cli,"RESULTS",tmp_path/"results")
    monkeypatch.setattr(cli,"ROOT",tmp_path)
    monkeypatch.setattr(io,"CACHE",tmp_path/"cache")
    monkeypatch.setattr(cli,"start_log",lambda _:None)
    monkeypatch.setattr(cli,"refresh",lambda *a:args.extend(a))
    monkeypatch.setattr(sys,"argv",["atlas","refresh","--snapshot","test","--threshold","20","--max-api-usd","0.001"])
    cli.main()
    assert args[-2:]==[20,Decimal("0.001")]
