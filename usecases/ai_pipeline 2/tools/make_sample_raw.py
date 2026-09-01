"""Generate a sample raw transcript parquet so you can run the pipeline (Tier B).

Writes ``<date>.parquet`` in the exact shape the ``denoise`` step expects, with
realistic speaker-labelled contact-center transcripts. Run it from the pipeline's
venv (it uses polars, the same lib the pipeline uses).

    # 1) write the file locally
    python -m ai_pipeline.tools.make_sample_raw --date 2025-08-28 --out ./2025-08-28.parquet

    # 2) OR write straight into your Azure raw container (uses StorageService + .env)
    python -m ai_pipeline.tools.make_sample_raw --date 2025-08-28 --upload

Schema (columns denoise reads):
    full_text     str   required — the raw, messy transcript to be cleaned
    contact_id    str   required — unique call id
    EmployeeID    int   required — agent id (used by --agent filter)
    ProgramName   str   required — must match your *_PROGRAMS env mapping
    CoachID       int   optional — if absent, enriched from Azure SQL at run time
    CoachName     str   optional
    totalcalltime int   optional — seconds
    totalholdtime int   optional — seconds
"""
from __future__ import annotations

import argparse
import os

# ProgramName must match TELESALES_PROGRAMS in .env (default there is "VZW Telesales").
DEFAULT_PROGRAM = os.environ.get("SAMPLE_PROGRAM", "VZW Telesales")

# Twelve realistic, deliberately-messy telesales transcripts (denoise cleans these).
_TRANSCRIPTS = [
    "Agent: uh thank you for calling Verizon telesales this is Jordan how can i help. Customer: yeah hi um i wanted to see about upgrading my plan i keep going over on data. Agent: absolutely i can help with that, let me pull up your account, can you verify the last four. Customer: 4821. Agent: perfect. so you're on the 15 gig plan right now, the unlimited welcome is only ten dollars more and you'd never worry about overages. Customer: hmm ten more a month. Agent: right and honestly with the two overage charges last month you actually paid more than that. Customer: oh wow okay yeah lets do it.",
    "Agent: hi this is Jordan with Verizon how can i help today. Customer: my bill went up like thirty dollars and i dont know why im pretty upset. Agent: i completely understand let me take a look... okay i see a promotional credit expired last cycle. Customer: nobody told me that. Agent: i hear you, that's frustrating, let me see what current offers you qualify for so we can get that back down. Customer: okay please. Agent: alright i can add a loyalty credit of fifteen and move you to a newer plan that's actually cheaper. Customer: okay that helps a little.",
    "Agent: Verizon telesales Jordan speaking. Customer: hi i saw an ad for a free phone with trade in is that real. Agent: it is, so with an eligible trade and the unlimited plus plan you can get the new model at no cost over 36 months. Customer: whats the catch. Agent: no catch, it's applied as monthly bill credits, if you stay on the line i can check your device's trade value right now. Customer: yeah okay do that. Agent: your current phone qualifies for the full 800 credit. Customer: nice okay im interested.",
    "Agent: thanks for calling this is Jordan. Customer: i want to cancel my line im moving overseas. Agent: oh i'm sorry to hear you're leaving us, before we do that can i ask where you're moving, we do have international options. Customer: japan for two years. Agent: got it, we actually have a travel pass and a suspend option so you keep your number, would either of those work instead of cancelling. Customer: hmm i didnt know i could suspend. Agent: yes up to 24 months. Customer: okay actually that's perfect lets suspend it.",
    "Agent: hi Verizon telesales. Customer: yeah my daughter needs a line added to my account. Agent: happy to help set that up, are we also looking at a device for her. Customer: maybe something cheap. Agent: sure, we have a few budget models, and adding a line on your current plan is only twenty a month with autopay. Customer: okay and the phone. Agent: the entry model is free with a new line right now. Customer: oh perfect yeah lets add the line and the free phone.",
    "Agent: Jordan with Verizon how can i help. Customer: im calling because my service has been terrible dropped calls all week. Agent: i'm really sorry about that, that's not the experience we want, let me check the towers in your area... i do see maintenance happening near you that finished yesterday. Customer: so it should be better now. Agent: it should, and if you keep seeing issues we can send a network extender at no charge. Customer: okay lets do the extender just in case. Agent: done, and again i apologize for the trouble.",
    "Agent: thank you for calling telesales this is Jordan. Customer: i just want to pay my bill. Agent: no problem i can take that payment, and while i have you, i noticed you're a great candidate for autopay which saves ten a month. Customer: eh i dont like autopay. Agent: totally understand, no pressure at all, i'll just process the one time payment then. Customer: yeah thanks. Agent: all set, anything else. Customer: nope thats it.",
    "Agent: hi this is Jordan. Customer: whats your best deal for a new customer im switching from another carrier. Agent: welcome, so we can cover your switching costs up to 650 per line and give you unlimited plus, how many lines. Customer: three. Agent: excellent, three lines on unlimited plus comes to a great per line rate and each eligible trade can earn up to 800 in credits. Customer: okay that sounds way better than what im paying. Agent: shall i get the port started. Customer: yes lets do it.",
    "Agent: Verizon telesales Jordan speaking how can i help. Customer: im so frustrated i've called three times about the same issue. Agent: i am so sorry you've had to call back, that's on us, let me make this the last time, walk me through what's happening. Customer: my international texts arent going through. Agent: okay let me check your plan features... i see the messaging add on didn't provision correctly, i'm fixing that now and adding a credit for the trouble. Customer: finally thank you.",
    "Agent: hi Jordan here. Customer: i think im paying too much can you review my account. Agent: of course, let's do a quick review... you're on an older plan, i can move you to a current one with more data for five dollars less. Customer: really less. Agent: yes and you'd get a streaming perk included. Customer: okay yeah switch me. Agent: done, you'll see the savings next cycle.",
    "Agent: thank you for calling this is Jordan. Customer: my phone got stolen i need help. Agent: oh no i'm sorry that happened, first let's protect your account, i'll suspend the line so no one can use it. Customer: okay good. Agent: now, do you have insurance on the device. Customer: i think so. Agent: you do, so we can file a claim and get a replacement out, and i'll help you set a temporary forwarding to another number. Customer: thank you that's a relief.",
    "Agent: Verizon telesales Jordan how can i help. Customer: i want the new watch do you have those. Agent: we do, and the watch is fifty percent off when you add it to your plan on the number share feature. Customer: how much is number share. Agent: it's ten a month and the watch uses your existing plan, no separate data needed. Customer: okay that's reasonable add the watch. Agent: great choice.",
]

_NAMES = [
    ("Jordan Lee", 9040400), ("Priya Nair", 9040401), ("Marcus Reyes", 9040402),
    ("Ava Thompson", 9040403), ("Diego Alvarez", 9040404),
]


def build_rows(program: str) -> list[dict]:
    rows = []
    for i, text in enumerate(_TRANSCRIPTS):
        emp_name, emp_id = _NAMES[i % len(_NAMES)]
        rows.append({
            "full_text": text,
            "contact_id": f"C{1000 + i}",
            "EmployeeID": emp_id,
            "EmployeeName": emp_name,
            "ProgramName": program,
            "CoachID": 3000510 + (i % 2),
            "CoachName": ["Sam Rivera", "Dana Cole"][i % 2],
            "totalcalltime": 180 + (i * 17) % 600,
            "totalholdtime": (i * 11) % 90,
        })
    return rows


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate a sample raw transcript parquet")
    p.add_argument("--date", required=True, help="YYYY-MM-DD (also the parquet filename)")
    p.add_argument("--program", default=DEFAULT_PROGRAM, help=f"ProgramName value (default: {DEFAULT_PROGRAM})")
    p.add_argument("--out", default=None, help="local output path (default ./<date>.parquet)")
    p.add_argument("--upload", action="store_true", help="also upload into the raw container via StorageService")
    args = p.parse_args(argv)

    import polars as pl

    rows = build_rows(args.program)
    df = pl.DataFrame(rows)
    out = args.out or f"./{args.date}.parquet"
    df.write_parquet(out)
    print(f"Wrote {out} | {len(df)} rows | program='{args.program}'")

    if args.upload:
        from ai_pipeline.programs_config.base import StorageConfig
        from ai_pipeline.services.storage import StorageService

        cfg = StorageConfig()
        storage = StorageService(cfg)
        storage.write_parquet(df, cfg.raw_container, f"{args.date}.parquet")
        print(f"Uploaded to container '{cfg.raw_container}' as {args.date}.parquet")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
