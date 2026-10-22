# Three-minute demo

**Setup before the room fills:** laptop hotspot on, `python run.py --https --demo`, tablet on the crew page, one phone on the passenger page (seat 24C, Punjabi, senior mode on). Internet off on the laptop. Keep the speech model loaded (`/api/health` shows `asr_ready`).

## 0:00 The problem (20 s)
"A cabin is 80 decibels. Mr. Singh is 72, speaks Punjabi, and does not want to trouble anyone. We don't translate. We understand."

## 0:20 Anticipate (30 s)
* Tablet: open **Seats**. Seat 24C carries a chip: Punjabi, senior, first flight, hard of hearing.
* Open **Greet** → Punjabi → read the katakana line aloud. "The crew learn three words. The passenger doesn't have to learn anything."

## 0:50 Understand (60 s)
* Phone: tap **Water** (picture tile). The tablet shows the card in Japanese with an English subtitle within a second or two.
* Phone: hold the microphone and say a Punjabi request, for example "ਮੈਨੂੰ ਕੰਬਲ ਚਾਹੀਦਾ ਹੈ". The card appears. If the match is unsure the phone asks "Did you mean…?" with pictures.
* "We match meaning against about forty cabin requests instead of transcribing everything. That is what makes noisy, accented speech workable." Show the benchmark table in `bench/REPORT.md` if asked.

## 1:50 Confirm (40 s)
* Tablet: tap **On my way**, then **I will bring it shortly**.
* Phone: the reply arrives as picture, large text and audio. Tap **I understood**. The tablet card turns green.
* Tablet: **Announce** → "Seat belt sign on" → all seats. Phone shows it large; do not tap yet. The board shows the seat as not confirmed. Tap on the phone; the board updates.

## 2:30 Safety and exit row (20 s)
* Tablet: **Exit row** → row 24 → start. Phone shows the teach-back. Answer "As soon as the plane stops" to show the red "check in person" state.
* Phone: press the big red **I need help** button. The red banner pins to the top of the tablet and the seat blinks on the map.

## 2:50 Close (10 s)
"Offline, no new hardware, two taps for crew, data deleted at landing. Tablet: **Landed** wipes everything."

## If something fails
* **Voice fails or is slow:** "That is the fallback ladder working" and use the tiles.
* **Phone loses Wi-Fi:** it reconnects by itself; the queued request goes when it returns.
* **Crew page blank:** reload; cards come back from the server.
* **No phone available:** `python scripts/demo_traffic.py sequence` sends scripted requests from fake seats.
