import '@testing-library/jest-dom';
import { server } from './server';

// Establish API mocking before all tests
beforeAll(() => server.listen());
// Reset handlers after each test
afterEach(() => server.resetHandlers());
// Clean up after the tests are finished
afterAll(() => server.close());
