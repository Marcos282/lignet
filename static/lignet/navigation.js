(() => {
  const header = document.querySelector('[data-site-navigation]');
  if (!header) return;
  const nav = header.querySelector('.site-nav');
  const toggle = header.querySelector('.site-toggle');
  const close = header.querySelector('.site-close');
  const backdrop = header.querySelector('.site-backdrop');
  const tools = header.querySelector('.site-tools > button');
  const mobile = matchMedia('(max-width: 900px)');
  let savedScroll = 0;
  let previousBodyStyle;
  let inertElements = [];
  const expanded = (button, value) => {
    button.setAttribute('aria-expanded', String(value));
    document.getElementById(button.getAttribute('aria-controls')).hidden = !value;
  };
  function setOpen(open, restoreFocus = true) {
    if (open === header.classList.contains('is-open')) return;
    header.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
    backdrop.hidden = !open;
    if (open) {
      savedScroll = window.scrollY;
      previousBodyStyle = document.body.getAttribute('style');
      Object.assign(document.body.style, {position: 'fixed', top: `-${savedScroll}px`, width: '100%', overflow: 'hidden'});
      // Inert every branch outside the drawer, including the logo and trigger.
      let branch = nav;
      while (branch !== document.body) {
        for (const sibling of branch.parentElement.children) {
          if (sibling !== branch && sibling !== backdrop && !sibling.inert) {
            sibling.inert = true;
            inertElements.push(sibling);
          }
        }
        branch = branch.parentElement;
      }
      nav.setAttribute('role', 'dialog');
      nav.setAttribute('aria-modal', 'true');
      requestAnimationFrame(() => {
        if (header.classList.contains('is-open')) close.focus({preventScroll: true});
      });
    } else {
      for (const element of inertElements) element.inert = false;
      inertElements = [];
      if (previousBodyStyle === null) document.body.removeAttribute('style');
      else document.body.setAttribute('style', previousBodyStyle);
      const behavior = document.documentElement.style.scrollBehavior;
      document.documentElement.style.scrollBehavior = 'auto';
      window.scrollTo(0, savedScroll);
      document.documentElement.style.scrollBehavior = behavior;
      nav.removeAttribute('role');
      nav.removeAttribute('aria-modal');
      if (restoreFocus) toggle.focus();
    }
  }
  toggle.addEventListener('click', () => setOpen(!header.classList.contains('is-open')));
  close.addEventListener('click', () => setOpen(false));
  backdrop.addEventListener('click', () => setOpen(false));
  header.querySelectorAll('.site-disclosure').forEach(button => {
    button.addEventListener('click', () => expanded(button, button.getAttribute('aria-expanded') !== 'true'));
  });
  nav.querySelectorAll('a').forEach(link => {
    const url = new URL(link.href);
    if (!url.hash && (location.pathname === url.pathname || (url.pathname === '/blog/' && location.pathname.startsWith('/blog/')))) {
      link.setAttribute('aria-current', 'page');
      if (link.closest('.site-tools')) tools.classList.add('site-tools-active');
    }
    link.addEventListener('click', () => {
      setOpen(false);
      expanded(tools, false);
    });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.site-tools')) expanded(tools, false);
  });
  document.addEventListener('keydown', event => {
    const open = header.classList.contains('is-open');
    if (event.key === 'Escape') {
      if (open) setOpen(false);
      else if (tools.getAttribute('aria-expanded') === 'true') { expanded(tools, false); tools.focus(); }
    }
    if (open && event.key === 'Tab') {
      const focusable = [...nav.querySelectorAll('a, button')].filter(el => el.getClientRects().length);
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && (document.activeElement === first || document.activeElement === nav)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  nav.addEventListener('focusout', event => {
    if (!mobile.matches && event.relatedTarget && !nav.contains(event.relatedTarget)) expanded(tools, false);
  });
  mobile.addEventListener('change', () => { setOpen(false, false); expanded(tools, false); });
})();
