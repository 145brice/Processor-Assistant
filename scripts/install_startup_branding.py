"""Add a startup screen to Streamlit's served shell at image build time."""
from pathlib import Path
import streamlit


BRANDING = '''
<div id="pa-startup" role="status" aria-live="polite" style="position:fixed;inset:0;
z-index:999999;background:#f8fafc;color:#17345a;display:grid;place-content:center;
text-align:center;font-family:system-ui,sans-serif">
<div style="font-size:28px;font-weight:800">Processor Assistant</div>
<p style="font-size:16px;color:#64748b">Preparing your workspace...</p></div>
<script>
(() => {
  const ready = () => {
    if (!document.getElementById('pa-workspace-ready')) return;
    document.getElementById('pa-startup')?.remove(); observer.disconnect();
  };
  const observer = new MutationObserver(ready);
  observer.observe(document.body, {childList:true, subtree:true}); ready();
})();
</script>
'''


def install():
    path = Path(streamlit.__file__).parent / "static" / "index.html"
    shell = path.read_text(encoding="utf-8")
    if 'id="pa-startup"' not in shell:
        path.write_text(shell.replace("</body>", BRANDING + "</body>"), encoding="utf-8")


if __name__ == "__main__":
    install()
