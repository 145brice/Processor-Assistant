# Parked

Work that was built or planned, then taken out of the live app on the owner's request. Nothing in this
folder is imported, bundled, shown to users, or run by the tests. It is saved here so it can be brought
back later. (It also stays in git history.)

## more-tools/

Removed on 2026-11-19 because these tools never worked in the current Streamlit app.

| Tool | Why it never worked in the current app | What the rebuilt version here does |
|---|---|---|
| Income Verifier | Reads `st.session_state["scan_results"]`, which is set to `None` at start-up and never filled | Uses the data the scanner saved on the chosen loan's documents |
| Auto Data Entry | Same | Same |
| Fraud Detector | Ignores its three checkboxes, and its sample deposit is exactly $5,000 while the module only flags deposits over $5,000 | Takes the figures the module really checks and checks a loan's document names |
| Underwriting Tracker | Only marks a condition cleared when the condition carries a submitted date, which the page never sends | A condition the loan marks Cleared counts as cleared; related documents are listed |
| Team | Works by writing files into a folder on each person's own computer or network drive, which a web server cannot reach | Not built. See below |

Files:

- `income_verifier_and_auto_data_entry.py`, `fraud_detector_and_underwriting_tracker.py`: the backend handlers
- `parked_tests_*.py`: their tests (named so pytest does not collect them)
- `web-tool-definitions.ts.txt`: their form definitions for the web app

### Bring one back

1. Copy the handler code into `backend/pa_api/tools/advanced.py` or `pipeline.py` (the imports are at the top of
   each parked file), or save the file next to them and add it to `load_tools()` in
   `backend/pa_api/tools/__init__.py`.
2. Paste its entry from `web-tool-definitions.ts.txt` into `TOOLS` in `web/src/lib/tools.ts`, and import its icon.
3. Add it back to the sidebar in `web/src/lib/nav.ts`.
4. Move its tests into `backend/tests/` (copy the helpers named at the top of each parked tests file) and add
   its row back to the tools table in `docs/nextjs-rebuild/API_CONTRACT.md`.
5. Run the full tests.

### Team

Nothing was built. The current page asks each person for an "inbox folder" path on their computer or network
share and writes shared loans there. A web service cannot reach those folders. A web version would share loans
between **accounts** (adding a teammate's account to a loan's `shared_with_user_keys`, which the pipeline's
visibility rules already read), with an accept or decline step. That puts one user's borrower data in front of
another, so decide the rules first: who may share, whether the teammate must accept, whether sharing can be
undone, and whether it is logged.
