# Rally · Pickleball culture, shaped by people

**Live website:** https://kjincs.github.io/pickleball-rally/

Rally is a bilingual pickleball publication for women who play or are curious about the sport. Read concise, source-linked stories, leave comments using a GitHub account, and help shape the next edition. The story-language selector switches between English and Simplified Chinese. The library searches across languages and previous editions.

## Comment-only feedback

This testing version accepts feedback from **any GitHub user**. No invitation, collaborator access, or username list is required. Click **Leave feedback** under a story (or **Review the edit** for the whole edition), write a comment in English or Chinese, and submit the GitHub issue. Ratings and more/less preferences are optional. Feedback is public, so do not include private information.

Edit your feedback issue to change a response. The newest valid submission per person/story/edition wins. Closed issues are included. The next research run reads recent reviews from the last six weeks; comments received after its snapshot inform a later edition. A comment alone counts. A completely empty submission does not.

## Daily publication

Research runs in a **scheduled task in the signed-in Codex app**, using this local project. No OpenAI API key or separate AI API billing setup is required. Your account’s Codex usage limits still apply. Keep the computer powered on with the app running for local scheduled work.

The daily task is intended for **8:17 a.m. America/Chicago**. Its instructions live in `AGENTS.md`. It:

1. Reads public GitHub reviews and the permanent editorial brief.
2. Searches English and Chinese sources for court style, community stories, meaningful news, trends, and paddle knowledge.
3. Opens original pages and prepares faithful bilingual summaries. Public social/forum posts are attributed perspectives, not verified general reporting. Inaccessible or login-only posts are skipped.
4. Checks dates, source evidence, duplicate URLs, bilingual fields, and story limits. It avoids repeat coverage and keeps an exploratory subject where suitable material exists.
5. Saves a new edition, runs checks, commits content, and pushes to GitHub.
6. Verifies the **Publish website** deployment. If research or publishing fails, the last successful edition remains available.

There is no daily owner approval. A scheduled edition already published for the local date is not duplicated. The owner can ask Codex for an extra edition. Existing editions remain available in the archive.

GitHub Actions only tests and deploys saved website files; it does not call the AI. The obsolete API research workflow has been removed. The website stays readable if this computer is asleep, but new content waits for a successful Codex run.

## Configuration

Edit `config.json` to change the editorial brief, preferred sources, edition size, and source-language preferences. Source lists guide discovery; credibility is evaluated per source and claim, rather than assuming all posts on a platform are trustworthy.

`review_mode: "open"` considers all public GitHub reviewers. Later, if needed, set `review_mode: "trusted"` and add GitHub usernames to `trusted_reviewers`; the repository owner is included automatically in trusted mode. Leave open mode for this testing version.

If moving the repository, update `repository` in config.json and the repository/site references in AGENTS.md. The Pages workflow assumes the default branch is main for push events.

## Local preview and checks

```sh
python3 -m http.server 4173 --bind 127.0.0.1
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Open http://127.0.0.1:4173/. Use HTTP rather than opening index.html directly. There are no package installs or build dependencies; Python 3.9+ works locally, and GitHub uses Python 3.12.

`build.py` packages public files into `_site/`. This directory is generated, ignored by Git, and can be removed after verification. The deployment does not include scripts, tests, drafts, or raw review snapshots.

## Preparing an edition without a key

```sh
python3 scripts/generate.py --context /tmp/rally-context.json
```

This reads the public GitHub issues with no key. The standard library HTTPS request may need network access in the local sandbox. An existing `GITHUB_TOKEN` can optionally be used for higher GitHub rate limits, but is not required. If feedback cannot be retrieved, do not pretend there were no reviews: resolve the fetch or retain the previous edition.

Codex reads the snapshot, researches with its search tools, and writes `/tmp/rally-draft.json` using the schema in AGENTS.md. Source evidence records what was actually opened and checked. Then:

```sh
python3 scripts/generate.py --publish /tmp/rally-draft.json
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

The publisher validates the whole draft before updating the edition index. It rejects previous URLs, uncited links, future dates, undated/stale items labeled news, invalid bilingual fields, and oversized editions. These checks do not independently prove every statement or translation is correct. The research task must verify the sources and preserve their context.

Commit content under `data/` and push main. GitHub’s **Publish website** workflow publishes it. Check Actions and the live page to verify success. Do not publish if checks fail or if conflicting local/remote work needs attention.

## Files kept in this project

- `index.html`, `assets/`: responsive reading interface and original SVG illustrations.
- `config.json`: editorial and feedback configuration.
- `data/index.json`, `data/editions/`: permanent edition archive and source evidence.
- `data/preferences.json`: aggregate search guidance.
- `.github/ISSUE_TEMPLATE/review.yml`: public feedback form with optional score.
- `.github/workflows/pages.yml`: validation and website deployment.
- `scripts/generate.py`: public-review collection, validation, and draft publication; no AI API calls.
- `scripts/build.py`: public-file packaging.
- `tests/test_pipeline.py`: meaningful review and publication checks.
- `AGENTS.md`: durable instructions for the daily Codex task.

Temporary drafts, snapshots, screenshots, `_site/`, and Python caches do not belong in the repository. Do not delete historical editions as “temporary” files; they are the reader’s knowledge library.

## Editorial notes

Every story links to its publisher and shows a publication date or explicit unknown date, original language, and source type. Older material is labeled evergreen. Brand announcements and forum/social experiences are distinguished from reporting. Illustrations are original art, not pictures of reported events. No publisher photographs or full articles are copied.

Reader preference helps choose interesting content; it does not verify facts. Correct mistakes explicitly in the affected summary and commit a correction, rather than silently rewriting the historical record.

The founding edition is a source-linked starter collection. Subsequent editions are researched through the signed-in Codex session. A short edition with solid sources is preferable to filling slots with weak or repetitive material.
