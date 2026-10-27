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
      applyTheme(newTheme);
      localStorage.setItem('findmydoc-theme', newTheme);
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
  const toggle = document.querySelector('.mobile-nav-toggle');
  const links = document.querySelector('.nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('show-mobile');
    });
  }
}
