"""Durable cost authorization before each physical OpenAI request and receipt-based estimates.

Rates verified 2026-11-26 at https://developers.openai.com/api/docs/pricing .
The ledger uses integer millionths of a dollar. Reservations are never refunded,
so a timeout, retry or crash cannot erase potential spend.
"""
import json
import os
import time
from decimal import Decimal
from filelock import FileLock
from openai import APIConnectionError, APIStatusError
from .io import now, save_json

MILLION=1_000_000
JOURNAL="budget-reservations.jsonl"
GUARD_RATES={"embeddings":(1,0),"labels":(2,3)}  # USD per million input/output tokens.
RATES={"embedding":.13,"input":.10,"cached":.01,"write_30m":.125,"write_12h":.25,"output":.50}


class BudgetExceeded(RuntimeError):
    """Raised before transmission when the next maximum charge cannot be reserved."""


class CreditBudget:
    def __init__(self,folder,dollars):
        self.journal=folder/JOURNAL
        amount=Decimal(str(dollars))*MILLION
        if not amount.is_finite() or amount!=amount.to_integral_value() or amount<0:
            raise ValueError("Budget must be nonnegative and expressed to at most six decimal places")
        self.cap=int(amount)
        work=folder/"work";work.mkdir(parents=True,exist_ok=True)
        self.lock=FileLock(str(work/"credits.lock"))
        with self.lock:
            if self.journal.exists():
                with self.journal.open("rb") as f:header=json.loads(f.readline())
                if header["cap_micro_usd"]!=self.cap:raise ValueError("A named snapshot has an immutable credit limit")
            else:
                if (folder/"api-usage.jsonl").exists():
                    raise ValueError("Cannot initialize an empty budget after hosted requests already occurred")
                with self.journal.open("xb") as f:
                    self._append(f,dict(time=now(),id=0,cap_micro_usd=self.cap,total_micro_usd=0))

    @staticmethod
    def _append(stream,record):
        stream.write((json.dumps(record,separators=(",",":"))+"\n").encode())
        stream.flush()
        os.fsync(stream.fileno())

    def reserve(self,phase,input_bound,output_bound):
        """A process-shared lock and fsync commit the charge before the network call."""
        ir,orr=GUARD_RATES[phase]
        if input_bound<0 or output_bound<0 or phase=="embeddings" and output_bound:
            raise ValueError("Invalid token reservation")
        charge=ir*input_bound+orr*output_bound
        with self.lock,self.journal.open("r+b") as f:
            end=f.seek(0,os.SEEK_END);f.seek(max(0,end-2048))
            tail=f.read()
            if not tail.endswith(b"\n"):raise ValueError("Incomplete credit journal; refusing further spend")
            last=json.loads(tail.splitlines()[-1])
            total=last["total_micro_usd"]+charge
            if total>self.cap:
                raise BudgetExceeded(f"Next {phase} request would exceed the USD {self.cap/MILLION:.2f} ceiling")
            ticket=last["id"]+1
            self._append(f,dict(id=ticket,time=now(),phase=phase,input_bound=input_bound,output_bound=output_bound,
                                reserved_micro_usd=charge,total_micro_usd=total))
        return ticket


def request(budget,phase,inputs,outputs,send):
    """The capped client disables SDK retries. Each explicit transport retry gets a new ticket."""
    if budget is None:return send(),None
    for attempt in range(3):
        ticket=budget.reserve(phase,inputs,outputs)
        try:return send(),ticket
        except (APIConnectionError,APIStatusError) as error:
            status=getattr(error,"status_code",None)
            if attempt==2 or status is not None and status<500 and status not in (408,409,429):raise
            time.sleep(2**attempt)


def cost_report(folder):
    """Price confirmed token categories and retain the whole reservation for missing receipts."""
    head,*entries=map(json.loads,(folder/JOURNAL).read_bytes().splitlines())
    receipts=folder/"api-usage.jsonl"
    records=list(map(json.loads,receipts.read_bytes().splitlines())) if receipts.exists() else []
    tickets={e["id"]:e for e in entries}
    confirmed=set();costs={"embeddings":0.0,"labels":0.0}
    for r in records:
        ticket=r["reservation"];phase=r["phase"];u=r["usage"];entry=tickets[ticket]
        if ticket in confirmed or entry["phase"]!=phase:raise ValueError("Invalid credit receipt")
        confirmed.add(ticket)
        if phase=="embeddings":
            used=u.get("prompt_tokens",u["total_tokens"]);out=0
            if r["model"]!="text-embedding-3-large":raise ValueError("Unknown embedding price")
            cost=used*RATES["embedding"]
        else:
            if r["model"]!="gpt-6-luna":raise ValueError("Unknown label price")
            used=u["input_tokens"];out=u["output_tokens"];d=u.get("input_tokens_details") or {}
            cached=d.get("cached_tokens",0) or 0;writes=d.get("cache_write_tokens",0) or 0
            short=(d.get("cache_write_tokens_details") or {}).get("ttl_30m_tokens",0) or 0
            if short>writes or cached+writes>used:raise ValueError("Unexpected cache billing breakdown")
            # Unknown write TTLs are charged at the more expensive 12-hour rate.
            cost=((used-cached-writes)*RATES["input"]+cached*RATES["cached"]+short*RATES["write_30m"]+
                  (writes-short)*RATES["write_12h"]+out*RATES["output"])
        if used>entry["input_bound"] or out>entry["output_bound"]:raise ValueError("Reported tokens exceed their reservation")
        costs[phase]+=cost/MILLION
    reserved=sum(e["reserved_micro_usd"] for e in entries)
    if reserved!=(entries[-1] if entries else head)["total_micro_usd"] or reserved>head["cap_micro_usd"]:
        raise ValueError("Credit journal exceeds the limit or its running sum is inconsistent")
    unknown=sum(e["reserved_micro_usd"] for e in entries if e["id"] not in confirmed)
    report=dict(cap_usd=head["cap_micro_usd"]/MILLION,estimated_usd=round(sum(costs.values()),9),
                estimated_by_phase_usd={k:round(v,9) for k,v in costs.items()},reserved_usd=reserved/MILLION,
                attempted_requests=len(entries),confirmed_receipts=len(confirmed),unconfirmed_attempts=len(entries)-len(confirmed),
                unconfirmed_bound_usd=unknown/MILLION,rate_card_usd_per_million=RATES,
                reservation_rates_usd_per_million=GUARD_RATES,pricing_source="https://developers.openai.com/api/docs/pricing",
                pricing_date="2026-11-26",feed_access="anonymous metadata",currency="USD")
    save_json(folder/"budget.json",report)
    return report
