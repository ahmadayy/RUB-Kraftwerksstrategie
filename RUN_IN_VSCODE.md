# How to run the model in VS Code — from scratch (Windows)

You just installed VS Code. VS Code is only a text editor — it does **not** include
Python. So the order is: install Python → open this folder in VS Code → make a clean
"virtual environment" → install the libraries → run two scripts. Total time ~15–20 min.

Follow every step in order. Commands you type are in `code boxes` — type one line, press
**Enter**, wait for it to finish, then do the next.

> You can ignore API tokens completely. The model's default data source (Energy-Charts)
> needs no token. Your tokens are already saved in `.env` as a backup; nothing else to do.

---

## STEP 1 — Install Python 3.11

1. Go to <https://www.python.org/downloads/release/python-3119/>
2. Scroll to the bottom → click **"Windows installer (64-bit)"** → it downloads an `.exe`.
3. Double-click the downloaded file to run the installer.
4. **CRITICAL:** on the first installer screen, tick the checkbox at the bottom
   **"Add python.exe to PATH"**. Then click **"Install Now"**.
   (If you forget this box, nothing below will work.)
5. Click **Close** when it finishes.

---

## STEP 2 — Add the Python extension to VS Code

1. Open VS Code.
2. On the left sidebar click the **Extensions** icon (four squares, or press
   `Ctrl+Shift+X`).
3. In the search box type **Python**.
4. Install the one published by **Microsoft** (it's the first result).

---

## STEP 3 — Open the project folder

1. In VS Code: **File → Open Folder…**
2. Navigate to and select the folder named **`RUB-Kraftwerksstrategie`**
   (the one that contains `model.py`, `config.py`, `README.md`).
3. Click **Select Folder**. If VS Code asks *"Do you trust the authors?"*, click
   **Yes, I trust the authors**.

You should now see the file list (`config.py`, `data_loader.py`, `model.py`, …) in the
left panel.

---

## STEP 4 — Open the built-in terminal

1. Top menu: **Terminal → New Terminal** (or press `` Ctrl+` `` — the key above Tab).
2. A panel opens at the bottom. The text prompt should end with the folder name,
   e.g. `...\RUB-Kraftwerksstrategie>`.

This terminal is where you'll type everything below. Keep it open.

---

## STEP 5 — Check Python is found

Type:

```
python --version
```

- If you see `Python 3.11.9` (or any `3.10`/`3.11`/`3.12`) → 
- If you see an error like *"'python' is not recognized"* → Python isn't on PATH.
  Close VS Code, redo **Step 1** (tick "Add python.exe to PATH"), restart the PC, reopen.

---

## STEP 6 — Create a virtual environment ("venv")

A venv is a private box for this project's libraries so they don't clash with anything
else. Type:

```
python -m venv venv
```

Wait ~20 seconds. A new `venv` folder appears in the file list. (You only ever do this
**once**.)

---

## STEP 7 — Activate the venv

VS Code's terminal is usually **PowerShell**. Type:

```
.\venv\Scripts\Activate.ps1
```

- **Success:** your prompt now starts with **`(venv)`**. 
- **If you get a red error about "running scripts is disabled on this system":** run this
  one line, press `Y` then Enter, then run the activate line again:

  ```
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

  *(Alternative if PowerShell keeps fighting you:* click the small **˅** arrow next to the
  `+` at the top-right of the terminal panel → choose **Command Prompt** → then type
  `venv\Scripts\activate` instead.)*

You must see `(venv)` at the start of the line before continuing. If you ever close the
terminal, re-run the activate command to get it back.

---

## STEP 8 — Point VS Code at the venv (so the editor matches the terminal)

1. Press `Ctrl+Shift+P` to open the command palette.
2. Type **Python: Select Interpreter** and click it.
3. Choose the one whose path contains **`venv`** (it usually says *"Recommended"*).

---

## STEP 9 — Install the libraries

With `(venv)` showing, type these **two** lines (one at a time):

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

This downloads PyPSA, the HiGHS solver, pandas, etc. **Takes 3–6 minutes.** Wait until
the prompt comes back. Success ends with a line like `Successfully installed pypsa-0.29.0 …`.

**If it fails with a dependency/resolver conflict** (uncommon), use the conda route in
`README.md` section 4B instead — it's the most reliable on Windows.

Quick check that the solver installed:

```
python -c "import pypsa, highspy; print('PyPSA', pypsa.__version__, '+ HiGHS OK')"
```

You should see a version line ending in `+ HiGHS OK`. If you see
`ModuleNotFoundError: highspy`, run `pip install highspy` and try again.

---

## STEP 10 — Download the authentic 2025 data (script 1 of 2)

```
python data_loader.py
```

- Fetches Germany's 2025 hourly load, generation and prices from the Energy-Charts API.
- **Takes ~2–4 minutes** (it pauses 1 sec between requests on purpose). You'll see
  progress lines like `public_power 2025-01-01 -> 2025-02-01`.
- **Needs internet.** If a corporate/university VPN blocks it, try normal Wi-Fi.
- If it errors out partway (flaky Wi-Fi), just run `python data_loader.py` again.

**Worked?** The folder `data\processed\` now has 4 `.csv` files and `data\provenance.json`
exists. The printed capacity factors should look sane (onshore wind ≈ 0.20–0.24,
offshore ≈ 0.35–0.42, solar ≈ 0.11–0.13).

---

## STEP 11 — Run the model (script 2 of 2)

```
python model.py
```

- Calibrates on 2025, then solves the four 2030 scenarios (A, B, B_low, B_high) with HiGHS.
- **Takes ~3–8 minutes** (each scenario is an 8,760-hour optimisation).
- You should see `solver status=ok, condition=optimal` **four times**, then a printed
  **comparison table (A vs B)**.

**Worked?** The `results\` folder now has the CSVs and `figures\` has the PNG charts.

---

## STEP 12 — Where your results are

```
results\comparison_table.csv      <- MAIN RESULT: Scenario A vs B, every metric + delta
results\sensitivity_table.csv     <- B_low / B / B_high
results\scenario_A_hourly.csv     <- 8760-hour dispatch, Scenario A
results\scenario_B_hourly.csv     <- 8760-hour dispatch, Scenario B
results\calibration_2025_validation.csv

figures\fig1_price_duration_curve.png  ...  figures\fig7_model_schematic.png
```

Open `results\comparison_table.csv` in Excel. These numbers are the single source of
truth for the report and presentation — don't retype them by hand anywhere.

---

## The whole thing as a checklist (after the first time)

Once installed, every future run is just:

```
.\venv\Scripts\Activate.ps1      (get (venv) back)
python model.py                  (re-run; no need to re-download data)
```

To change assumptions (2030 demand, CO₂ price, scenario GW, …) edit **`config.py`**, save,
then re-run `python model.py`.

---

## Troubleshooting (Windows / VS Code)

| What you see | Fix |
|---|---|
| `'python' is not recognized` | Python not on PATH — reinstall Python 3.11, tick **Add to PATH**, restart PC (Step 1). |
| `(venv)` never appears | Re-run `.\venv\Scripts\Activate.ps1`. If blocked, run the `Set-ExecutionPolicy` line in Step 7, or switch the terminal to **Command Prompt**. |
| "running scripts is disabled on this system" | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` → `Y` → re-activate. |
| `pip install` resolver conflict | Use the conda-forge route in `README.md` section 4B. |
| `ModuleNotFoundError: highspy` / `No solver found` | `pip install highspy`, then re-run the check in Step 9. |
| `data_loader.py` network error | Re-run it; check internet; turn off VPN. |
| `Missing input files … run data_loader.py first` | You ran `model.py` before `data_loader.py`. Do Step 10 first. |
| Very slow / low memory | Close other apps; each scenario is an 8,760-hour problem — a few minutes is normal. |

---

*If anything prints an error you don't recognise, copy the whole red message and send it
to me — I'll tell you exactly what to do.*
