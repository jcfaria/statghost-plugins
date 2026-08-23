import * as vscode from 'vscode';
import {
  ACTION_KEYS,
  GRID_CAP,
  gridPlan,
  keyFromCommandId,
  parseShow,
  type ActionKey,
  type GridLabelMode,
} from './chromeContract';
import { ACTION_HINTS, ICON_FILES } from './iconMap';
import { getChromeShow, getGridLabel, getIconsFg, getIconsSize } from './prefs';
import { gridMetrics, metricsCssVars, type IconSizePx } from './gridMetrics';
import { mapVscodeVars, themeCssBlock, themeFromCssVars } from './themeBridge';
import type { ArmState } from './bridge';

export class AnalyticPanelProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'statghost.analyticPanel';

  private view?: vscode.WebviewView;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly armState: ArmState,
  ) {}

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, 'media')],
    };

    webviewView.webview.onDidReceiveMessage((msg: { type?: string; key?: string }) => {
      if (msg.type === 'action' && msg.key) {
        void vscode.commands.executeCommand(`statghost.${msg.key}`);
      }
      if (msg.type === 'theme') {
        this.postThemeUpdate();
      }
    });

    webviewView.onDidChangeVisibility(() => {
      if (webviewView.visible) {
        this.refresh();
      }
    });

    this.refresh();
  }

  refresh(): void {
    if (!this.view) {
      return;
    }
    const show = getChromeShow();
    const gridLabel = getGridLabel();
    const iconsFg = getIconsFg();
    const iconsSize = getIconsSize();
    this.view.webview.html = this.buildHtml(show, gridLabel, iconsFg, iconsSize);
  }

  postThemeUpdate(): void {
    // Webview recomputes theme client-side; host can push config changes.
    this.refresh();
  }

  private iconUri(webview: vscode.Webview, key: ActionKey, size: IconSizePx): string {
    let file = ICON_FILES[key];
    if (key === 'arm') {
      file = this.armState.isArmed() ? 'armed.png' : 'idle.png';
    }
    const onDisk = vscode.Uri.joinPath(
      this.extensionUri, 'media', 'res', `${size}px`, file,
    );
    return webview.asWebviewUri(onDisk).toString();
  }

  private buildHtml(
    show: ActionKey[],
    gridLabel: GridLabelMode,
    iconsFg: string,
    iconsSize: IconSizePx,
  ): string {
    const webview = this.view!.webview;
    const cspSource = webview.cspSource;
    const plan = gridPlan(show);
    const nonce = String(Date.now());
    const metrics = gridMetrics(iconsSize);
    const metricsVars = metricsCssVars(metrics);

    const cells: string[] = [];
    for (const entry of plan) {
      if (entry[0] === 'hdr') {
        cells.push(`<div class="band">${escapeHtml(entry[1].toUpperCase())}</div>`);
      } else {
        const keys = entry[1];
        cells.push('<div class="row">');
        for (const key of keys) {
          const cap = key === 'arm'
            ? (this.armState.isArmed() ? 'Armed' : 'Idle')
            : GRID_CAP[key];
          const hint = ACTION_HINTS[key] ?? cap;
          const icon = this.iconUri(webview, key, iconsSize);
          const labelClass = gridLabel === 'icon' ? 'label hide' : 'label below';
          cells.push(`
            <button class="cell mode-${gridLabel}" data-key="${key}" title="${escapeAttr(hint)}">
              <span class="glyph" style="--sg-mask:url('${icon}')"></span>
              <span class="${labelClass}">${escapeHtml(cap)}</span>
            </button>`);
        }
        // pad row to 3 cols for equal width
        for (let i = keys.length; i < 3; i++) {
          cells.push('<div class="cell pad"></div>');
        }
        cells.push('</div>');
      }
    }

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource} data:; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    :root {
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background, var(--vscode-editor-background));
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      ${metricsVars};
    }
  </style>
  <style id="sg-theme"></style>
  <style>
    body { margin: 0; padding: var(--sg-body-pad-v) var(--sg-body-pad-h) 8px; box-sizing: border-box; }
    .band {
      margin: var(--sg-band-mt) 0 2px;
      padding: var(--sg-band-pad-v) var(--sg-band-pad-h);
      font-weight: 700;
      font-size: var(--sg-band-font);
      letter-spacing: 0.04em;
      line-height: 1.1;
      background: var(--sg-hdr-band);
      color: var(--sg-hdr-fg);
      border-radius: 2px;
    }
    .band:first-child { margin-top: 0; }
    .row {
      display: grid;
      grid-template-columns: repeat(3, minmax(var(--sg-cell-min-w), 1fr));
      gap: var(--sg-row-gap);
      margin-bottom: var(--sg-row-gap);
    }
    .cell {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
      min-width: 0;
      min-height: var(--sg-cell-min-below);
      padding: var(--sg-cell-pad-v) var(--sg-cell-pad-h);
      border: 1px solid var(--vscode-panel-border, transparent);
      border-radius: 2px;
      background: transparent;
      color: var(--sg-cell-fg);
      cursor: pointer;
      font: inherit;
      font-weight: 400;
      box-sizing: border-box;
    }
    .cell.pad { visibility: hidden; pointer-events: none; border: none; background: transparent; min-height: 0; padding: 0; }
    .cell:hover {
      background: var(--vscode-toolbar-hoverBackground, transparent);
      border-color: var(--vscode-focusBorder, var(--vscode-panel-border, transparent));
    }
    .cell:focus-visible {
      outline: 1px solid var(--vscode-focusBorder);
      outline-offset: -1px;
    }
    .cell.mode-icon { min-height: var(--sg-cell-min-icon); }
    .glyph {
      width: var(--sg-glyph);
      height: var(--sg-glyph);
      flex: 0 0 auto;
      background-color: var(--sg-cell-fg);
      -webkit-mask-image: var(--sg-mask);
      mask-image: var(--sg-mask);
      -webkit-mask-size: contain;
      mask-size: contain;
      -webkit-mask-repeat: no-repeat;
      mask-repeat: no-repeat;
      -webkit-mask-position: center;
    }
    .label {
      font-size: var(--sg-label);
      line-height: 1.1;
      text-align: center;
      font-weight: 400;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .label.hide { display: none; }
    .label.below { margin-top: var(--sg-label-gap); }
    .foot {
      margin-top: 6px;
      padding-top: 4px;
      border-top: 1px solid var(--vscode-panel-border, #444);
      font-size: 9px;
      opacity: 0.75;
    }
  </style>
</head>
<body>
  ${cells.join('\n')}
  <div class="foot">STATghost · ${show.length}/${ACTION_KEYS.length} actions · ${gridLabel} · ${iconsSize}px</div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const iconsFg = ${JSON.stringify(iconsFg)};

    function parseRgb(css, fb) {
      if (!css) return fb;
      const s = css.trim();
      let m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(s);
      if (m) {
        let h = m[1];
        if (h.length === 3) h = h.split('').map(c => c + c).join('');
        return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
      }
      m = /^rgba?\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)/i.exec(s);
      if (m) return [+m[1], +m[2], +m[3]];
      return fb;
    }
    function blend(a,b,t){return a.map((v,i)=>Math.round(v+(b[i]-v)*t));}
    function relLuma(rgb){return (0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2])/255;}
    function contrast(fg,bg){
      const l1=relLuma(fg), l2=relLuma(bg), L=Math.max(l1,l2), D=Math.min(l1,l2);
      return (L+0.05)/(D+0.05);
    }
    function hdrBandBg(back, face, border) {
      const luma = relLuma(back);
      if (luma < 0.45) {
        const lift = (face.join()!==back.join()) ? face : [0x52,0x52,0x56];
        return blend(back, lift, 0.58);
      }
      const shade = (border.join()!==back.join()) ? border : [0xc8,0xc8,0xcc];
      return blend(back, shade, 0.32);
    }
    function pickFg(mode, buttonFont, bg) {
      const WHITE = [0xc4,0xc4,0xc4], GRAY = [0x8a,0x8a,0x8a], GRAPHITE = [0x3a,0x3a,0x3a];
      if (mode==='light' || mode==='white') return WHITE;
      if (mode==='dark' || mode==='graphite') return GRAPHITE;
      if (mode==='gray' || mode==='grey') return GRAY;
      if (mode==='theme') return buttonFont;
      const cands = [WHITE, GRAY, GRAPHITE, buttonFont];
      let best=null, br=0;
      for (const c of cands) {
        const r = contrast(c,bg);
        if (r>=3 && r>br) { best=c; br=r; }
      }
      if (best) return best;
      return relLuma(bg)<0.45 ? WHITE : GRAPHITE;
    }
    function cssRgb(rgb){return 'rgb('+rgb.join(',')+')';}

    function applyTheme() {
      const cs = getComputedStyle(document.body);
      const tabBg = parseRgb(cs.getPropertyValue('--vscode-tab-activeBackground') ||
        cs.getPropertyValue('--vscode-sideBar-background') ||
        cs.getPropertyValue('--vscode-editor-background'), [42,42,42]);
      const buttonBg = parseRgb(cs.getPropertyValue('--vscode-button-secondaryBackground') ||
        cs.getPropertyValue('--vscode-tab-activeBackground'), tabBg);
      const tabFont = parseRgb(cs.getPropertyValue('--vscode-tab-activeForeground') ||
        cs.getPropertyValue('--vscode-foreground'), [144,144,144]);
      const buttonFont = parseRgb(cs.getPropertyValue('--vscode-button-secondaryForeground') ||
        cs.getPropertyValue('--vscode-foreground'), tabFont);
      const border = parseRgb(cs.getPropertyValue('--vscode-panel-border'), [96,96,96]);
      const hdr = hdrBandBg(tabBg, buttonBg, border);
      const cellFg = pickFg(iconsFg, buttonFont, tabBg);
      document.getElementById('sg-theme').textContent =
        ':root{--sg-hdr-band:'+cssRgb(hdr)+';--sg-hdr-fg:'+cssRgb(tabFont)+
        ';--sg-cell-fg:'+cssRgb(cellFg)+';}';
    }
    applyTheme();

    document.querySelectorAll('button.cell').forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.getAttribute('data-key');
        if (key) vscode.postMessage({ type: 'action', key });
      });
    });
  </script>
</body>
</html>`;
  }
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeAttr(s: string): string {
  return escapeHtml(s).replace(/"/g, '&quot;');
}

/** Push computed theme CSS into an open panel (called from extension on config change). */
export function injectThemeScript(webview: vscode.Webview, iconsFg: string): string {
  const vars = mapVscodeVars({});
  const snap = themeFromCssVars(vars, iconsFg);
  return `:root { ${themeCssBlock(snap).trim()} }`;
}

export function keysForCommandPalette(): ActionKey[] {
  return parseShow('');
}

export { keyFromCommandId };
