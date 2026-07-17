/*
 * slac-theme-config.js
 * Reveal.js initialisation and chrome behaviour for SLAC presentations.
 * Include this script AFTER reveal.js and its plugins.
 */

Reveal.initialize(Object.assign(
  {
    hash: true,
    slideNumber: false,
    controls: false,
    transition: 'slide',
  },
  window.__DECK_REVEAL_CONFIG__ || {},
  { plugins: [ RevealNotes ] },
));

// ── Footer & title-logo chrome ─────────────────────────────────────────────
const footer          = document.getElementById('slac-footer');
const titleLogo       = document.getElementById('title-logo');
const stanfordDoeLogo = document.getElementById('title-stanford-doe');
const slideNumEl      = document.getElementById('footer-slide-num');

function updateChrome() {
  const isTitleSlide = Reveal.getCurrentSlide()?.classList.contains('title-slide');
  footer.classList.toggle('hidden', isTitleSlide);
  titleLogo.style.opacity       = isTitleSlide ? '1' : '0';
  titleLogo.style.pointerEvents = 'none';
  stanfordDoeLogo.style.opacity       = isTitleSlide ? '1' : '0';
  stanfordDoeLogo.style.pointerEvents = 'none';
  slideNumEl.textContent = Reveal.getIndices().h + 1;
}
Reveal.on('slidechanged', updateChrome);
Reveal.on('ready', updateChrome);

// ── Footnote overlay ───────────────────────────────────────────────────────
// Reads .slide-footnote content from the current slide and displays it
// in the fixed #footnote-overlay element.
const footnoteOverlay = document.getElementById('footnote-overlay');

function updateFootnote() {
  const fn = Reveal.getCurrentSlide()?.querySelector('.slide-footnote');
  footnoteOverlay.innerHTML = fn ? fn.innerHTML : '';
}
Reveal.on('slidechanged', updateFootnote);
Reveal.on('ready', updateFootnote);

// Open footnote links in a new tab (prevent Reveal.js capturing the click)
footnoteOverlay.addEventListener('click', function(e) {
  const link = e.target.closest('a');
  if (link && link.href) {
    e.stopImmediatePropagation();
    e.preventDefault();
    window.open(link.href, '_blank');
  }
}, true);
