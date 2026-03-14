# 1️⃣ Core engine

## Cycle Position
odhad kde se nacházíme v bullrunu (0–100%)

Cycle Position: 34%
Phase: Early Bull

## Market Phase Detection
Early Bull
Mid Bull
Late Bull

## Indicator Model
- Pi Cycle
- Rainbow
- MVRV approx
- Puell approx

## Top Probability
kombinace všech indikátorů

---

# 2️⃣ Data & History

## Logging
history.json

date
btc_price
top_probability
cycle_phase

## Historical backtest
- 2013 cycle
- 2017 cycle
- 2021 cycle

## Indicator vs price
porovnání indikátorů s BTC cenou

---

# 3️⃣ Telegram bot

## Telegram bot
automatické publikování reportu

## Rozdělení zpráv bota

### BTC Cycle Radar
Top Probability
Indicator breakdown

### Market Phase
Early / Mid / Late Bull

### Altcoin Season Index

### DCA návrhy

Navrh DCA prodeje (intenzita)
Navrh DCA nákupu (intenzita)

## Telegram bot odpovědi

/btc
/cycle
/altcoins
/heat

---

# 4️⃣ Message formatting

Pěkné formátování zpráv

sections
emoji
short explanations

📊 BTC Cycle Radar

Top Probability: 18%

Cycle Phase
Mid Bull

Indicators
Pi Cycle: Far
Rainbow: Green
MVRV: Healthy
Puell: Healthy

---

# 5️⃣ Chart export

graf indikátorů

- Pi Cycle
- Rainbow
- MVRV approx
- Puell approx

output:
*chart.png*

# 6️⃣ Subscription model ($1)

## Free vs Premium report

Free
Top Probability
Cycle Phase

Premium
Indicator breakdown
DCA strategy
Market heat score

## Payment options

Stripe
Telegram payments

# 7️⃣ Web dashboard

btc-cycle-radar.com

Top Probability
Cycle Phase
Indicators
History

# 8️⃣ Docker container

docker run btc-cycle-radar

# 9️⃣ Project name

BTC Cycle Radar
Bitcoin Cycle Monitor
Bitcoin Top Probability

# 📊 PRIORITY
1️⃣
👉 rozsekat btc_top_watcher.py na modulární strukturu projektu
Cycle Position
Market Phase Detection
Top Probability model
2️⃣
history.json
logging
3️⃣
Telegram bot
report formatting
4️⃣
chart export
5️⃣
subscription model
6️⃣
web dashboard


# Next day 15.3.2025
Pokračujeme v projektu BTC Top Watcher.

Repo:
https://github.com/zanigmj-code/Btc-top-watcher

Projekt:
Python aplikace, která analyzuje BTC cyklus a generuje grafy.

Používáme 4 hlavní indikátory:

1) Pi Cycle Score
2) Rainbow Heat
3) MVRV approximation
4) Puell approximation

Z nich počítáme:

Market Heat
Top Probability
Late-Cycle Alerts

Grafy které generujeme:

1) BTC Historical Cycle Model
2) BTC Action Radar (90 days)

Aktuální stav projektu:

- historický graf funguje
- zobrazuje posledních 6 let
- BTC line je zelená/červená
- Market Heat je černý
- Pi Cycle je modrý
- Late-Cycle Alerts jsou růžové tečky (threshold 50)

Testovali jsme všechny kombinace indikátorů (15 kombinací)
a zjistili jsme, že většina funguje podobně.

Závěr:
model zatím neindikuje cycle top.

Další krok:

1) přidat liquidity faktor (Global M2 / liquidity index)
2) upravit graf tak aby vysvětlení a poslední cena byly pod grafem
3) zlepšit interpretaci signálů (buy / reduce / exit)

Prosím pokračuj odtud.

NEXT DEVELOPMENT

1) move price status under charts
2) improve chart readability for telegram
3) test indicator combinations performance
4) add liquidity indicator (global M2)
5) experiment with liquidity-adjusted cycle model
6) improve action radar buy/sell logic
7) add explanation block under charts

Current BTC price ≈ 70k
cycle phase: early bull
top probability low
late cycle alerts threshold = 50

mozna zakomponovat btc liqidity Cycle Model



přidat a upravit strukturu

docs/

model.md
indikatory.md
grafy.md
roadmap.md

| soubor          | význam                         |
| --------------- | ------------------------------ |
| `models.py`     | datové struktury               |
| `indicators.py` | výpočty indikátorů             |
| `docs/model.md` | vysvětlení ekonomického modelu |

docs model.md vysvětlení

BTC TOP WATCHER MODEL

Inputs:

1) Pi Cycle
2) Rainbow Heat
3) MVRV approximation
4) Puell approximation

Output:

Market Heat
Top Probability
Cycle Phase
Trade Action

Score interpretation

0–25 undervalued
25–40 early bull
40–50 warm
50–65 late cycle
65–80 danger
80+ extreme top risk

Celková změna jmena aplikace..