
// Render diff using Diff2Html
document.addEventListener('DOMContentLoaded', function() {
    const diffText = document.getElementById('diff-text').textContent;
    const configuration = {
        drawFileList: false,
        matching: 'lines',
        highlight: true,
        outputFormat: 'side-by-side',
    };
    const diff2htmlUi = new Diff2HtmlUI(document.getElementById('diff-container'), diffText, configuration);
    diff2htmlUi.draw();
    diff2htmlUi.highlightCode();
});
