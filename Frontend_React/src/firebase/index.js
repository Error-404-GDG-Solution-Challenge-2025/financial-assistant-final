import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyD1j7q0tejhQv2nlb_AdEOwks0hXrOGZu0",
  authDomain: "financialaid-16bcd.firebaseapp.com",
  projectId: "financialaid-16bcd",
  storageBucket: "financialaid-16bcd.firebasestorage.app",
  messagingSenderId: "811174543926",
  appId: "1:811174543926:web:8dfd7f6e317a1ad68a8e97",
  measurementId: "G-3KBBE3T2BW"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);