document.addEventListener('DOMContentLoaded', function () {
  // Initialize mermaid and convert fenced mermaid codeblocks
  if (window.mermaid) {
    try {
      mermaid.initialize({ startOnLoad: false });
      // Replace <pre><code class="language-mermaid"> with <div class="mermaid"> so mermaid can render
      document.querySelectorAll('pre > code[class*="language-mermaid"]').forEach(function (code) {
        var pre = code.parentElement;
        var parent = pre.parentElement;
        var container = document.createElement('div');
        container.className = 'mermaid';
        container.textContent = code.textContent;
        parent.replaceChild(container, pre);
      });
      // Render all mermaid containers
      mermaid.init(undefined, document.querySelectorAll('.mermaid'));
    } catch (e) { console.error('mermaid init error', e); }
  }

  // Add copy buttons to all code blocks
  document.querySelectorAll('pre > code').forEach(function (code) {
    var pre = code.parentElement;
    // Avoid adding button to mermaid pre/code (they may have been replaced earlier)
    if (pre.querySelector('.copy-code-button')) return;
    var button = document.createElement('button');
    button.className = 'copy-code-button';
    button.type = 'button';
    button.innerText = 'Copy';
    button.addEventListener('click', function () {
      navigator.clipboard.writeText(code.textContent).then(function () {
        var old = button.innerText;
        button.innerText = 'Copied';
        setTimeout(function () { button.innerText = old; }, 1500);
      }, function (err) {
        console.error('Copy failed', err);
        button.innerText = 'Error';
        setTimeout(function () { button.innerText = 'Copy'; }, 1500);
      });
    });
    pre.style.position = 'relative';
    pre.appendChild(button);
  });
});
