import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Polyfill IntersectionObserver — not implemented in jsdom but used by ConfigForm's
// sidebar active-section tracking. Must be a class so `new IntersectionObserver(...)` works.
class IntersectionObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  root: Element | null = null;
  rootMargin = '';
  thresholds: number[] = [];
  takeRecords = vi.fn(() => [] as IntersectionObserverEntry[]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  constructor(_callback: IntersectionObserverCallback, _options?: IntersectionObserverInit) {}
}
globalThis.IntersectionObserver = IntersectionObserverMock as unknown as typeof IntersectionObserver;

// jsdom's default origin (about:blank) is NOT a secure context, so window.isSecureContext is
// false. The clipboard API guard (`navigator.clipboard && isSecureContext`) would always take
// the execCommand fallback. Treat the test environment as secure so tests that mock
// navigator.clipboard exercise the real clipboard path.
Object.defineProperty(window, 'isSecureContext', {
  value: true,
  writable: false,
  configurable: true,
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});
