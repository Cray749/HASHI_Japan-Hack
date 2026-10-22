# Running HASHI with no internet (laptop hotspot)

The whole system runs on one laptop. Phones and the crew tablet join the laptop's own Wi-Fi.

## One-time setup (with internet)

```bash
python -m pip install -r server/requirements.txt -r server/requirements-voice.txt
cd web && npm install && npm run build && cd ..
python scripts/get_models.py small      # speech model, about 460 MB
python scripts/gen_audio.py             # reply and announcement audio
```

After this the system needs no internet.

## On the day

1. Turn on the laptop's mobile hotspot (Windows: Settings → Network → Mobile hotspot; macOS: Internet Sharing; Linux: create a Wi-Fi hotspot).
2. Join the tablet and the phones to that hotspot.
3. Start the server. Use `--https` if phones should use the microphone (phones only allow the microphone on secure pages):

   ```bash
   python run.py --https --demo
   ```

   The terminal prints the crew and passenger addresses.
4. On the tablet open the crew address. Tap **QR** to show the passenger QR.
5. On a phone scan the QR. With `--https` the browser warns about the certificate once: choose "Advanced → continue". The certificate is made by the server itself for the hotspot address.
6. The apps are cached by a service worker after the first visit, so a short Wi-Fi drop does not lose the page. The phone reconnects by itself and sends any request made while offline.

## Checks

* Turn the laptop's internet off (leave the hotspot on). Everything must still work.
* `GET /api/health` shows whether the speech engine is loaded.
* No internet and no model? Voice falls back to picture tiles by design.

## If something is off

| Symptom | Fix |
| --- | --- |
| Phone cannot open the page | Same hotspot? Use the address the terminal prints, not `localhost`. Allow Python through the laptop firewall. |
| Microphone button missing or greyed | The page is not secure. Restart with `--https` and accept the certificate warning. |
| Voice says "please tap a picture" every time | Speech model not loaded yet (see `/api/health`) or noise too high. Tiles still work. |
| Crew tablet shows "Reconnecting" | The tablet left the hotspot. Rejoin; cards reappear. |
