w_todo — working docs (SAP / CPR for the CudaText host chrome)
===============================================================
Updated: 2026-08-22 (lives under plugins/cudatext/ — host-specific)
Reading preference: **Portuguese (w_pt/br)**. Always keep EN twins.

Layout:
  w_todo/
    README.txt          ← this file
    w_en/               ← English
    w_pt/br/            ← Portuguese Brazil
    icons/              ← Tinn-R_D 16px extracts + generated 24/32 (lab stash)
    tools/              ← extract / upsample recipes

Numbering (elaboration order — same in every language pack):
  01_sap_workbar.txt    2026-08-16  SAP Tinn-R_D workbar → plugin chrome
                                    (D29 companion; VP-WB-*)
  02_cpr_workbar.txt    2026-08-16  CPR WORKBAR (VP-WB-1 GO; WB-2 stash;
                                    WB-3 Insert; WB-4 Rnoweb RECORD;
                                    WB-5 R-control Inspect/Clear GO)
  03_sap_chrome.txt     2026-08-22  SAP Chrome pattern (multi-editor;
                                    one contract / three surfaces)
  04_cpr_chrome.txt     2026-08-22  CPR CHROME (VP-CH-1..7; shared extract
                                    RECORD until second host GO)

Canonical EN (all hosts): `shared/CHROME.md`

STATghost product packs (16/17 EDITOR-BRIDGE, D29) stay in the sibling
repo `jcfaria/statghost` `w_todo/`. This companion folder owns **plugin
chrome** only — do not steal Explorer / GEOM / Console widgets.

Norm: full EN ↔ PT mirror; next free NN_; no files loose under w_todo/
root except this README + tools/ + icons/.

Skill: `.cursor/skills/sap-cpr-workbar/SKILL.md`
Reference (read-only): `jcfaria/Tinn-R_D` `TBRMain` (Toolbar2000).
Head noted 2026-08-16: Tinn-R_D `work` `6126062`.
