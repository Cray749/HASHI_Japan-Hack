# Language review checklist

Hindi (Devanagari), Punjabi (Gurmukhi) and Japanese strings in this folder have **not yet been checked by a native speaker**. Please check each file and tick it off. Do not describe the wording as verified until this is done.

| File | What to check | Hindi | Punjabi | Japanese |
| --- | --- | --- | --- | --- |
| `intents.yaml` | Passenger tile labels (`hi`, `pa`) are natural and polite; crew card sentences (`ja`) are in polite register | [ ] | [ ] | [ ] |
| `replies.yaml` | One-tap crew replies read warmly, are gender-neutral where possible, and are polite | [ ] | [ ] | [ ] |
| `announcements.yaml` | Safety wording is clear and matches the airline's own phrasing | [ ] | [ ] | [ ] |
| `greetings.yaml` | Katakana spelling sounds right when read aloud; Gurmukhi and Devanagari scripts are correct | [ ] | [ ] | [ ] |
| `phrases.yaml` | Phrasings are what real passengers say; add real transcripts from recordings | [ ] | [ ] | n/a |

Things to look at in particular:

* Medical requests (`chest_pain`, `breathing`, `dizzy`, `unwell`, `injury`) must sound urgent but never give advice.
* Replies avoid gendered verb endings: "we are coming" rather than "I am coming (female)".
* Punjabi labels use the everyday spoken register, not formal Sanskritised words.
* Japanese crew sentences stay in `ます` form or more polite.

Passenger app interface strings live in `web/src/passenger/i18n.ts` and need the same check.
