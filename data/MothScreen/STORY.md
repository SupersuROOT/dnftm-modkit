# Moth Screen: story bible (v2.5)

The player watches the desktop and microphone of m0th (Elias Krumm, 19), a beginner hacker paid by "Crow" (Dorian Pell)
to find Nora Vance. From day 4 he discovers the relay and starts hunting the observer. 7 days.

## Daily window
Elias sleeps in the morning and works night shifts at a gas station, so every day plays between **14:00 and about 22:00**.
The only exception is the door visit at 01:00 on day 7. Scenes are about an hour long, and the schedule fits even if
every scene runs 30% longer (`validate_cage.py` report).

| Day | Scenes (start hour) |
|---|---|
| 1 | boot 14, tutorial 15, job 16.5, profile 17.75, pizza 19, night 20.5 |
| 2 | vpn 14, phish 15, call 16, photo 17.25, crow 19.5 (+night) |
| 3 | result 14, mom 16, number 18, paid 19.5 (+night: **breakIn**) |
| 4 | news 14, dorian 16.25, relay 17.5, trace 19 (+whisper) |
| 5 | poc 14 (chat opens), chat 17 (chat closes), crow 19, video 20.25 (+night) |
| 6 | geo 14, call 15, gift 16.5, crowCheck 18.5, leave 21 (**finalNight**, knock at 01:00) |
| 7 | end 14 |

## Phases
| Phase | Starts when | Variable |
|---|---|---|
| A. hunting | day 1 | - |
| B. address sold | d3_paid ~19:30 | `addressSold` |
| C. after the break-in / break-in prevented | end of day 3 | `breakIn` (unless `dorianStopped`) |
| D. he knows he is watched | d4_relay | (`guiltSeen` d4_news) |
| E. chat window | d5_poc 14:00 to d5_chat 17:00 | `mothChatOn` |
| F. last night | d6_leave 21:00 | `finalNight`, `mothLeft` (not a member) |

## Player actions × phases
| Action | A | B | C | F |
|---|---|---|---|---|
| Call Nora | warn → `noraWarned` (with Nora / Dorian / Kestrel / m0th / Crow / **noraHiding** / **crowEx**); wrong deductions get suspicion, no warning | same | too late: "it was Dorian? call 555-0110"; warned: "I'm safe" | same as C |
| Police: m0th's address | "call back with something concrete" | raid → `copsMoth` | raid ("matches Kestrel Lane") | no raid: nobody home / car in the morning |
| Police: Dorian | arrest → `copsDorian`, `dorianStopped` (break-in prevented) | same | arrest (after the fact) | already in custody if reported |
| Police: deductions | crowEx → "need his name" (or "in custody"); crowDebt → civil matter; crowCop → badge number; mothComing → lock your door | | | |
| Chat with m0th | - | - | only in phase E; each answer sets exactly one of chatClub / chatMirror / chatHelp / chatLie / chatThreat; deductions route to these | closed |
| Door (01:00 day 7) | - | - | - | open the door and answer (2 choices, then 2 more); not answering the knock = he leaves |
| MART parcels | reactions | | | nobody home after `mothLeft` |
| Call m0th's number | annoyed / "it's you" after guilt | | | only the cat after `mothLeft` |

## Deductions (notebook "?", ModLoader 0.5.6)
| Circle | Question | Shown when | Options (right one in bold) | Payoff |
|---|---|---|---|---|
| Crow (4) | Why does Crow want her? | 3 words + restraining order | debt collector / **her ex, banned from her** / undercover cop | right answer stays visible and also writes **Dorian Pell** (keyword `addWords`) (earlier than day 4 → the break-in can be prevented); Nora, police and chat answers |
| Nora (1) | What is she running from? | 4 of her words incl. Kestrel Lane | owes money / **hiding from someone** / secretly famous | Nora recognises Dorian and is warned; chat mirror line |
| Relay (5) | What will m0th do? | 4 relay words incl. relay server | wipe everything / **come to your door** / go to the police | door: "I knew you'd come" → `doorKnew`, extra day-7 line; chat; police advice |

Wrong answers are usable too (different, weaker reactions); the cross next to an answer lets the player choose again.

## Endings (checked by enumerating every reachable flag combination)
Exactly one main ending, one Nora card, one Dorian card per playthrough.

| Main | Condition |
|---|---|
| Arrest | police raid (address reported after it was sold, before the last night) |
| Turned himself in | chatHelp and (door opened, or he came and nobody opened) |
| He came to your door | door opened, no chatHelp |
| You never opened | he came, door not opened, no chatHelp |
| Club member | chat answer "you've been selected" |

| Nora | Condition |
|---|---|
| Moved in with her sister | noraWarned |
| Fled through the window | break-in happened, not warned |
| Never knew how close he came | Dorian stopped before the break-in, not warned |

| Dorian | Condition |
|---|---|
| Back behind bars | copsDorian |
| Still out there | never reported |

## Recording
Disabled: `recordings` is empty, so the record button shows the game's "cannot record" message. The masked
confession on day 5 is still a story scene, but there is no Shock.tv video to sell.

## Validator
`validate_cage.py`: 0 errors, 0 warnings (v2.1).

## v2.1: clue → notebook word → deduction → use (feedback item 3)
| Observed (where) | Notebook words | Deduction | What it is used for |
|---|---|---|---|
| Crow's job post (d1_job), DarkBoard page, inbox "court: order granted" (d3_result), court news | crow, bounty, darkBoard, restraining order | **Crow (circle 4)** "?" from 3 words + restraining order: debt collector / **her ex** / a cop | "her ex" adds **Dorian Pell** (keyword `addWords`); search "her ex" (alone or with "restraining order") opens the court record; Nora call → she names Dorian and is warned; police → asks his name (follow-up); chat → chatHelp. Wrong answers: Nora suspects a trick, police say "civil matter" / ask for a badge number. |
| Nora's profile and posts (d1_profile), bakery call (d2_call), breakfast photo (d2_photo) | Sweet Crumb, Biscuit, blue bike, Kestrel Lane, sister | **Nora (circle 1)** "?" from 4 of her words incl. Kestrel Lane: in debt / **hiding** / famous | Search "hiding" = stalking article with the tip line; "hiding" + "Sweet Crumb" = bakery notice (photos removed, call 555-0110); Nora call → she names Dorian; police → "a name?" follow-up; chat → mirror. |
| Task manager, traceroute, relay page, mask video (d4–d5) | poc_relay, club member, tape, traceroute, relay server, moth mask, phototaxis | **Relay (circle 5)** "?" from 4 relay words incl. relay server: wipe it all / **your door** / the police | Search "your door" = doorstep-safety article; "your door" + "relay server" = the Club's own alert; chat → threat line; police → "lock your door". |
| Pizza order said aloud (d1_pizza) | Pizza Now, 22 Gorse St, 555-0193, m0th | - | Search "Pizza Now" = shop only; **"Pizza Now" + "m0th" or "+ 555-0193"** = the order (address, phone). Address → police raid (after the address is sold). |
| Mom's call (d3_mom) | Elias Krumm | - | MeetaU profile; police follow-up "a real name?" |
| Day-2 newspaper, court letter (d3_result), wiki | 555-0110, City Police | - | police box; reporting Dorian on day 3 prevents the break-in |

Notebook words are short, like the game's own: names capitalised (CROW, DORIAN PELL), things lowercase, deduction answers two or three words.

## v2.1: searches (feedback item 2)
A general word gives a general page; the investigation page needs two words (entry `a_b`, either order).
| Search | Result |
|---|---|
| Crow | encyclopedia: the bird |
| Crow + DarkBoard | Crow's DarkBoard profile (no name on it) |
| Crow + Dorian Pell | old car forum: same avatar, signed D. Pell |
| Dorian Pell / her ex / her ex + restraining order | court news (no alias) |
| Pizza Now | shop page ("search with your name or phone to track an order") |
| Pizza Now + m0th / + 555-0193 | order #4471 |
| m0th | his DarkBoard ad (no real name any more) |
| club member | nothing (too general); relay server → relay page |
| hiding / hiding + Sweet Crumb | stalking article / bakery notice |
| your door / your door + relay server | doorstep safety / Club alert |

## v2.1: police follow-ups (feedback item 4)
The officer's question is a keyword node in the same call (the notebook opens again), with an "I don't know" fallback:
- "A name?" (report about Nora / hiding) → Dorian Pell = arrest, her ex = "he has a file, his name?", Crow = "a nickname, real name?", m0th / Elias = alias / address questions;
- "A real name or an address?" (report about m0th / Crow) → Elias Krumm = "where does he live?", 22 Gorse St = raid / not yet / nobody home (by phase).

## v2.1: cage LED, pause and end (feedback items 1 and 5)
- LED (game help: "LED lit: activity detected in the cage"): on while something happens, off as soon as the screen sleeps (`sleep_screen` stops it). Before v2.1 it stayed lit through the sleeping screensaver, up to 00:40 on day 6.
- **Pending** (the game's own state, notebook stamped PENDING, notice "Cage N is now PENDING"): only for the police raid. The call that orders the raid sets `copsMoth` and `pendingDiary`; the notebook page is disabled for the 2 hours until the raid scene, so no further calls, searches or deductions can contradict it. The raid ends the cage (**CLOSED**, "Cage N is now CLOSED").
- Every other ending goes straight on: the investigation stays open until d7_end, which ends the cage. Calls in between cannot change the main ending (it depends on the door visit and the chat), only the Dorian card, which is consistent with the story.

| Ending path | Waiting | End |
|---|---|---|
| Police raid | PENDING from the call, about 2 h | raid scene → CLOSED |
| Door / no door / turn-in / member | none (story continues) | d7_end 14:00 → CLOSED |


## v2.2: conversations keep going
- Chat (day 5): after each first answer and its follow-up the player says "Wait. One more thing." and reaches a hub:
  ask who Crow is (askCrow), why he took the job (askJob), what he will do (askNext), show notebook words
  (Nora, Dorian, her ex, his address, his name, your door, Byte), or "Goodbye, Elias." (the only end).
  Asked questions disappear from the hub. The hub sets no ending variable; only the first answer does
  (chatClub / chatMirror / chatHelp / chatLie / chatThreat), so d5_chat and the endings are unchanged.
- Day-6 call: one more choice after "look at your door" (don't come / I'll be waiting / silence).
- Door (01:00 day 7): one more choice after "so you know how it feels" (come in? / go home, Elias / close the door).

## v2.3
- Merged night scenes keep their LED-off actions (the merge used to strip every stopLed, so the LED burned through
  the sleeping screen on all merged nights, most visibly the night he leaves). The dawn part no longer wakes the screen.
- Door: no notebook option (opening the notebook during the door talk froze the game) and no close-door options.
  The relay deduction keeps its other uses (search, chat, police).

## v2.4: keywords and notebook (user review of the keyword table)
Full notebook picture: `筆記本關鍵詞全圖_v2.4.png`. Review documents: `關鍵詞線索表*.md`.

Notebook
- Removed words: mom, twoStep, osint, mothPhone (old tags are stripped at build time; text ids stay stable).
- **Identity deduction** on the methods circle (3): "?" when 4 of its 7 words incl. H4CK SCHOOL;
  amateur hacker (right) / private eye / detective. The original page's arrow 5 (circles 2-3) appears once it is solved.
- Nora's box: name, 555-0147, and **Kestrel Lane 14** written just above the box (a copied slot; the frame cannot
  hold three Chinese lines). Kestrel Lane is not an address keyword (MART parcels would trigger m0th's lines) and is
  also listed in circle 1's zone so the Nora deduction (3 of 5 words + Kestrel Lane) can see it.
- m0th's box: m0th + 22 Gorse St; the box moves left so the Crow "?" and its answer sit next to the circle.
- New word **Nora Pell** (her married name; d3_number 18:00). Answers renamed: 前任; 躲债人 / 离异分居 / 明星;
  删除 / 上门 / 自首.

Searches: m0th alone = a garage band wiki; m0th + amateur hacker = his DarkBoard ad; amateur hacker = script-kiddie
wiki; Nora Pell = 6-year-old wedding notice with Dorian; relay server finds nothing (no relay page, no Club alert).

Nora call, phase A (needs proof): a vague warning (Nora, m0th, Crow, amateur hacker, fake courier) leads to P2,
one that points at Dorian (Dorian, her ex, separated) to P3: "tell me something only someone looking for me would
know". Kestrel Lane or Nora Pell convinces her (then the warning as before); Sweet Crumb / Biscuit / bike are on her
profile ("anyone can see that", hang up); nothing = hang up. Kestrel Lane and Nora Pell as the first word warn
directly. Phase C: fake courier ("A parcel for Nora"), Nora Pell. Warned: sister, fake courier.

Police: Kestrel Lane, intruder, fake courier -> "who? a name?" (node 6); Nora Pell -> "Dorian Pell's ex-wife?"
-> arrest (or "in custody"); amateur hacker -> "alias not enough"; private eye -> "who hired him?" (Dorian / m0th /
Elias); detective -> badge number.

Chat: first answer also takes amateur hacker (chatMirror), private eye / detective (chatLie), Nora Pell (chatHelp);
"turn himself in" still sets chatHelp (user left it). Hub adds amateur hacker, fake courier, Nora Pell, mask, tape,
traceroute, night shift.

Not done: a second Club mission (the game has one mission mail per cage); City Police still only from the tip line
page (user's choice).

## v2.4.1: notebook layout by relationship (user's sketch)
Needs ModLoader 0.5.9 (diary moves/copies take `sx`/`sy` scale).
- Top: m0th's circle with his box (m0th, 22 Gorse St) under it, arrow to the methods circle; relay circle top right.
- Bottom: Crow's circle -> arrow (copy of arrow 5, shown when the Crow and Nora deductions are both answered) with
  Nora's answer "separated" written on it -> Nora's box (frame scaled 1.2 x 1.6, three lines inside: Kestrel Lane 14,
  555-0147, Nora Vance) -> Nora's circle. Police box bottom right.
- Layout data: `moth_pages.py` CIRCLE_SHIFT / ANSWER_SHIFT / NORA_BOX / ARROW_COPIES / POLICE_BOX_AT (screen pixels
  of a 1280x720 window); `build_moth.py` moves each shifted circle with its "?", remove icon, word and answer slots.

## v2.5: second feedback round (request_for_2.txt)
- "her ex" no longer writes Dorian Pell (no keyword addWords); alone it finds the stalking article. The court news
  needs Dorian Pell, or her ex + restraining order.
- Two words for Nora's street: kestrelLane "Kestrel Lane" (day-2 photo; Nora's circle, free videoCorrecto slot moved
  into it; the Nora deduction needs it) and kestrel14 "Kestrel Lane 14" (only from d3_number 18:00 on; Nora's box).
  Every call/chat keyword node that takes kestrelLane also takes kestrel14.
- m0th's phone number no longer appears in any text.
- Gift: the hacker hands the jar over at the door (door node 1 onCallEnd addPrize, if mothVisited, like the game's own
  Wylon visitors). No mailman. The freeze: the game shows a prize by activating prizeHolderItems/<id> and reads that
  object's prizeInterface.popupBackground; a prize without its own shelf object threw there and left the popup
  blocking. ModLoader 0.5.10 "prizes" copies an original prize object (coca), registers it in main.objects (the game
  finds shelf objects with GameObject.Find, which skips inactive ones) and replaces its pictures. The game has no
  shelf-slot system (every prize has its own fixed spot); the jar sits on the small cabinet left of the door, a spot
  no original prize uses, so it never collides. Art: tools/moth_prize.py (placeholders), art_override/prize/.
- More dialogue: Nora (sister, bakery, cat, bike in every phase; public details do not prove anything), police
  (DarkBoard, bounty, H4CK SCHOOL, Pizza Now, Byte, free VPN, relay), m0th's day-6 call (notebook answers), chat hub.
