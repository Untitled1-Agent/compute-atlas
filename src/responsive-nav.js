/* Navigation must be closed and out of the focus order at mobile breakpoints.
   This module deliberately owns no research or publication state. */
(() => {
  'use strict';
  const sidebar = document.getElementById('sidebar');
  const trigger = document.querySelector('.mobile-menu');
  const shell = document.querySelector('.app-shell');
  if (!sidebar || !trigger || !shell) return;
  const mobile = matchMedia('(max-width: 640px)');
  const backdrop = document.createElement('button');
  backdrop.className = 'nav-backdrop';
  backdrop.type = 'button';
  backdrop.hidden = true;
  backdrop.tabIndex = -1;
  backdrop.setAttribute('aria-label', 'Close navigation');
  document.body.append(backdrop);
  const close = document.createElement('button');
  close.className = 'icon-button nav-close';
  close.type = 'button';
  close.setAttribute('aria-label', 'Close navigation');
  close.textContent = '✕';
  sidebar.prepend(close);
  trigger.setAttribute('aria-controls', 'sidebar');
  let wasOpen = false;
  function sync() {
    const open = mobile.matches && sidebar.classList.contains('open');
    sidebar.inert = mobile.matches && !open;
    sidebar.setAttribute('aria-hidden', String(sidebar.inert));
    trigger.setAttribute('aria-expanded', String(open));
    trigger.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    backdrop.hidden = !open;
    shell.inert = open;
    document.body.classList.toggle('nav-open', open);
    if (open && !wasOpen) close.focus();
    if (!open && wasOpen && mobile.matches) trigger.focus();
    wasOpen = open;
  }
  function dismiss() { sidebar.classList.remove('open'); sync(); }
  close.addEventListener('click', dismiss);
  backdrop.addEventListener('click', dismiss);
  new MutationObserver(sync).observe(sidebar, { attributes: true, attributeFilter: ['class'] });
  mobile.addEventListener('change', () => { sidebar.classList.remove('open'); sync(); });
  document.addEventListener('keydown', event => {
    if (!mobile.matches || !sidebar.classList.contains('open')) return;
    if (event.key === 'Escape') { event.preventDefault(); dismiss(); }
    if (event.key !== 'Tab') return;
    const controls = [...sidebar.querySelectorAll('button:not([disabled]),a[href],input,[tabindex="0"]')]
      .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  });
  // Actions such as Search can open a dialog without navigating to another page.
  sidebar.addEventListener('click', event => {
    if (event.target.closest('[data-action],.brand')) dismiss();
  });
  sync();
})();
