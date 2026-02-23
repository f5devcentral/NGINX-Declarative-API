import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Extend globalThis type to include expect
declare global {
  var expect: typeof import('vitest').expect;
}

// Make expect available globally
globalThis.expect = expect;
