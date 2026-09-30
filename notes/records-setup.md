# Turning the record boards on

The game's timed modes (5, 10, 30, 60 minutes) work already, with a personal
best per mode saved on each player's own device. What is **not** on yet is the
shared leaderboard, because it needs a tiny online service to hold the scores.
This is the ten-minute job of connecting one.

Until you do, nothing about the site changes: no board, no "Submit" button, and
the privacy page says nothing is collected. The moment you do, the privacy and
terms pages switch themselves to describe the board and name `Discord @bperk`
for removals. You do not edit them.

The menu names below are from memory of Cloudflare's dashboard and may be worded
slightly differently. If a step doesn't match, the goal is in bold.

## 1. Make a Cloudflare account

Free, at cloudflare.com. No card needed for what this uses (check their current
free limits; nothing here should come near them for a friends-only board).

## 2. Create the service

1. **Workers & Pages** -> **Create** -> **Create Worker**.
2. Name it `hall-records` and press **Deploy** (it will deploy a hello-world).
3. Press **Edit code**, **delete everything**, and **paste in the whole of
   `worker/records.js`** from this repo. Press **Deploy**.

## 3. Give it somewhere to keep scores

1. **Storage & databases** -> **KV** -> **Create a namespace**. Call it
   `hall-records`.
2. Back on the Worker: **Settings** -> **Bindings** -> **Add** -> **KV
   namespace**.
3. **Variable name must be exactly `RECORDS`** (capitals). Pick the namespace
   you just made. Save, and deploy if it asks.

## 4. Check it is alive

Open `https://hall-records.<your-name>.workers.dev/` in a browser. You should
see `{"service":"hall-of-extremes records"}`. Add `/boards` to the end and you
should see four empty boards: `{"5":[],"10":[],"30":[],"60":[]}`.

If it says `Records storage is not connected`, the binding in step 3 is missing
or misnamed.

## 5. Point the site at it

In `data/site.json` change

```json
"records": {"endpoint": null},
```

to your address, **with no slash and nothing after the `.dev`**:

```json
"records": {"endpoint": "https://hall-records.<your-name>.workers.dev"},
```

Then rebuild and push as usual:

```bash
python3 build.py
```

The build refuses to switch the board on if there is no contact (`site.contact`
or `site.discord`) for removal requests. You have one set, so it will build.

## 6. Try it

Play a 5-minute run, let it finish, put a username in and press **Submit to
records**. Then press **Show records**. Your name should be on the 5-minute
board.

## What players will see

The first time someone opens the Game after the board is on, it fades in behind a
notice with the background blurred: please read the privacy policy, and accept
that the only way to have records removed is to privately message `@bperk` on
Discord. Accept opens the Game; Deny keeps it shut (with a link back to the
Hall). A "Don't ask me again" box remembers the choice on that device.

**Editing the privacy page, or the notice's wording, asks everyone again** --
even people who ticked the box -- because the remembered choice is tied to a
hash of that text. That is deliberate: nobody should be held to wording they
never saw. It also means fixing a typo in `pages/privacy.html` re-prompts
everyone, so batch edits.

The notice only exists while the board does. With the board off, nothing asks
anything and the privacy page says nothing is collected.

## Taking an entry off

Cloudflare -> **KV** -> your namespace -> **View** -> open the key for the board
(`board:5`, `board:10`, `board:30` or `board:60`). The value is a list, best
first, like `{"n":"name","s":143,"t":590000,"d":"2026-10-01"}` per entry. Delete
that entry's braces and the comma beside it, and save. Deleting the whole key
empties that board.

This is also how you honour a removal request from someone DMing `@bperk`.

## Turning it off again

Set `"endpoint"` back to `null`, rebuild, push. The button, the board and the
privacy wording all go away together. The scores stay in KV until you delete the
namespace, so **delete it if you want them gone.**

## Good to know

- **It does not stop cheating.** The answers are in the page, so any score can
  be faked; the service only refuses the plainly impossible (more than two
  levels a second, more than the list holds, a time past the limit). That was
  the decision: it is a board for friends.
- **One line per username**, and only a better score replaces it. Nobody can
  lower someone else's score; someone *could* post a higher one under a friend's
  name. There are no accounts to stop that.
- **Usernames are public** and nobody checks them. The page tells people not to
  use their real name. Geometry Dash's audience skews young, so that line is
  there on purpose.
- **Checking the service's behaviour:** there is no Node on this project, so its
  tests run in a browser instead. `python3 -m http.server 3010 --directory
  worker`, then open `http://127.0.0.1:3010/check.html`. The tab title says
  PASS or FAIL.
- **Other addresses.** The service only accepts submissions from
  `www.b4ylor.com`, `b4ylor.com`, `djkhxled.github.io` and
  `localhost:3003`. If the site ever moves, add a Worker variable
  `ALLOWED_ORIGINS` (comma-separated) to replace that list.
