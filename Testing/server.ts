// import { setupServer } from 'msw/node';
// import { rest } from 'msw';

// // Use the same base URL as your axiosInstance in axiosConfig.tsx
// const API_BASE_URL = 'http://127.0.0.1:5000';

// console.log('[MSW]', typeof rest, rest ? '✔️ available' : '❌ undefined');

// export const server = setupServer(
//   // Login endpoint
//   rest.post(`${API_BASE_URL}/login`, (req, res, ctx) => {
//     return res(ctx.status(200), ctx.json({ token: 'mock-token' }));
//   }),

//   // Chat history endpoint
//   rest.get(`${API_BASE_URL}/chat-history`, (req, res, ctx) => {
//     return res(ctx.status(200), ctx.json({ history: [], datasetExists: false, name: 'TestUser' }));
//   }),

//   // Transform endpoint
//   rest.post(`${API_BASE_URL}/transform`, (req, res, ctx) => {
//     return res(ctx.status(200), ctx.json({ message: 'Transformed', download_url: null }));
//   }),

//   // Optional: dataset-status used in Chaty.tsx
//   rest.get(`${API_BASE_URL}/dataset-status`, (req, res, ctx) => {
//     return res(ctx.status(200), ctx.json({ datasetExists: false, name: 'TestUser' }));
//   })
// );


import { setupServer } from 'msw/node';
import { rest } from 'msw';

const API_BASE_URL = 'http://127.0.0.1:5000';

export const server = setupServer(
  rest.post(`${API_BASE_URL}/login`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ token: 'mock-token' }));
  }),
  rest.post(`${API_BASE_URL}/signup`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ token: 'mock-token' }));
  }),
  rest.get(`${API_BASE_URL}/chat-history`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ history: [], datasetExists: false, name: 'BuffUser' }));
  }),
  rest.post(`${API_BASE_URL}/transform`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ message: "Processed!", table: null }));
  }),
  rest.post(`${API_BASE_URL}/forgot-password`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ user_id: "1234" }));
  }),
);
