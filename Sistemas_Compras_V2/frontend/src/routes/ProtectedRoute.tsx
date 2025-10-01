import { Navigate } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const token = useAppSelector((s) => s.auth.tokens?.access) || localStorage.getItem('access');
  if (!token) return <Navigate to="/login" replace />;
  return children;
}
