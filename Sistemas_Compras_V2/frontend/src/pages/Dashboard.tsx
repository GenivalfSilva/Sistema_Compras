import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

export default function Dashboard() {
  const navigate = useNavigate();
  const profile = useAppSelector((s) => s.auth.profile);
  const perms = profile?.permissions;

  useEffect(() => {
    // Redirecionar para o dashboard específico do perfil
    if (perms?.can_approve) {
      navigate('/dashboard/diretoria');
    } else if (perms?.can_manage_procurement) {
      navigate('/dashboard/suprimentos');
    } else if (perms?.can_create_solicitation) {
      navigate('/dashboard/solicitante');
    } else {
      navigate('/solicitacoes');
    }
  }, [navigate, perms]);

  return null;
}
