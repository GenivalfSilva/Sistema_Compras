import { configureStore } from '@reduxjs/toolkit';

// Importação do authSlice
// @ts-ignore - Ignorando erro de importação temporariamente
import authReducer from '../features/auth/authSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Declare the shape of our state for TypeScript
declare module 'react-redux' {
  // Estende a interface DefaultRootState com nosso RootState
  interface DefaultRootState extends RootState {}
}
