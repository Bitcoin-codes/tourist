/**
 * UI Utilities — Modals, Toasts, Scroll, DOM Helpers
 */

import type { Theme } from './types';

export function $(selector: string): HTMLElement | null {
  return document.querySelector(selector);
}

export function $$(selector: string): HTMLElement[] {
  return Array.from(document.querySelectorAll(selector));
}

export function createElement(tag: string, attrs?: Record<string, string>, children?: string): HTMLElement {
  const el = document.createElement(tag);
  if (attrs) {
    Object.entries(attrs).forEach(([key, val]) => {
      if (key === 'className') el.className = val;
      else if (key === 'innerHTML') el.innerHTML = val;
      else el.setAttribute(key, val);
    });
  }
  if (children) el.innerHTML = children;
  return el;
}

export function escapeHTML(str: string): string {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function openModal(modalId: string): void {
  const overlay = document.getElementById(modalId);
  if (overlay) {
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

export function closeModal(modalId: string): void {
  const overlay = document.getElementById(modalId);
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
}

let toastTimeout: ReturnType<typeof setTimeout> | null = null;

export function showToast(message: string): void {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = createElement('div', { id: 'global-toast', className: 'toast' });
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> ${escapeHTML(message)}`;
  toast.classList.add('active');

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast?.classList.remove('active'), 3000);
}

export function initThemeToggle(): void {
  document.documentElement.setAttribute('data-theme', 'light');

  $$('.theme-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const current = (document.documentElement.getAttribute('data-theme') as Theme) || 'light';
      const next: Theme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      showToast(`Switched to ${next === 'light' ? 'Light' : 'Dark'} theme`);
    });
  });
}

export function initMobileNav(): void {
  const toggle = document.getElementById('mobile-toggle-btn');
  const navLinks = document.querySelector('.nav-links');
  if (!toggle || !navLinks) return;

  toggle.setAttribute('aria-expanded', 'false');

  toggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('active');
    toggle.classList.toggle('active', isOpen);
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
    document.body.classList.toggle('nav-open', isOpen);
  });

  $$('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('active');
      toggle.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('nav-open');
    });
  });

  document.addEventListener('click', (e: Event) => {
    const target = e.target as HTMLElement;
    if (
      navLinks.classList.contains('active') &&
      !navLinks.contains(target) &&
      !toggle.contains(target)
    ) {
      navLinks.classList.remove('active');
      toggle.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('nav-open');
    }
  });
}

export function initHeaderScroll(): void {
  const header = document.getElementById('site-header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 10);
  }, { passive: true });
}

export function initModalClose(): void {
  document.addEventListener('click', (e: Event) => {
    const target = e.target as HTMLElement;
    if (target.classList.contains('modal-overlay')) {
      target.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
}
