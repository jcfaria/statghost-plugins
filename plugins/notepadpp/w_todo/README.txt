w_todo — Notepad++ host (SAP / CPR)
====================================
Updated: 2026-08-23
Status: VP-NPP-2/3/6 CODE landed; owner TF pending (grid + clipboard with SG Armed)

Reading preference: Portuguese (w_pt/br). Always keep EN twins.

Layout:
  w_todo/
    README.txt          ← this file
    w_en/               ← English
    w_pt/br/            ← Portuguese Brazil

Numbering (host-local — not a continuation of cudatext 03/04):
  01_sap_notepadpp.txt  SAP — N++ host scope, surfaces, language choice
  02_cpr_notepadpp.txt  CPR — VP-NPP-* milestones

Canonical chrome (all hosts): shared/CHROME.md
Strategic index: shared/NOTEPADPP.md

CODE:
  plugins/notepadpp/statghost-npp/   ← C++ Unicode DLL (VP-NPP-1)
  plugins/notepadpp/build_lab.ps1    ← build
  plugins/notepadpp/install_lab.ps1  ← deploy
  plugins/notepadpp/restart_lab.ps1  ← restart host

Norm: full EN ↔ PT mirror; no loose files under w_todo/ root except README.