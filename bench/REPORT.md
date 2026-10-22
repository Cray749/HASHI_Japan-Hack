# Noise benchmark report

Run on 2026-10-22 · faster-whisper small (int8, CPU) · AMD64 Family 23 Model 96 Stepping 1, AuthenticAMD / Windows · took 2986 s

Clip sources: **synthetic**. Speakers: hi-madhur, hi-madhur-fast, hi-swara, pa-gtts, pa-gtts-quick, pa-gtts-slow.

## Question
How often does the crew card show the right request when the passenger speaks in cabin noise?

* **A: plain speech-to-text then translation.** The speech engine translates the clip to English; the English text is matched to a request using the English phrase bank only (this hands the baseline our own matcher, which is generous to it).
* **B: HASHI.** The engine transcribes in the passenger's language and the text is matched to the closed request list. **B+** is the same with the spectral-gating cleanup applied first.

Success means the top request equals the request the speaker meant.

## Results

| Language | Noise | A: speech-to-text + translation | B: HASHI | B+: HASHI with cleanup | B+ right request in top 3 |
| --- | --- | --- | --- | --- | --- |
| Hindi | clean | 82% (49/60) | 88% (53/60) | 88% (53/60) | 93% (56/60) |
| Hindi | 10 dB | 82% (49/60) | 93% (56/60) | 93% (56/60) | 95% (57/60) |
| Hindi | 0 dB | 68% (41/60) | 72% (43/60) | 60% (36/60) | 68% (41/60) |
| Punjabi | clean | 52% (31/60) | 90% (54/60) | 90% (54/60) | 95% (57/60) |
| Punjabi | 10 dB | 53% (32/60) | 87% (52/60) | 88% (53/60) | 95% (57/60) |
| Punjabi | 0 dB | 37% (22/60) | 58% (35/60) | 48% (29/60) | 65% (39/60) |

### Overall by noise level (both languages)

| Noise | A | B | B+ |
| --- | --- | --- | --- |
| clean | 67% (80/120) | 89% (107/120) | 89% (107/120) |
| 10 dB | 68% (81/120) | 90% (108/120) | 91% (109/120) |
| 0 dB | 52% (63/120) | 65% (78/120) | 54% (65/120) |

### What the passenger would see (B+)

HASHI only sends straight away when it is confident; otherwise it shows the top pictures to confirm.

| Noise | Sent directly and right | Sent directly but wrong | Asked to confirm | Fell back to tiles |
| --- | --- | --- | --- | --- |
| clean | 61 | 2 | 57 | 0 |
| 10 dB | 49 | 0 | 68 | 3 |
| 0 dB | 24 | 11 | 64 | 21 |

### By speaker (B+, all noise levels)

| Speaker | Right request |
| --- | --- |
| hi-madhur | 80% (48/60) |
| hi-madhur-fast | 78% (47/60) |
| hi-swara | 83% (50/60) |
| pa-gtts | 78% (47/60) |
| pa-gtts-quick | 77% (46/60) |
| pa-gtts-slow | 72% (43/60) |

Speech engine time per clip on this machine: median 2.8 s.

## Failures at 0 dB (B+), for inspection

| Language | Meant | HASHI picked | Engine heard |
| --- | --- | --- | --- |
| Hindi | water | unwell | तबीयत नहीं है, तबीयत नहीं है, तबीयत नहीं है, तबीयत नहीं है, तब |
| Hindi | blanket | water | एक गलास पानी, एक कंबल लाए दीजीए |
| Hindi | blanket | unwell | तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, |
| Hindi | blanket | unwell | तबीवाई, तबीवाई, तबीवाई, तबीवाई, तबीवाई, तबीवा� |
| Hindi | food | unwell | बहुत फुप लगी है, उचाने को मिलेगा |
| Hindi | toilet | wheelchair | तोलिक किस तरफ है? |
| Hindi | toilet | wheelchair | तवाले किस तरव है, तवाली किस तरव है |
| Hindi | toilet | unwell | तबीयत ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक � |
| Hindi | help | unwell | तबीयत बाई नहीं है, तबीयत नहीं है, तबीयत नहीं है, तबीयत नहीं है |
| Hindi | tea_coffee | unwell | तबीयत ठीक, तबीयत ठीक, तबीयत ठीक, ठीक, ठीक, ठीक, ठीक, ठीक, ठी |
| Hindi | tea_coffee | unwell | तबीयत, बाई, बाई, बाई, बाई, बाई, बाई, बाई, बाई, बाई, ब |
| Hindi | tea_coffee | unwell | तबीयत ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक ठीक � |
| Hindi | pillow | unwell | तबीयत दवाई, तबीयत नहीं है |
| Hindi | pillow | unwell | तबीयत देदीजीए |
| Hindi | too_hot | breathing | आई साहिए, आई साहिए, आई साहिए, आई साहिए, आई साहिए, आई साहि� |
| Hindi | too_hot | too_cold | यहाँ बवोड़ तरनी लग रही है |
| Hindi | headphones | medicine | फिल्म देखनी है, है भों देवीजीगी |
| Hindi | headphones | medicine | प्रुम दिखनी है, प्रुम देदीजे |
| Hindi | breathing | food | तबाई साहिए, साहिए, साहिए, साहिए, साहिए, साहिए, साहिए, साहिए, स |
| Hindi | breathing | unwell | तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, तबीयत, |
| Hindi | form_help | help | यह जापान वाला फोम रहने में मदध की जी |
| Hindi | form_help | help | यह जाबान बाला फुर्म शौचने में मदध की जी |
| Hindi | juice | unwell | तबीयत बाई, बाई, बाई, बाई, बाई, बाई, बाई, बाई, बाई, बा |
| Hindi | charger | unwell | तबीयत नहीं है, तबीयत नहीं है |
| Punjabi | blanket | help | इक सब वल्दि आद्यो ती लाए इस् |

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
