#!/usr/bin/env python3
"""Rank ride options for Sun Devil Rides. Standard library only.

Rank trips:
  python3 scripts/rank.py --people 2 --max-walk 15 --options '[{"name":"Light rail","cost":2,"minutes":35,"walk":8,"per_person":true,"link":"https://..."}]'

U-Pass check:
  python3 scripts/rank.py upass --rides-per-week 6 --fare 2 [--date 2026-10-24]
"""
import argparse
import json
import sys
from datetime import date


def rank(args):
    try:
        options = json.loads(args.options)
    except json.JSONDecodeError as e:
        sys.exit(f"Bad --options JSON: {e}")
    if not isinstance(options, list) or not options:
        sys.exit("--options must be a non-empty JSON list")
    people = max(1, args.people)
    kept, dropped = [], []
    for o in options:
        name = str(o.get("name", "Option"))
        try:
            cost = float(o.get("cost", 0))
            minutes = float(o.get("minutes", 0))
            walk = float(o.get("walk", 0))
        except (TypeError, ValueError):
            dropped.append(f"{name} (bad numbers)")
            continue
        if walk > args.max_walk:
            dropped.append(f"{name} (walk {walk:.0f} min > {args.max_walk} min)")
            continue
        each = cost if o.get("per_person") else cost / people
        kept.append({**o, "name": name, "each": each, "minutes": minutes, "walk": walk})
    kept.sort(key=lambda o: (round(o["each"], 2), o["minutes"]))
    if not kept:
        print("No options within the walk limit.")
    for i, o in enumerate(kept[: args.top], 1):
        price = "free" if o["each"] == 0 else f"${o['each']:.2f} each"
        line = f"{i}. {o['name']}: {price}, {o['minutes']:.0f} min ({o['walk']:.0f} min walking)"
        if o.get("estimate"):
            line += ", estimate"
        print(line)
        if o.get("link"):
            print(f"   {o['link']}")
    if dropped:
        print("Dropped: " + "; ".join(dropped))


def upass(args):
    today = date.fromisoformat(args.date) if args.date else date.today()
    y = today.year
    if date(y, 5, 16) <= today <= date(y, 8, 15):
        price, end, label = 75.0, date(y, 8, 16), "summer pass"
    else:
        end_year = y + 1 if today.month >= 8 else y
        end = date(end_year, 5, 15)
        after_jan1 = today.month < 8
        price = 75.0 if after_jan1 else 150.0
        label = "academic-year pass" + (" (after Jan 1 price)" if after_jan1 else "")
    weeks = max(0.0, (end - today).days / 7)
    pay_as_you_go = args.rides_per_week * args.fare * weeks
    print(f"{label}: ${price:.0f}, valid until {end.isoformat()} (~{weeks:.0f} weeks left)")
    print(f"Paying per ride: {args.rides_per_week:g} rides/week x ${args.fare:.2f} x {weeks:.0f} weeks = ${pay_as_you_go:.0f}")
    if pay_as_you_go > price:
        print(f"Verdict: the U-Pass saves about ${pay_as_you_go - price:.0f}.")
    else:
        print(f"Verdict: paying per ride is cheaper by about ${price - pay_as_you_go:.0f}.")
    breakeven = price / (args.fare * weeks) if weeks and args.fare else 0
    if breakeven:
        print(f"Break-even: about {breakeven:.1f} rides per week.")
    if label.startswith("academic") and today.month >= 8:
        print(f"Refund: return the pass before Dec 31, {y} for $75 back.")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "upass":
        p = argparse.ArgumentParser(prog="rank.py upass")
        p.add_argument("--rides-per-week", type=float, required=True)
        p.add_argument("--fare", type=float, required=True, help="today's single-ride fare in dollars")
        p.add_argument("--date", help="YYYY-MM-DD, defaults to today")
        upass(p.parse_args(sys.argv[2:]))
        return
    p = argparse.ArgumentParser(prog="rank.py")
    p.add_argument("--options", required=True, help="JSON list of options")
    p.add_argument("--people", type=int, default=1)
    p.add_argument("--max-walk", type=float, default=15)
    p.add_argument("--top", type=int, default=3)
    rank(p.parse_args())


if __name__ == "__main__":
    main()
