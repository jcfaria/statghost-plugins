# Aprovações Cursor / Smart Mode

Se o agente **parar** pedindo confirmação e você **não vê** os cartões de aprovação:

1. **Cursor Settings → Features** — confira que **approval cards** / prompts de terminal estão habilitados (não ocultos).
2. **Smart Mode** — para este workspace, desative bloqueios que exigem aprovação em comandos de desenvolvimento (`npm`, `powershell`, instalar extensão), ou aprove a sessão como “autonomous GO”.
3. **Último recurso manual** (uma vez): na raiz do repo,
   ```powershell
   powershell -File plugins\vscode\restart_lab.ps1
   ```
   Isso compila, roda testes, gera o VSIX e instala via `cursor --install-extension` (ou `code` se existir).

O agente deve fazer isso sozinho; estes passos são só se a UI de aprovação falhar.
