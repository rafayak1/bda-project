import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
    apiKey: "Your Key",
    authDomain: "Your Key",
    projectId: "Your Keyk",
    storageBucket: "Your Key",
    messagingSenderId: "Your Key",
    appId: "Your Key",
    measurementId: "Your Key"
  };

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export const mockAuth = {
  currentUser: null,
  onAuthStateChanged: (callback) => {
    callback(null);
    return () => {};
  },
  signInWithEmailAndPassword: () => Promise.resolve({}),
  createUserWithEmailAndPassword: () => Promise.resolve({}),
  signOut: () => Promise.resolve({}),
};

export const mockApp = {};

export { app, auth };
