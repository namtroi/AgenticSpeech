import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect method with testing-library's matchers
expect.extend(matchers);

// Automatically clean up DOM after each test to prevent state leakage
afterEach(() => {
  cleanup();
});
