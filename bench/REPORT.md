# Noise benchmark report

Run on 2026-10-22 · faster-whisper small (int8, CPU) · AMD64 Family 23 Model 96 Stepping 1, AuthenticAMD / Windows · took 2906 s

Clip sources: **synthetic**. Speakers: hi-madhur, hi-madhur-fast, hi-swara, pa-gtts, pa-gtts-quick, pa-gtts-slow.

## Question
How often does the crew card show the right request when the passenger speaks in cabin noise?

* **A: plain speech-to-text then translation.** The speech engine translates the clip to English; the English text is matched to a request using the English phrase bank only (this hands the baseline our own matcher, which is generous to it).
* **B: HASHI.** The engine transcribes in the passenger's language and the text is matched to the closed request list. **B+** is the same with the spectral-gating cleanup applied first.

Success means the top request equals the request the speaker meant.

## Results

| Language | Noise | A: speech-to-text + translation | B: HASHI | B+: HASHI with cleanup | B: right request in top 3 |
| --- | --- | --- | --- | --- | --- |
| Hindi | clean | 82% (49/60) | 95% (57/60) | 95% (57/60) | 95% (57/60) |
| Hindi | 10 dB | 82% (49/60) | 95% (57/60) | 93% (56/60) | 97% (58/60) |
| Hindi | 0 dB | 68% (41/60) | 75% (45/60) | 58% (35/60) | 87% (52/60) |
| Punjabi | clean | 52% (31/60) | 90% (54/60) | 90% (54/60) | 97% (58/60) |
| Punjabi | 10 dB | 53% (32/60) | 87% (52/60) | 88% (53/60) | 95% (57/60) |
| Punjabi | 0 dB | 37% (22/60) | 58% (35/60) | 48% (29/60) | 70% (42/60) |

### Overall by noise level (both languages)

| Noise | A | B | B+ |
| --- | --- | --- | --- |
| clean | 67% (80/120) | 92% (111/120) | 92% (111/120) |
| 10 dB | 68% (81/120) | 91% (109/120) | 91% (109/120) |
| 0 dB | 52% (63/120) | 67% (80/120) | 53% (64/120) |

### Reading the numbers

* **clean:** HASHI (B) is +26 points against plain speech-to-text plus translation (A); the cleanup step (B+) is +0 points against B.
* **10 dB:** HASHI (B) is +23 points against plain speech-to-text plus translation (A); the cleanup step (B+) is +0 points against B.
* **0 dB:** HASHI (B) is +14 points against plain speech-to-text plus translation (A); the cleanup step (B+) is -13 points against B.

### What the passenger would see (B, the shipped setting)

HASHI only sends straight away when it is confident; otherwise it shows the top pictures to confirm.

| Noise | Sent directly and right | Sent directly but wrong | Asked to confirm | Fell back to tiles |
| --- | --- | --- | --- | --- |
| clean | 57 | 0 | 61 | 2 |
| 10 dB | 54 | 0 | 60 | 6 |
| 0 dB | 27 | 1 | 78 | 14 |

### By speaker (B, all noise levels)

| Speaker | Right request |
| --- | --- |
| hi-madhur | 87% (52/60) |
| hi-madhur-fast | 90% (54/60) |
| hi-swara | 88% (53/60) |
| pa-gtts | 82% (49/60) |
| pa-gtts-quick | 78% (47/60) |
| pa-gtts-slow | 75% (45/60) |

Speech engine time per clip on this machine: median 2.7 s.

## Failures at 0 dB (B), for inspection

| Language | Meant | HASHI picked | Engine heard |
| --- | --- | --- | --- |
| Hindi | food | unwell | बहुत फुट लगी है, उचाने को मिल |
| Hindi | medicine | meal_time | भी बवाई काने का समय होगया है |
| Hindi | dizzy | tea_coffee | मुझे चग्गर आरगीजें |
| Hindi | tea_coffee | juice | अग, तब चाए मिल सकती है क्या? |
| Hindi | tea_coffee | juice | एक सब चाई मिल सक्ती है क्या? |
| Hindi | tea_coffee | juice | एक भब चाई मिल सबती है क्या? |
| Hindi | veg_meal | food | मैं सर्फ शाखा हरी खाना काता |
| Hindi | veg_meal | food | मैं सर्व शाका हारी खाना काता |
| Hindi | pillow | water | एक पक्या दे दीजिये |
| Hindi | pillow | allergy | यह दख्या देड़ीजीए |
| Hindi | headphones | wheelchair | पिल्म देखनी है, हेट्फों दै दी� |
| Hindi | headphones | chest_pain | फिल्म देखनी है, है पुन दिल भी ज |
| Hindi | headphones | medicine | विन दिखनी है रेफों देदीजे |
| Hindi | breathing | too_cold | तब आद बाद़़ी बच्छाएगे � |
| Hindi | juice | toilet_help | तुब आप तो बज़़ा तरीए बा� |
| Punjabi | blanket | language_help | इक सब वल्जी आदी अटी लाए। |
| Punjabi | food | screen_help | बाद बोखलगती है, पुच खानू मि |
| Punjabi | food | unwell | बहुत पोख लगी है, पुज़ खान � |
| Punjabi | toilet | thanks | तालिट किस पासे है जी |
| Punjabi | toilet | family_seat | ताईलिप के स्पासे हैजी |
| Punjabi | toilet | thanks | तालिप की सबासे है जी? |
| Punjabi | help | baby_help | ॐ ृ ौ ू ॉ ै ु ॑ ो ॄ � |
| Punjabi | dizzy | unwell | मैंनु चब्रा रहीं लेए। |
| Punjabi | tea_coffee | meal_time | इक कब जा मिल सकती है |
| Punjabi | tea_coffee | meal_time | इस कब चाल मिल सकती है |

## Sample of baseline A output (0 dB)

| Meant | English the crew would have read |
| --- | --- |
| water (Hindi) | Sir, can I get a glass of water? |
| blanket (Hindi) | Give me a cup of water. |
| food (Hindi) | I am very hungry. Can I get something to eat? |
| toilet (Hindi) | Toilet on which side? |
| medicine (Hindi) | It's time to take my medicines. |
| help (Hindi) | Please help us. Come soon. |
| chest_pain (Hindi) | My chest is hurting a lot. |
| dizzy (Hindi) | I am feeling dizzy |
| tea_coffee (Hindi) | Can I get a cup of tea? |
| veg_meal (Hindi) | I only eat Shakahari food. |
| pillow (Hindi) | Give me one bottle of water. |
| too_hot (Hindi) | Sir, it's very hot here. |

## Limits (read before quoting any number)

* Clips are **synthetic** (text-to-speech voices, with simple speed/pitch variants as extra "speakers") unless the source line above also lists `real`. Synthetic voices are cleaner and more regular than frightened or elderly people with accents, so real-world accuracy will be lower.
* Noise is **synthetic** cabin noise (steady engine rumble and tones plus faint background voices) mixed at the stated signal-to-noise ratios. It is not a recording from an aircraft.
* The test sentences are one per request per language, 20 per language. Small samples: treat a difference of a few clips as noise.
* The request list is closed (about 40 requests). Free speech outside the list falls back to tiles by design.
* Baseline A uses our own matcher on the English text, so it is a stronger baseline than a human reading raw machine translation would be, but it does not model how well a crew member would guess the meaning.
* To add real recordings see `bench/README.md` and re-run `make bench`.
