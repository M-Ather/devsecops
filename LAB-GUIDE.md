# DevSecOps Workshop: Student Lab Guide

> **Safety:** This app is intentionally vulnerable. Use it only for this workshop. Never deploy it. Every key in this repo is fake.

**What you will build:** A GitHub Actions pipeline that catches security problems automatically.

```
commit > secrets scan > code scan (SAST) > dependency scan (SCA) > container scan > merge gate
```

**The pattern in every lab: break it, detect it, fix it.**
After every `git push`, open your fork's **Actions** tab in the browser to see the result.

You need: a Linux terminal (Kali, Ubuntu or WSL), `git`, a GitHub account and a browser.
You do not need Docker, Python or any scanner on your laptop. All scans run on GitHub.

----------------------------------------------------------------------------------------

## Step 0: One-time setup (do this BEFORE the workshop or before workshop labs)

**0.1 Check git**

```bash
git --version
```

If missing: `sudo apt-get install -y git`

**0.2 Set your identity**

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**0.3 Create a personal access token. Tick BOTH 'repo' and 'workflow'.**

GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic) > Generate new token (classic).

- Expiration: 7 days
- Scopes: repo and workflow
- Copy the token now. It is your password for 'git push'.

> **Most common mistake:** forgetting the 'workflow' box. Pushes that add a file under '.github/workflows/' are then rejected:
> 'refusing to allow a Personal Access Token to create or update workflow ... without workflow scope'.
> Fix: edit the token, tick `workflow`, save, run `git credential-cache exit`, then push again.

**0.4 Remember the token for 2 hours**

```bash
git config --global credential.helper 'cache --timeout=7200'
```

-----------------------------------------------------------------------------------------------

## Lab 0: Fork, clone, baseline CI (10 min)

1. In the browser open the workshop repo (https://github.com/M-Ather/devsecops) and click Fork, then Create fork.
2. In your fork, open the Actions tab. If you see a green button, click "I understand my workflows, go ahead and enable them".
3. Clone your fork (use your own username):

```bash
git clone https://github.com/YOUR-USERNAME/devsecops.git
cd devsecops
```

4. Trigger the baseline pipeline:

```bash
echo "" >> README.md
git add -A
git commit -m "lab0: trigger CI"
git push
```

Username = your GitHub username. Password = your **token**.

5. Open **Actions**. The `CI` workflow should turn green (about 30 seconds).

> **No run appeared?** A brand-new fork sometimes ignores the first push. Push an empty commit:
> `git commit --allow-empty -m "retrigger" && git push`

**Done when:** `CI` has a green tick.

---

## Lab 1: Secrets scanning (25 min)

**Idea:** a secret committed to git stays in history forever, even after you delete it from the code.

**Break:** find the hardcoded key.

```bash
grep -n "INTERNAL_API_KEY" app/app.py
```

**Detect:** add the Gitleaks workflow.

```bash
mkdir -p .github/workflows
cp solutions/lab1-secrets.yml .github/workflows/secrets.yml
git add -A
git commit -m "lab1: add gitleaks"
git push
```

Open **Actions > Lab1 - Secrets Scan** (red). Click the job `gitleaks`, then expand the step **Scan for secrets**. You will see:

```
RuleID:      generic-api-key
File:        app/app.py
Line:        19
Fingerprint: <commit>:app/app.py:generic-api-key:19
```

**Fix the code:** read the key from the environment instead.

```bash
sed -i 's|^INTERNAL_API_KEY = .*|INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "")|' app/app.py
sed -i 's/^import sqlite3/import os\nimport sqlite3/' app/app.py
git add -A
git commit -m "lab1: remove hardcoded key"
git push
```

It is **still red**. Why? The key is still inside an old commit in your git history.

> **Real-life rule:** if a secret leaks, **rotate or revoke it first**. Cleaning code or history is only housekeeping.
> (Your instructor will demo how history can be rewritten. You will not do that today.)

**Make it green (allowed only because this key is fake):** tell Gitleaks to ignore that one finding.

Copy the **whole** `Fingerprint:` value from the log. It has 4 parts joined by colons: `commit:file:rule:line`.

```bash
echo "PASTE-THE-WHOLE-FINGERPRINT-LINE-HERE" > .gitleaksignore
git add -A
git commit -m "lab1: ignore fake key"
git push
```

Use a single `>` so the file is overwritten with exactly one line.

> **Still red?** Look at the Gitleaks log for `Invalid .gitleaksignore entry`. That means your line is wrong: you pasted only the commit hash, or the placeholder text. Quick fix: `cp solutions/gitleaksignore .gitleaksignore`, then commit and push.

**Done when:** `Lab1 - Secrets Scan` is green.

---

## Lab 2: SAST, code scanning (30 min)

**Idea:** SAST reads your source code and flags dangerous patterns before the app ever runs.

**Break:** `app/app.py` has three real bugs: SQL injection in `/search`, XSS in `/hello`, and `debug=True`.

**Detect:**

```bash
cp solutions/lab2-sast.yml .github/workflows/sast.yml
git add -A
git commit -m "lab2: add semgrep"
git push
```

Open **Actions > Lab2 - SAST** (red). Click the job `semgrep` and expand the step **Run Semgrep**. You should see about **6 findings for 3 bugs** (one bug can trigger several rules):

| Line | Bug | Example rule |
|---|---|---|
| 51 | SQL injection | `tainted-sql-string` |
| 60 | Cross-site scripting | `directly-returned-format-string`, `raw-html-concat` |
| 65 | Debug mode and exposed host | `debug-enabled`, `avoid_app_run_with_bad_host` |

**Fix all three:**

```bash
python3 - <<'EOF'
p = "app/app.py"
s = open(p).read()
s = s.replace('''    query = "SELECT title, body FROM notes WHERE title LIKE '%" + term + "%'"
    rows = _conn.execute(query).fetchall()''',
'''    rows = _conn.execute("SELECT title, body FROM notes WHERE title LIKE ?", (f"%{term}%",)).fetchall()''')
s = s.replace('return "<h1>Hello " + name + "</h1>"', 'return render_template_string("<h1>Hello {{ name }}</h1>", name=name)')
s = s.replace("from flask import Flask, request", "from flask import Flask, request, render_template_string")
s = s.replace('app.run(host="0.0.0.0", port=5000, debug=True)', 'app.run(host="127.0.0.1", port=5000, debug=False)')
open(p, "w").write(s)
EOF
git diff --stat
git add -A
git commit -m "lab2: fix SQLi, XSS, debug"
git push
```

What each fix does: a parameterized query keeps user input as data, never as SQL; a template auto-escapes user input in HTML; `debug=False` removes the debugger; `127.0.0.1` stops the server listening on every network interface.

**Done when:** `Lab2 - SAST` **and** `CI` are both green.

---

## Lab 3: Dependency scanning, SCA (25 min)

**Idea:** most of your app is other people's code. SCA checks those libraries against known-vulnerability databases.

**Break:** `requirements.txt` pins old versions (for example `requests==2.19.1`, `PyYAML==5.3.1`).

**Detect + automate:**

```bash
cp solutions/lab3-sca.yml .github/workflows/sca.yml
cp solutions/dependabot.yml .github/dependabot.yml
git add -A
git commit -m "lab3: add pip-audit and dependabot"
git push
```

Open **Actions > Lab3 - Dependency Scan** (red). Expand the step **Audit dependencies**. You will see a table with the package, the vulnerable version, the advisory ID and the **Fix Versions**.

Things to notice:
- The count is large (around 71 rows) because some IDs appear twice. Unique advisories are fewer.
- `idna` and `urllib3` are **not** in your `requirements.txt`. They came in through `requests` (a **transitive dependency**) and are still your problem.
- Pick one ID (for example `PYSEC-2021-142`) and read it at https://osv.dev.

**Dependabot (browser):** Settings > Code security > enable **Dependabot alerts**. Pull requests from Dependabot can take minutes to hours to appear, so check the **Security** tab and **Pull requests** later.

**Fix:** upgrade to current versions.

```bash
cat > requirements.txt <<'EOF'
Flask>=3.1
requests>=2.32
PyYAML>=6.0.1
EOF
git add -A
git commit -m "lab3: upgrade dependencies"
git push
```

**Done when:** `Lab3 - Dependency Scan` **and** `CI` (the tests) are green.

---

## Lab 4: Container security (20 min)

**Mini Docker primer:** a container image is your app plus an operating-system layer. If that OS layer is old, you ship its vulnerabilities. A container that runs as `root` is also riskier if an attacker gets in.

**Break:** open the `Dockerfile`. It uses an old base image (`python:3.9-bullseye`) and runs as root.

**Detect:**

```bash
cp solutions/lab4-container.yml .github/workflows/container.yml
git add -A
git commit -m "lab4: add trivy"
git push
```

Open **Actions > Lab4 - Container Scan**. Two jobs run side by side, and both should fail:

- `dockerfile-scan`: `DS-0002 (HIGH)`: no non-root `USER` in the Dockerfile.
- `image-scan`: roughly 180 CRITICAL vulnerabilities in the old Debian 11 layer, plus the warning *"This OS version is no longer supported"*.

> The image-scan log is very long. Do not read the whole table. Read the **Report Summary** and the line `Total: N (CRITICAL: N)`.

**Fix:** a current slim base image and a non-root user.

```bash
sed -i 's/^FROM .*/FROM python:3.12-slim/' Dockerfile
sed -i 's|^CMD|RUN useradd -m appuser\nUSER appuser\nCMD|' Dockerfile
cat Dockerfile
git add -A
git commit -m "lab4: slim base, non-root user"
git push
```

`cat Dockerfile` should show `FROM python:3.12-slim`, then `RUN useradd -m appuser` and `USER appuser` just before `CMD`.

**Done when:** `dockerfile-scan`, `image-scan` and `CI` are all green.

---

## Wrap-up: the security gate (10 min)

Scans that nobody has to remember to run are good. Scans that **block a bad merge** are better.

### Part 1: Protect `main` (browser, on YOUR fork)

1. Your fork > **Settings > Branches > Add classic branch protection rule**.
2. Branch name pattern: `main`
3. Tick **Require a pull request before merging** (no approvals needed).
4. Tick **Require status checks to pass before merging**. Search and add all six, one at a time:
   `test`, `gitleaks`, `semgrep`, `pip-audit`, `dockerfile-scan`, `image-scan`
5. Tick **Do not allow bypassing the above settings**.
6. Click **Create**.

### Part 2: Try pushing straight to `main`

```bash
echo "x" >> README.md
git add -A
git commit -m "direct push test"
git push
```

It is rejected: `GH006: Protected branch update failed ... Changes must be made through a pull request`. Undo your local commit:

```bash
git reset --hard origin/main
```

### Part 3: Open a PR that leaks a secret

```bash
git checkout -b test-leak
echo "API_TOKEN = \"$(openssl rand -hex 32)\"" >> app/app.py
git add -A
git commit -m "add token"
git push -u origin test-leak
```

Now open the pull request. **This is where most people go wrong:**

> **STOP and check the base repository.** On a fork, GitHub's "Compare & pull request" button and the link printed by `git push` default to the **instructor's repository**, not yours.
> Go to **your fork's** Pull requests tab > **New pull request**, then check that **both** the *base repository* and the *head repository* dropdowns say `YOUR-USERNAME/devsecops`, with base `main` and compare `test-leak`. Only then click **Create pull request**.
> Tip: the right page shows only **1 commit, 1 file**. If it shows 15 commits, you are on the wrong repository.

**What you should see:**
- Six required checks run.
- `gitleaks` fails, the other five pass.
- The **Merge pull request** button is greyed out ("Merging is blocked").

> If `gitleaks` passes (rare, the random value had low entropy), run the `echo` line again with a new value, commit and push.

**Cleanup:** close the PR without merging, then:

```bash
git checkout main
git branch -D test-leak
git push origin --delete test-leak
```

You now have a full DevSecOps pipeline: **commit > secrets scan > SAST > SCA > container scan > merge gate.**

**Take-home ideas:** DAST with OWASP ZAP, infrastructure-as-code scanning, SBOM generation, signing container images.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Push rejected: "without `workflow` scope" | Token is missing the `workflow` scope. Tick it, then `git credential-cache exit` and push again |
| Asked for a password on every push | Re-run step 0.4 |
| No run after the first push | Enable Actions on your fork, then push an empty commit (Lab 0) |
| Workflow run says "awaiting approval" | You are on the instructor's repo. Open your PR on **your own fork** (Wrap-up, Part 3) |
| `.gitleaksignore` does not work | Log shows `Invalid .gitleaksignore entry`. Paste the **whole** fingerprint, or `cp solutions/gitleaksignore .gitleaksignore` |
| Wrong or extra file committed | `git rm FILENAME`, commit, push |
| `git remote -v` shows the instructor's repo | You cloned the wrong repo. Clone **your fork** |
| A scan job is red after your fix | Open the job log and read the first error. Compare with the matching file in `solutions/` |
| `Could not find a version that satisfies the requirement` | Check you typed `requirements.txt` exactly as shown in Lab 3 |
| Trivy `TOOMANYREQUESTS` | Click **Re-run jobs** |
