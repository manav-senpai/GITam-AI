# Gitam AI
this was built during a hackathon… and yeah… kinda went all in with ai agents and stuff…

basically… this thing connects to any github repo… and then tries to figure out that what part of code is vulnerable or can cause the problems in future.. or is broken

like not in a dumb way… it actually checks commits… bugs… code changes… patterns…
and then predicts future failures… like next 30…60…90 days…

and then… the funniest part… it writes a CEO report… like proper business language…
so non tech people can understand what’s about to go wrong…

yeah.. the below part is written by ai >> ; 😐
---

## what it actually does…

* scans github repos (no login needed… public ones work)
* tracks commits… bugs… contributors… all that messy history
* tries to find “hotspots” where code is getting unstable
* gives health score (0-100 type thing… not super perfect but works)
* predicts future issues (based on patterns… not magic)
* generates report like “this will cost money if ignored” 💀
* can even send that report on email (yeah… that part was fun)

also there’s a chatbot… coz why not… everything has one now…

---

## agents… yeah there are 7 of them…

i didn’t wanna make just one model doing everything… so split into roles…

1. data collector → pulls stuff from github
2. code analyzer → checks code changes + churn
3. bug analyzer → looks at issues + patterns
4. health scorer → gives score (kinda judgemental tbh…)
5. predictor → future risk (this one is scary accurate sometimes…)
6. report generator → turns tech mess into business talk
7. email sender → sends it like a boss

---

## tech stack (nothing crazy but works)

* frontend → react + vite
* backend → fastapi
* ai → groq (mostly)… ollama if local
* api → github
* email → smtp (gmail)

---

## how to run (if it breaks… not my fault… just kidding… kinda…)

clone it:

```bash
git clone https://github.com/YOUR_USERNAME/gitam-ai.git
cd gitam-ai
```

backend setup:

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# put your api key… dont forget this or it’ll cry
```

frontend:

```bash
cd frontend
npm install
```

run:

```bash
# backend
python main.py

# frontend
npm run dev
```

open browser → localhost:5173

paste any repo link… click analyze… and wait…

---

## why i made this…

honestly… hackathon pressure + curiosity…

like everyone keeps saying “ai this ai that”…
so i wanted to actually build something that feels useful…

and also something that looks cool when demoing 💀

---

## is it perfect?

nope…

some predictions are off…
ui could be better…
code could be cleaner…

but it works… and that’s enough for now…

---

## final note…

if you’re reading this…
just know this wasn’t written by some clean documentation bot…

this is me… trying… breaking things… fixing them…
and somehow ending up with this…

…yeah that’s it
