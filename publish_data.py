#!/usr/bin/env python3
"""
Publish each session's sales as a data file the web app can fetch.

    SUPABASE_PAT=sbp_xxx python3 publish_data.py 2026-07-28 2026-08-31

Writes one file per session into deploy/UPLOAD THESE/data/ :

    rwc-2026-08-11.json
    sc-2026-08-16-AM.json
    sc-2026-08-16-PM.json

plus index.json listing what is available.

Why files rather than the app talking to the database directly:

  * No credential ever reaches the browser. A published anon key would need RLS
    on all 14 recon tables first, and that work is not done.
  * It works on GitHub Pages, which serves static files and nothing else.
  * The production database is only ever read here, by this script, from a
    machine you control.

The cost is that the data is as fresh as the last run. Run it after each
session, or on a schedule, and push the files.
"""
import os, sys, json, urllib.request, datetime, re
from collections import defaultdict

PROD = "faoqpyjhwvwgwvmgqxjr"
API  = "https://api.supabase.com/v1/projects/{ref}/database/query"
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

PAT = os.environ.get("SUPABASE_PAT")
if not PAT:
    sys.exit("Set SUPABASE_PAT")
HDRS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
        "Authorization": "Bearer " + PAT}


def q(sql):
    req = urllib.request.Request(API.format(ref=PROD),
                                 data=json.dumps({"query": sql}).encode(),
                                 headers=HDRS, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def esc(v):
    return "'" + str(v).replace("'", "''") + "'"


# NOTE: product names differ by hall — 'Buy In' at Santa Clara, 'Buy-In' at
# Redwood City. Every buy-in match uses ~* 'buy[- ]?in' so both are caught.
def categorise(name):
    n = (name or "").lower()
    if "buy-in" in n or "buy in" in n:                        return "Buy-In"
    if "dauber" in n or "merch" in n:                         return "Merch"
    if any(k in n for k in ("hotball", "hot ball", "flash", "all number")):
        return "Flash"
    if any(k in n for k in ("double action", "rwb", "red white",
                            "early bird", "bonus paper")):    return "Paper"
    return "Strips"


def parse_items(raw):
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except Exception: return []
    return raw or []


def sessions_between(a, b):
    return q(f"""
      select s.id, s.session_date::text d, s.session_time::text t,
             case when h.name ilike '%redwood%' then 'rwc' else 'sc' end hall
      from sessions s join halls h on h.id = s.hall_id
      where s.session_date between {esc(a)} and {esc(b)}
      order by s.session_date, s.session_time;""")


def build(sess):
    sid = sess["id"]
    # ---- sales, online (paid only) and POS, itemised
    rows = q(f"""
      select 'online' src, null station, t.line_items
        from transactions t
       where t.session_id = {esc(sid)} and t.source='website'
         and t.voided_at is null and coalesce(t.payment_status,'paid')='paid'
      union all
      select 'pos', ps.user_email, t.line_items
        from transactions t join pos_shifts ps on ps.id = t.pos_shift_id
       where ps.session_id = {esc(sid)} and t.source='pos' and t.voided_at is null;""")
    agg = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        st = r["station"] or ""
        st = st.split("+")[1].split("@")[0] if "+" in st else (st.split("@")[0] if st else None)
        for it in parse_items(r["line_items"]):
            nm  = it.get("name") or "?"
            qty = float(it.get("quantity") or 0)
            tot = it.get("total")
            val = float(tot) if tot is not None else float(it.get("price") or 0) * qty
            cell = agg[(r["src"], st, nm)]
            cell[0] += qty; cell[1] += val
    sales = [{"channel": ch, "station_code": st, "item_name": nm,
              "category": categorise(nm), "qty": f"{v[0]:.2f}", "value": f"{v[1]:.2f}"}
             for (ch, st, nm), v in sorted(agg.items(), key=lambda x: -x[1][1])]

    # ---- per station: cash and card as the POS recorded them
    #
    # cash_collected / card_collected ARE the split, and they work: Redwood City
    # 8-11 records rwc01 $4,795 card, rwc02 $4,385, rwc03 $18. Sixteen of the
    # eighteen August sessions carry a card figure.
    #
    # Two do not — SC 8-02 and SC 8-14 both show $0 card against a drawer far
    # below what was rung, which is the POS failing to capture the split rather
    # than a genuinely all-cash night. Where that happens the implied figure
    # (rung, less what stayed in the drawer) is offered and flagged, so the
    # operator keys the real number off the terminal report.
    cash = []
    for r in q(f"""
      select ps.id, ps.user_email, ps.opening_cash, ps.closing_cash,
             coalesce(sum(t.amount),0)::numeric(12,2) rung,
             coalesce(sum(t.cash_collected),0)::numeric(12,2) cash_col,
             coalesce(sum(t.card_collected),0)::numeric(12,2) card_col
        from pos_shifts ps
        left join transactions t on t.pos_shift_id = ps.id and t.voided_at is null
       where ps.session_id = {esc(sid)}
       group by ps.id, ps.user_email, ps.opening_cash, ps.closing_cash;"""):
        st = (r["user_email"].split("+")[1].split("@")[0]
              if "+" in (r["user_email"] or "") else "pos")
        closing = float(r["closing_cash"] or 0); opening = float(r["opening_cash"] or 0)
        rung    = float(r["rung"] or 0);        card    = float(r["card_col"] or 0)
        implied = round(rung - (closing - opening), 2)
        recorded = card > 0
        cash.append({"station": st, "cash_in": closing, "start_cash": opening,
                     "rung": rung,
                     "credit_in": card if recorded else (implied if implied > 0 else 0.0),
                     "credit_recorded": recorded,
                     "credit_implied": round(implied, 2)})

    # ---- attendance and people
    #
    # PEOPLE is the seat count. Each online order carries one or more seats in
    # selected_seat, comma separated ("108, 109, 99"), and it is the seats that
    # count — orders average about 1.25 of them.
    #
    # Whether a session has seats is read from the data, not guessed from the
    # weekday. Only the Saturday and Sunday SECOND sessions come through with
    # none, and those fall back to the order count.
    c = q(f"""
      with w as (select selected_seat, line_items from transactions
                  where session_id={esc(sid)} and source='website'
                    and voided_at is null and coalesce(payment_status,'paid')='paid')
      select (select count(*) from w) orders,
             (select count(*) from w where line_items::text ~* 'buy[- ]?in') attendance,
             (select count(*) from w where coalesce(selected_seat,'')<>'') orders_with_seats,
             (select coalesce(sum(array_length(string_to_array(
                 regexp_replace(selected_seat,'\\s','','g'),','),1)),0)
                from w where coalesce(selected_seat,'')<>'') seats;""")[0]
    seats = int(c["seats"] or 0)
    seatless = seats == 0
    pos_buyins = q(f"""
      select coalesce(sum((it->>'quantity')::numeric),0) n
        from transactions t join pos_shifts ps on ps.id=t.pos_shift_id
        cross join lateral jsonb_array_elements(
          case when jsonb_typeof(t.line_items)='string'
               then (t.line_items #>> '{{}}')::jsonb else t.line_items end) it
       where ps.session_id={esc(sid)} and t.source='pos' and t.voided_at is null
         and it->>'name' ~* 'buy[- ]?in';""")[0]["n"]
    counts = {"online_orders": int(c["orders"]),
              "online_attendance": int(c["attendance"]),
              "online_people": int(c["orders"]) if seatless else seats,
              "online_seats": seats,
              "orders_with_seats": int(c["orders_with_seats"] or 0),
              "online_seatless": seatless,
              "pos_attendance": float(pos_buyins or 0),
              "pos_people": float(pos_buyins or 0)}

    # ---- flash boxes scheduled for the pre-sale
    flash = [{"game_name": r["name"], "tickets": str(r["tickets_per_box"] or 0),
              "presold_tickets": str(r["tickets_sold"] or 0)}
             for r in q(f"""
      select fg.name, fg.tickets_per_box, sf.tickets_sold
        from session_flashgames sf join flash_games fg on fg.id = sf.flash_game_id
       where sf.session_id = {esc(sid)} order by sf.display_order;""")]

    # ---- orders that never completed payment: excluded, but surfaced
    ab = q(f"""select count(*) n, coalesce(sum(amount),0)::numeric(12,2) amt
                 from transactions where session_id={esc(sid)} and source='website'
                  and voided_at is null and coalesce(payment_status,'paid')<>'paid';""")[0]

    return {"session": {"id": sid, "hall_id": sess["hall"],
                        "session_date": sess["d"], "session_time": sess["t"][:5],
                        "weekday": datetime.date.fromisoformat(sess["d"]).strftime("%A"),
                        "ecom_session_id": sid},
            "sales": sales, "cash": cash, "flash": flash, "counts": counts,
            "abandoned": {"orders": int(ab["n"]), "value": float(ab["amt"] or 0)},
            "published_at": datetime.datetime.utcnow().isoformat() + "Z"}


def key_for(sess):
    """Matches what the app asks for: hall-date, plus AM/PM where a day runs twice."""
    part = "-AM" if sess["t"][:5] < "16:00" else "-PM"
    twice = sess["hall"] == "sc" and datetime.date.fromisoformat(
        sess["d"]).strftime("%A") in ("Saturday", "Sunday")
    return f"{sess['hall']}-{sess['d']}{part if twice else ''}"


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else str(datetime.date.today() - datetime.timedelta(days=30))
    b = sys.argv[2] if len(sys.argv) > 2 else str(datetime.date.today() + datetime.timedelta(days=1))
    os.makedirs(OUT, exist_ok=True)
    made = []
    for s in sessions_between(a, b):
        d = build(s)
        if not d["sales"]:
            continue
        k = key_for(s)
        with open(os.path.join(OUT, k + ".json"), "w") as f:
            json.dump(d, f, separators=(",", ":"))
        made.append({"key": k, "hall": s["hall"], "date": s["d"], "time": s["t"][:5],
                     "sales_lines": len(d["sales"]),
                     "value": round(sum(float(x["value"]) for x in d["sales"]), 2)})
        print(f"  {k:24} {len(d['sales']):>4} lines  ${made[-1]['value']:>12,.0f}")
    with open(os.path.join(OUT, "index.json"), "w") as f:
        json.dump({"published_at": datetime.datetime.utcnow().isoformat() + "Z",
                   "sessions": made}, f, indent=1)
    print(f"\n{len(made)} session files written to {OUT}")
    print("Commit the data folder and push; the app will fetch from it.")


if __name__ == "__main__":
    main()
