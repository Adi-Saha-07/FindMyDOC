/**
 * MediConnect - Core JavaScript
 * Handles: Theme toggle, City autocomplete, Modals, Toasts, Mobile menu
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initCityAutocomplete();
  initFlashToasts();
  initModals();
  initMobileNav();
  initMobileBottomNav();
  initFeaturedCoverflow();
  initNavDropdowns();
});

/* ==========================================================================
   THEME TOGGLE (Light / Dark Mode)
   ========================================================================== */
function initTheme() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  const storedTheme = localStorage.getItem('findmydoc-theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  const initialTheme = storedTheme || (prefersDark ? 'dark' : 'light');
  applyTheme(initialTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      requestAnimationFrame(() => {
        applyTheme(newTheme);
        localStorage.setItem('findmydoc-theme', newTheme);
      });
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const toggleBtn = document.getElementById('themeToggleBtn');
  if (toggleBtn) {
    if (theme === 'dark') {
      toggleBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      `;
      toggleBtn.setAttribute('title', 'Switch to Light Mode');
    } else {
      toggleBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
        </svg>
      `;
      toggleBtn.setAttribute('title', 'Switch to Dark Mode');
    }
  }
}

/* ==========================================================================
   CITY AUTOCOMPLETE (Seed data lookup)
   ========================================================================== */
function initCityAutocomplete() {
  const inputs = document.querySelectorAll('[data-city-autocomplete="true"]');

  inputs.forEach(input => {
    const wrapper = input.closest('.autocomplete-wrapper') || input.parentElement;
    let dropdown = wrapper.querySelector('.autocomplete-dropdown');

    if (!dropdown) {
      dropdown = document.createElement('ul');
      dropdown.className = 'autocomplete-dropdown';
      wrapper.appendChild(dropdown);
    }

    let debounceTimer;

    input.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();

      debounceTimer = setTimeout(() => {
        fetchCities(query, dropdown, input);
      }, 150);
    });

    input.addEventListener('focus', () => {
      fetchCities(input.value.trim(), dropdown, input);
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });

    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
      const items = dropdown.querySelectorAll('.autocomplete-item');
      let activeIndex = Array.from(items).findIndex(it => it.classList.contains('active'));

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (activeIndex < items.length - 1) {
          if (activeIndex >= 0) items[activeIndex].classList.remove('active');
          items[activeIndex + 1].classList.add('active');
          items[activeIndex + 1].scrollIntoView({ block: 'nearest' });
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (activeIndex > 0) {
          items[activeIndex].classList.remove('active');
          items[activeIndex - 1].classList.add('active');
          items[activeIndex - 1].scrollIntoView({ block: 'nearest' });
        }
      } else if (e.key === 'Enter') {
        if (activeIndex >= 0 && items[activeIndex]) {
          e.preventDefault();
          items[activeIndex].click();
        }
      } else if (e.key === 'Escape') {
        dropdown.classList.remove('show');
      }
    });
  });
}

function fetchCities(query, dropdown, input) {
  fetch(`/api/cities?q=${encodeURIComponent(query)}`)
    .then(res => res.json())
    .then(data => {
      const cities = data.cities || [];
      dropdown.innerHTML = '';

      if (cities.length === 0) {
        dropdown.classList.remove('show');
        return;
      }

      cities.forEach(city => {
        const li = document.createElement('li');
        li.className = 'autocomplete-item';
        li.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--brand-green);">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
            <circle cx="12" cy="10" r="3"></circle>
          </svg>
          <span>${city}</span>
        `;
        li.addEventListener('click', () => {
          input.value = city;
          dropdown.classList.remove('show');
          input.focus();
        });
        dropdown.appendChild(li);
      });

      dropdown.classList.add('show');
    })
    .catch(err => {
      console.error('Error fetching city list:', err);
      dropdown.classList.remove('show');
    });
}

/* ==========================================================================
   TOASTS / FLASH MESSAGES
   ========================================================================== */
function initFlashToasts() {
  const toasts = document.querySelectorAll('.flash-toast');
  toasts.forEach(toast => {
    const closeBtn = toast.querySelector('.flash-toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => removeToast(toast));
    }
    // Auto remove after 5.5s
    setTimeout(() => {
      removeToast(toast);
    }, 5500);
  });
}

function removeToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
  toast.style.opacity = '0';
  toast.style.transform = 'translateX(50px) scale(0.9)';
  setTimeout(() => {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 300);
}

/* ==========================================================================
   GLASS MODALS
   ========================================================================== */
function initModals() {
  // Modal trigger buttons
  const triggers = document.querySelectorAll('[data-open-modal]');
  triggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modalId = btn.getAttribute('data-open-modal');
      const modalBackdrop = document.getElementById(modalId);
      if (!modalBackdrop) return;

      // Check if button passes data-appointment-id, patient-name, action
      const aptId = btn.getAttribute('data-appointment-id');
      const patName = btn.getAttribute('data-patient-name');
      const action = btn.getAttribute('data-action') || 'accept';

      const inputAptId = modalBackdrop.querySelector('input[name="appointment_id"]');
      const inputAction = modalBackdrop.querySelector('input[name="action"]');
      const spanPatName = modalBackdrop.querySelector('[data-modal-patient-name]');

      if (inputAptId && aptId) inputAptId.value = aptId;
      if (inputAction && action) inputAction.value = action;
      if (spanPatName && patName) spanPatName.textContent = patName;

      modalBackdrop.classList.add('show');
      document.body.style.overflow = 'hidden';
    });
  });

  // Close modal triggers
  const closeBtns = document.querySelectorAll('[data-close-modal]');
  closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.glass-modal-backdrop');
      if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });

  // Close when clicking outside of modal card
  const modalBackdrops = document.querySelectorAll('.glass-modal-backdrop');
  modalBackdrops.forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });

  // ESC key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      modalBackdrops.forEach(backdrop => {
        backdrop.classList.remove('show');
      });
      document.body.style.overflow = '';
    }
  });
}

/* ==========================================================================
   MOBILE NAVIGATION
   ========================================================================== */
function initMobileNav() {
  const toggle = document.getElementById('mobileNavToggle');
  const links = document.getElementById('mainNavLinks');
  const backdrop = document.getElementById('mobileNavBackdrop');

  if (!toggle || !links) return;

  function openNav() {
    links.classList.add('show-mobile');
    toggle.classList.add('open');
    if (backdrop) backdrop.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeNav() {
    links.classList.remove('show-mobile');
    toggle.classList.remove('open');
    if (backdrop) backdrop.classList.remove('show');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', () => {
    if (links.classList.contains('show-mobile')) {
      closeNav();
    } else {
      openNav();
    }
  });

  // Close on backdrop click
  if (backdrop) {
    backdrop.addEventListener('click', closeNav);
  }

  // Close when a nav link is clicked
  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', closeNav);
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeNav();
  });
}

/* ==========================================================================
   FEATURED DOCTORS COVERFLOW CAROUSEL
   ========================================================================== */
function initFeaturedCoverflow() {
  const root = document.getElementById('featuredCoverflow');
  if (!root) return;

  const items = Array.from(root.querySelectorAll('.featured-coverflow-item'));
  const dots = Array.from(root.querySelectorAll('.featured-coverflow-dot'));
  const prevBtn = root.querySelector('.featured-coverflow-arrow--prev');
  const nextBtn = root.querySelector('.featured-coverflow-arrow--next');
  const total = items.length;
  if (total === 0) return;

  let activeIndex = 0;

  function render() {
    items.forEach((item, idx) => {
      item.classList.remove('is-active', 'is-prev', 'is-next', 'is-far-prev', 'is-far-next', 'is-hidden');
      let offset = idx - activeIndex;
      if (offset > total / 2) offset -= total;
      if (offset < -total / 2) offset += total;

      if (offset === 0) {
        item.classList.add('is-active');
      } else if (offset === -1) {
        item.classList.add('is-prev');
      } else if (offset === 1) {
        item.classList.add('is-next');
      } else if (offset === -2 && total >= 5) {
        item.classList.add('is-far-prev');
      } else if (offset === 2 && total >= 5) {
        item.classList.add('is-far-next');
      } else {
        item.classList.add('is-hidden');
      }
    });

    dots.forEach((dot, idx) => {
      dot.classList.toggle('is-active', idx === activeIndex);
    });
  }

  function goTo(index) {
    activeIndex = ((index % total) + total) % total;
    render();
  }

  if (prevBtn) prevBtn.addEventListener('click', () => goTo(activeIndex - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => goTo(activeIndex + 1));

  items.forEach((item, idx) => {
    item.addEventListener('click', () => {
      if (idx !== activeIndex) goTo(idx);
    });
  });

  dots.forEach((dot, idx) => {
    dot.addEventListener('click', () => goTo(idx));
  });

  // ── Touch / swipe navigation (mobile) ──────────────────────────────────────
  // On mobile, arrows are hidden; users swipe left/right to navigate.
  // We also add a subtle drag-translate while the finger is moving so the
  // carousel feels physically responsive, then snap on touchend.
  let touchStartX = 0;
  let touchStartY = 0;
  let isDraggingH = false;   // true once we confirmed a horizontal drag

  const stage = root.querySelector('.featured-coverflow-stage');

  root.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].clientX;
    touchStartY = e.changedTouches[0].clientY;
    isDraggingH = false;
  }, { passive: true });

  root.addEventListener('touchmove', (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;

    // Determine drag axis on first meaningful move
    if (!isDraggingH && (Math.abs(dx) > 6 || Math.abs(dy) > 6)) {
      isDraggingH = Math.abs(dx) > Math.abs(dy);
    }

    if (isDraggingH) {
      // Live drag: shift the active card slightly for tactile feedback
      const activeEl = items[activeIndex];
      if (activeEl) {
        const pct = Math.min(Math.abs(dx) / 300, 0.35) * Math.sign(dx);
        activeEl.style.transform =
          `translate3d(calc(-50% + ${dx * 0.18}px), -50%, 0) scale(${1 - Math.abs(pct) * 0.08})`;
      }
    }
  }, { passive: true });

  root.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;

    // Reset any inline transform on the active card before CSS re-applies
    if (items[activeIndex]) items[activeIndex].style.transform = '';

    if (isDraggingH && Math.abs(dx) > 40) {
      goTo(dx < 0 ? activeIndex + 1 : activeIndex - 1);
    }
    isDraggingH = false;
  }, { passive: true });

  render();
}


/* ==========================================================================
   NAVBAR NOTIFICATION MODAL & PROFILE DROPDOWN
   ========================================================================== */
function initNavDropdowns() {
  const notifBtn = document.getElementById('navNotifBtn');
  const notifBackdrop = document.getElementById('navNotifBackdrop');
  const notifClose = document.getElementById('navNotifClose');
  const notifBadge = document.getElementById('navNotifBadge');
  const notifHeaderCount = document.getElementById('navNotifHeaderCount');
  const notifList = document.getElementById('navNotifList');
  const markReadBtn = document.getElementById('navNotifMarkRead');

  const profileBtn = document.getElementById('navProfileBtn');
  const profileDropdown = document.getElementById('navProfileDropdown');
  const guestBtn = document.getElementById('navGuestBtn');
  const guestDropdown = document.getElementById('navGuestDropdown');

  function openNotifModal() {
    if (!notifBackdrop) return;
    closeDropdown(profileBtn, profileDropdown);
    notifBackdrop.hidden = false;
    document.body.style.overflow = 'hidden';
    requestAnimationFrame(() => notifBackdrop.classList.add('is-open'));
    if (notifBtn) notifBtn.setAttribute('aria-expanded', 'true');
  }

  function closeNotifModal() {
    if (!notifBackdrop || notifBackdrop.hidden) return;
    notifBackdrop.classList.remove('is-open');
    document.body.style.overflow = '';
    if (notifBtn) notifBtn.setAttribute('aria-expanded', 'false');
    setTimeout(() => {
      if (!notifBackdrop.classList.contains('is-open')) notifBackdrop.hidden = true;
    }, 200);
  }

  function openDropdown(btn, panel) {
    if (!panel) return;
    panel.hidden = false;
    requestAnimationFrame(() => panel.classList.add('is-open'));
    if (btn) btn.setAttribute('aria-expanded', 'true');
  }

  function closeDropdown(btn, panel) {
    if (!panel || panel.hidden) return;
    panel.classList.remove('is-open');
    if (btn) btn.setAttribute('aria-expanded', 'false');
    setTimeout(() => {
      if (!panel.classList.contains('is-open')) panel.hidden = true;
    }, 180);
  }

  if (notifBtn && notifBackdrop) {
    notifBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (notifBackdrop.hidden) {
        openNotifModal();
      } else {
        closeNotifModal();
      }
    });
  }

  if (notifClose) {
    notifClose.addEventListener('click', closeNotifModal);
  }

  if (notifBackdrop) {
    notifBackdrop.addEventListener('click', (e) => {
      if (e.target === notifBackdrop) closeNotifModal();
    });
  }

  if (profileBtn && profileDropdown) {
    profileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const willOpen = profileDropdown.hidden;
      closeNotifModal();
      if (willOpen) {
        openDropdown(profileBtn, profileDropdown);
      } else {
        closeDropdown(profileBtn, profileDropdown);
      }
    });
  }

  if (guestBtn && guestDropdown) {
    guestBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const willOpen = guestDropdown.hidden;
      closeNotifModal();
      if (willOpen) {
        openDropdown(guestBtn, guestDropdown);
      } else {
        closeDropdown(guestBtn, guestDropdown);
      }
    });
  }

  document.addEventListener('click', (e) => {
    if (profileDropdown && !profileDropdown.hidden && !profileDropdown.contains(e.target) && !profileBtn.contains(e.target)) {
      closeDropdown(profileBtn, profileDropdown);
    }
    if (guestDropdown && !guestDropdown.hidden && !guestDropdown.contains(e.target) && !guestBtn.contains(e.target)) {
      closeDropdown(guestBtn, guestDropdown);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeNotifModal();
      closeDropdown(profileBtn, profileDropdown);
      closeDropdown(guestBtn, guestDropdown);
    }
  });

  // Track read notifications in localStorage per user
  if (notifList && notifBadge) {
    const userId = notifList.getAttribute('data-user-id') || 'guest';
    const storageKey = `findmydoc-read-notifs:${userId}`;
    const items = Array.from(notifList.querySelectorAll('.nav-notif-item[data-notif-key]'));

    function getReadSet() {
      try {
        return new Set(JSON.parse(localStorage.getItem(storageKey) || '[]'));
      } catch {
        return new Set();
      }
    }

    function saveReadSet(set) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(Array.from(set)));
      } catch {
        /* ignore storage quota errors */
      }
    }

    function syncUnreadUI() {
      const readSet = getReadSet();
      let unreadCount = 0;
      items.forEach((item) => {
        const key = item.getAttribute('data-notif-key');
        const isRead = readSet.has(key);
        item.classList.toggle('is-read', isRead);
        if (!isRead) unreadCount += 1;
      });
      if (unreadCount > 0) {
        notifBadge.textContent = String(unreadCount);
        notifBadge.hidden = false;
        if (notifHeaderCount) {
          notifHeaderCount.textContent = String(unreadCount);
          notifHeaderCount.hidden = false;
        }
      } else {
        notifBadge.hidden = true;
        if (notifHeaderCount) notifHeaderCount.hidden = true;
      }
    }

    items.forEach((item) => {
      item.addEventListener('click', () => {
        const key = item.getAttribute('data-notif-key');
        if (!key) return;
        const readSet = getReadSet();
        readSet.add(key);
        saveReadSet(readSet);
        syncUnreadUI();
      });
    });

    if (markReadBtn) {
      markReadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const readSet = getReadSet();
        items.forEach((item) => {
          const key = item.getAttribute('data-notif-key');
          if (key) readSet.add(key);
        });
        saveReadSet(readSet);
        syncUnreadUI();
      });
    }

    syncUnreadUI();
  }
}


/* ==========================================================================
   MOBILE BOTTOM LIQUID GLASS NAVBAR (Tap + Swipe/Drag Selection)
   ========================================================================== */
function initMobileBottomNav() {
  const nav = document.getElementById('mobileBottomNav');
  const track = document.getElementById('mobileBottomTrack');
  const pill = document.getElementById('mobileBottomPill');
  if (!nav || !track || !pill) return;

  const items = Array.from(track.querySelectorAll('.mobile-bottom-item'));
  if (!items.length) return;

  // Highlight hash tab if currently on home page with matching hash
  function syncActiveFromLocation() {
    const hash = window.location.hash;
    if (hash) {
      const hashItem = items.find(el => el.dataset.navHash === hash);
      if (hashItem) {
        items.forEach(el => el.classList.remove('is-active'));
        hashItem.classList.add('is-active');
      }
    }
  }

  function movePillToItem(item, immediate = false) {
    if (!item) {
      pill.classList.remove('is-visible');
      return;
    }
    const trackRect = track.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    if (trackRect.width === 0 || itemRect.width === 0) return;

    const offsetLeft = itemRect.left - trackRect.left;
    if (immediate) pill.classList.add('is-dragging');
    pill.style.width = `${itemRect.width}px`;
    pill.style.transform = `translate3d(${offsetLeft}px, 0, 0)`;
    pill.classList.add('is-visible');
    if (immediate) {
      requestAnimationFrame(() => pill.classList.remove('is-dragging'));
    }
  }

  function getActiveItem() {
    return items.find(el => el.classList.contains('is-active')) || null;
  }

  function selectAndNavigate(item) {
    if (!item) return;
    items.forEach(el => {
      el.classList.remove('is-active', 'is-hovered');
    });
    item.classList.add('is-active');
    movePillToItem(item);

    const href = item.getAttribute('href');
    if (!href) return;

    // Brief visual snap so user sees the liquid pill land before navigating
    setTimeout(() => {
      window.location.href = href;
    }, 140);
  }

  // Initial pill placement
  syncActiveFromLocation();
  const initialActive = getActiveItem();
  if (initialActive) {
    movePillToItem(initialActive, true);
  }

  window.addEventListener('resize', () => {
    const active = getActiveItem();
    if (active) movePillToItem(active, true);
  });

  window.addEventListener('hashchange', () => {
    syncActiveFromLocation();
    const active = getActiveItem();
    if (active) movePillToItem(active);
  });

  // ── Touch Swipe / Drag across the Liquid Glass Dock ────────────────────────
  let startX = 0;
  let startY = 0;
  let isSwiping = false;
  let hoveredItem = null;

  function itemAtPoint(clientX) {
    const trackRect = track.getBoundingClientRect();
    const clampedX = Math.max(trackRect.left + 1, Math.min(clientX, trackRect.right - 1));
    for (const item of items) {
      const r = item.getBoundingClientRect();
      if (clampedX >= r.left && clampedX <= r.right) {
        return item;
      }
    }
    return null;
  }

  track.addEventListener('touchstart', (e) => {
    if (e.touches.length !== 1) return;
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    isSwiping = false;
    hoveredItem = itemAtPoint(startX);
  }, { passive: true });

  track.addEventListener('touchmove', (e) => {
    if (e.touches.length !== 1) return;
    const dx = e.touches[0].clientX - startX;
    const dy = e.touches[0].clientY - startY;

    if (!isSwiping && Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) {
      isSwiping = true;
      pill.classList.add('is-dragging');
    }

    if (isSwiping) {
      e.preventDefault();
      const target = itemAtPoint(e.touches[0].clientX);
      if (target) {
        const trackRect = track.getBoundingClientRect();
        const itemRect = target.getBoundingClientRect();
        const rawLeft = e.touches[0].clientX - trackRect.left - itemRect.width / 2;
        const maxLeft = trackRect.width - itemRect.width;
        const clampedLeft = Math.max(0, Math.min(rawLeft, maxLeft));

        pill.style.width = `${itemRect.width}px`;
        pill.style.transform = `translate3d(${clampedLeft}px, 0, 0) scale(1.04)`;
        pill.classList.add('is-visible');

        if (hoveredItem !== target) {
          items.forEach(el => el.classList.remove('is-hovered'));
          target.classList.add('is-hovered');
          hoveredItem = target;
        }
      }
    }
  }, { passive: false });

  track.addEventListener('touchend', (e) => {
    pill.classList.remove('is-dragging');
    if (isSwiping) {
      const endX = e.changedTouches[0].clientX;
      const target = itemAtPoint(endX) || hoveredItem;
      isSwiping = false;
      hoveredItem = null;
      if (target) {
        selectAndNavigate(target);
      } else {
        movePillToItem(getActiveItem());
      }
    }
  }, { passive: true });

  track.addEventListener('touchcancel', () => {
    pill.classList.remove('is-dragging');
    items.forEach(el => el.classList.remove('is-hovered'));
    isSwiping = false;
    hoveredItem = null;
    movePillToItem(getActiveItem());
  }, { passive: true });

  // Also animate pill on normal tap before navigation
  items.forEach((item) => {
    item.addEventListener('click', (e) => {
      if (item.dataset.navHash && window.location.pathname === '/') {
        items.forEach(el => el.classList.remove('is-active'));
        item.classList.add('is-active');
        movePillToItem(item);
        return;
      }
      e.preventDefault();
      selectAndNavigate(item);
    });
  });
}
