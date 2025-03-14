// firebase.js
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

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { app, auth };
