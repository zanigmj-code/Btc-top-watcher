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