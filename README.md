# Rally · Pickleball culture, shaped by people

A GitHub Pages publication for women who play pickleball. Readers browse concise, source-linked stories. Invited reviewers use GitHub Issue Forms to score stories, select preferences, and comment. A daily GitHub Actions workflow researches and publishes the next edition using that feedback.

English and Chinese sources are supported. Use the **Story language** selector for bilingual titles, summaries, and reasons to read. Search works across both languages. Forum/social items are labeled community perspectives; inaccessible/login-only posts are skipped. Preferred community platforms are discovery targets, not endorsements of every author. The founding collection includes a Chinese source; future source diversity depends on what can be checked.

No database, separate server, JavaScript build tools, or Python dependencies are required. GitHub accounts are required to submit reviews; reading is public.

## Launch this repository

1. In **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
2. In **Settings → Secrets and variables → Actions → New repository secret**, create **OPENAI_API_KEY** using your OpenAI API key. Never put the key in config.json, issues, commits, or chat.
3. Edit `config.json`: add your friends’ GitHub usernames to `trusted_reviewers`. The repository owner (`kjincs`) is always included. Example: `"trusted_reviewers": ["friend-one", "friend-two"]`. Until friends are added, their reviews can be submitted, but do not influence research.
4. Ensure **Issues** is enabled under Settings → General → Features. The form is available after these files are on the default branch (`main`).
5. In **Actions → Publish website → Run workflow**, publish the founding collection. The expected address is **https://kjincs.github.io/pickleball-rally/**; the Pages deployment reports the actual URL.
6. Open **Actions → Prepare next edition → Run workflow** to test a real AI-researched edition. This incurs AI API usage. The workflow commits the edition and explicitly invokes the Pages workflow; it does not rely on a bot commit triggering another workflow.
7. Share the website. Story buttons open a GitHub form with the edition/story IDs prefilled. Reviewers pick a score (1–5), a preference, and an optional comment, then submit the issue. They can edit the issue to update their review.

If generation cannot write its commit, check Settings → Actions → General → Workflow permissions and branch protection. Allow this workflow to write contents on the default branch, or use a dedicated publication branch with an adjusted workflow. Do not disable protections unrelated to this task.

## Automatic daily cycle

- Scheduled for approximately **8:17 a.m. America/Chicago**. Two UTC triggers cover daylight/standard time; a local-time gate runs only once. A successfully generated edition for the date skips a second scheduled run. Manual runs can create additional editions. Change the timezone/hour and cron triggers together if changing the schedule.
- Reads all issue pages, including closed/edited reviews. Filters submissions to owner/trusted usernames and known edition/story IDs. The newest valid review per reviewer/story/edition wins.
- Uses reviews updated within the last six weeks (at most the latest 100 valid reviews in the AI prompt), prior guidance, a permanent editorial brief, and previously published stories.
- Makes two OpenAI Responses API calls: source-grounded web research, then structured formatting. Model defaults to `gpt-4.1`; use the Actions variable **OPENAI_MODEL** or config.json to select another model that supports web search and structured outputs. API access and limits depend on your account.
- Checks candidate URLs against research citation/source URLs, normalizes tracking URLs, rejects repeated URLs and future dates, and requires recent dates for items labeled news. Background reads are labeled evergreen. These automated checks reduce mistakes; they do not prove every claim is true.
- Publishes only if at least one new story passes. Allows shorter editions when material is scarce. Failures retain the existing published site and appear as failed workflow runs.
- Generates original summaries and uses original SVG illustrations. No third-party images are copied. Dates and publishers remain visible.

The feedback note and updated search guidance are automatic; there is no routine owner approval. The owner can run an extra edition from the workflow page. Readers cannot trigger paid searches directly from the public site.

GitHub scheduled workflows can be delayed, and scheduled workflows in inactive public repositories may be disabled by GitHub. Check Actions if editions stop appearing. Workflow concurrency prevents overlapping research runs; a failed push does not overwrite others’ commits.

## Editorial scope and knowledge base

Categories: **Style**, **Community**, **News**, **Trends**, **Paddle knowledge**. `editorial_brief` and `preferred_sources` are editable in config.json. Sources are preferences, not an exhaustive allowlist: research can discover better sources. AI instructions call for topic diversity, cautiously applied preferences, and an exploratory slot when suitable material exists.

The initial founding edition contains real source-linked background reads, clearly marked as a starter collection rather than newly reported news. AI editions start only after credentials are configured and the research workflow succeeds.

Previous editions remain immutable in `data/editions/`. The library searches their story summaries/categories and links to original publishers. This is a source-linked reader library, not a fact-verified encyclopedia or a copy of full publisher articles. `data/preferences.json` preserves aggregate search guidance and review count; raw comments remain in public GitHub issues. Do not submit private information in public reviews.

Corrections: edit a story’s summary/source/date in its edition JSON with an explicit correction note in the summary, then push. If reviewers choose “Check the facts or source,” it informs the next research run; it does not silently amend historical stories.

## Local development

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173/. Serve over HTTP; directly opening index.html cannot reliably fetch data files. Source links and GitHub forms work without the API key. No paid AI calls happen in the browser.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Builds only public files into `_site/`. The Pages workflow does not upload scripts, tests, or credentials. To run live research locally, set `OPENAI_API_KEY` and a GitHub token with repository issue-read access in your shell, then run `python3 scripts/generate.py`. Keep secrets outside shell history when possible. Avoid local live generation while the scheduled workflow is running; use the manual GitHub workflow for normal operation.

## Files

- `index.html`, `assets/`: responsive editorial website and original illustrations.
- `config.json`: repository identity, reviewer usernames, AI model, timezone, and editorial brief.
- `data/index.json`, `data/editions/`: ordered edition archive.
- `data/preferences.json`: automatic search guidance.
- `.github/ISSUE_TEMPLATE/review.yml`: public scoring/comment form.
- `.github/workflows/edition.yml`: daily/manual research and commit.
- `.github/workflows/pages.yml`: tests, packaging, and GitHub Pages deployment.
- `scripts/generate.py`: review ingestion, AI research, source/date checks, publication.
- `tests/test_pipeline.py`: feedback and publication validation tests.

## References

- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub Issue Forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
