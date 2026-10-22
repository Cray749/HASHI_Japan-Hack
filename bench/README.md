# Noise benchmark

Compares, for Hindi and Punjabi requests heard in cabin noise:

* **A:** plain speech-to-text, translated to English, then read as a request.
* **B:** HASHI's approach, speech-to-text in the passenger's language matched against the closed list of cabin requests (**B+** adds the noise cleanup).

Metric: share of requests where the crew card would show the right request.

## Run it

```bash
python -m pip install -r server/requirements.txt -r server/requirements-voice.txt
python scripts/get_models.py small       # once, needs internet
python -m bench.run                      # full run, writes bench/REPORT.md and bench/results.json
python -m bench.run --quick              # 6 requests, 1 voice, for a fast check
python -m bench.run --model base         # lighter model on a slow machine
```

The first run downloads synthetic voices (edge-tts for Hindi, gTTS for Punjabi) into `bench/.cache/`; later runs reuse them. A full run takes tens of minutes on a laptop CPU.

## What is in the test set
`testset.yaml` holds 20 requests per language, one sentence per request, written separately from the phrase bank so the matcher is not graded on sentences it was built from. Add more rows to widen it.

Synthetic speakers: three per language. Hindi uses two neural voices and a faster, lower variant. Punjabi uses one voice plus slower and quicker variants made by resampling, so they are the same voice at different tempo and pitch, not different people. The report states this.

Noise: synthetic cabin noise (steady rumble with engine tones and faint background voices) mixed at 10 dB and 0 dB signal-to-noise, plus a clean pass for reference.

## Adding real recordings (please do this before quoting results)
1. Record each sentence from `testset.yaml` with at least three different speakers, ideally with background noise playing from a speaker. Use a phone and save as WAV or MP3.
2. Put the files in `bench/real/` and add `bench/real/manifest.csv`:

   ```csv
   file,lang,speaker,gold
   hi_anna_01.wav,hi,anna,water
   pa_dev_07.wav,pa,dev,chest_pain
   ```

   `gold` is the request id from `data/intents/intents.yaml`.
3. Re-run `python -m bench.run`. The report lists real clips as a separate source and the speaker table shows them.

Real clips are not committed by default (they are recordings of people). Keep consent notes with them.

## Reading the report
Check the "Limits" section first. Twenty sentences per language is small, so a gap of one or two clips is noise. The failure table lists what the engine heard, which is the best guide to which phrases to add to the bank.

## What the benchmark has already taught us
* A first run showed that giving the speech engine a "cabin words" prompt made it repeat the prompt in loud noise (for example "I feel unwell" over and over), which the matcher then trusted. The prompt was removed, looping transcripts are collapsed and never sent without confirmation, and the run was repeated. If you change the speech settings, re-run the benchmark and read the failure table.
* The spectral-gating cleanup did not help the speech engine at 0 dB, so voice requests skip it by default (`cleanup=1` on `/api/voice` turns it on).
* `python -m bench.rescore` rebuilds the report from the saved transcripts if only the phrase bank changed.
