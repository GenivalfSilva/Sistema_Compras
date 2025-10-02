import { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Stack, 
  LinearProgress,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Button,
  IconButton,
  Tooltip,
  Avatar,
  Divider,
  useTheme,
  alpha
} from '@mui/material';
import { SolicitacoesAPI, type SolicitacaoListItem, type SolicitacoesDashboard } from '../../services/solicitacoes';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../app/hooks';

// Ícones
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PendingIcon from '@mui/icons-material/Pending';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import AssessmentIcon from '@mui/icons-material/Assessment';

export default function DashboardDiretoria() {
  const [data, setData] = useState<SolicitacoesDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const theme = useTheme();
  const profile = useAppSelector((s) => s.auth.profile);

  const load = async () => {
    setLoading(true);
    try {
      setError(null);
      const d = await SolicitacoesAPI.dashboard();
      setData(d);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Falha ao carregar o dashboard');
      setData({
        resumo: { total: 0, pendentes: 0, aprovadas: 0, reprovadas: 0, finalizadas: 0 },
        sla: { vencidas: 0, proximo_vencimento: 0, ok: 0 },
        por_status: {},
        por_prioridade: {},
        solicitacoes_recentes: [],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const recentes: SolicitacaoListItem[] = data?.solicitacoes_recentes || [];
  
  // Filtrar solicitações relevantes para o perfil Diretoria
  const solicitacoesDiretoria = recentes.filter(
    item => ['Aguardando Aprovação'].includes(item.status)
  );

  // Estatísticas para o dashboard da diretoria
  const estatisticas = {
    aguardandoAprovacao: solicitacoesDiretoria.length,
    aprovadas: data?.resumo.aprovadas || 0,
    reprovadas: data?.resumo.reprovadas || 0,
    valorTotal: solicitacoesDiretoria.reduce((total, item) => total + (item.valor_estimado || 0), 0),
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Card sx={{ mb: 3, borderRadius: 2, overflow: 'hidden', boxShadow: theme.shadows[3] }}>
        <Box 
          sx={{ 
            p: 3, 
            background: 'linear-gradient(45deg, #d91a2a 30%, #e14554 90%)',
            color: 'white',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          {/* Elementos decorativos de fundo */}
          <Box 
            sx={{ 
              position: 'absolute', 
              right: -20, 
              top: -20, 
              width: 200, 
              height: 200, 
              borderRadius: '50%', 
              background: alpha(theme.palette.common.white, 0.1),
              zIndex: 0
            }} 
          />
          <Box 
            sx={{ 
              position: 'absolute', 
              right: 80, 
              bottom: -40, 
              width: 120, 
              height: 120, 
              borderRadius: '50%', 
              background: alpha(theme.palette.common.white, 0.05),
              zIndex: 0
            }} 
          />
          
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ position: 'relative', zIndex: 1 }}>
            <Box>
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                <Avatar 
                  sx={{ 
                    bgcolor: theme.palette.secondary.main,
                    width: 56, 
                    height: 56,
                    boxShadow: theme.shadows[3]
                  }}
                >
                  {profile?.username?.charAt(0).toUpperCase() || 'D'}
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold" sx={{ textShadow: '0px 2px 4px rgba(0,0,0,0.2)' }}>
                    Painel Executivo
                  </Typography>
                  <Typography variant="subtitle1">
                    Bem-vindo, {profile?.username || 'Usuário'} | {profile?.perfil || 'Diretoria'}
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" sx={{ mt: 1, maxWidth: 500, opacity: 0.9 }}>
                Aprove pedidos de compras e monitore os gastos da empresa em um só lugar.
              </Typography>
            </Box>
            <Tooltip title="Atualizar dados">
              <IconButton 
                color="inherit" 
                onClick={load} 
                disabled={loading}
                sx={{ 
                  bgcolor: alpha(theme.palette.common.white, 0.1),
                  '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.2) }
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {loading && <LinearProgress color="secondary" />}

        {error && (
          <Box sx={{ p: 2 }}>
            <Typography color="error">{error}</Typography>
          </Box>
        )}
      </Card>

      {/* Cards de estatísticas */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
        {/* Card Aguardando Aprovação */}
        <Card sx={{ 
          borderRadius: 2, 
          boxShadow: theme.shadows[2],
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] }
        }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" fontWeight="medium">Aguardando</Typography>
              <Avatar sx={{ bgcolor: alpha(theme.palette.warning.main, 0.1), color: 'warning.main' }}>
                <PendingIcon />
              </Avatar>
            </Stack>
            <Typography variant="h3" fontWeight="bold" color="warning.main">
              {estatisticas.aguardandoAprovacao}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Pedidos aguardando aprovação
            </Typography>
          </CardContent>
        </Card>

        {/* Card Valor Total */}
        <Card sx={{ 
          borderRadius: 2, 
          boxShadow: theme.shadows[2],
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] }
        }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" fontWeight="medium">Valor Total</Typography>
              <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main' }}>
                <MonetizationOnIcon />
              </Avatar>
            </Stack>
            <Typography variant="h3" fontWeight="bold" color="primary.main">
              {formatCurrency(estatisticas.valorTotal)}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Em pedidos pendentes
            </Typography>
          </CardContent>
        </Card>

        {/* Card Aprovadas */}
        <Card sx={{ 
          borderRadius: 2, 
          boxShadow: theme.shadows[2],
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] }
        }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" fontWeight="medium">Aprovadas</Typography>
              <Avatar sx={{ bgcolor: alpha(theme.palette.success.main, 0.1), color: 'success.main' }}>
                <CheckCircleIcon />
              </Avatar>
            </Stack>
            <Typography variant="h3" fontWeight="bold" color="success.main">
              {estatisticas.aprovadas}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Solicitações aprovadas
            </Typography>
          </CardContent>
        </Card>

        {/* Card Reprovadas */}
        <Card sx={{ 
          borderRadius: 2, 
          boxShadow: theme.shadows[2],
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] }
        }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" fontWeight="medium">Reprovadas</Typography>
              <Avatar sx={{ bgcolor: alpha(theme.palette.error.main, 0.1), color: 'error.main' }}>
                <CancelIcon />
              </Avatar>
            </Stack>
            <Typography variant="h3" fontWeight="bold" color="error.main">
              {estatisticas.reprovadas}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Solicitações reprovadas
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Tabela de solicitações aguardando aprovação */}
      <Card sx={{ flex: 1, borderRadius: 2, overflow: 'hidden', boxShadow: theme.shadows[2] }}>
        <CardContent sx={{ p: 0, height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <AssessmentIcon color="primary" />
              <Typography variant="h6" fontWeight="medium">Solicitações Aguardando Aprovação</Typography>
            </Stack>
            <Button 
              variant="contained" 
              size="small" 
              onClick={() => navigate('/diretoria/aprovacoes')}
              endIcon={<VisibilityIcon />}
            >
              Ver Todas
            </Button>
          </Box>
          <Divider />
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                  <TableCell>Nº</TableCell>
                  <TableCell>Descrição</TableCell>
                  <TableCell>Departamento</TableCell>
                  <TableCell>Valor</TableCell>
                  <TableCell>Data</TableCell>
                  <TableCell align="right">Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading && Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={`skeleton-${i}`}>
                    <TableCell colSpan={6} align="center">
                      <LinearProgress />
                    </TableCell>
                  </TableRow>
                ))}
                {!loading && solicitacoesDiretoria.map((row) => (
                  <TableRow 
                    key={row.id} 
                    hover 
                    sx={{ 
                      cursor: 'pointer',
                      '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02) },
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <TableCell>{row.numero_solicitacao_estoque}</TableCell>
                    <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {row.descricao}
                    </TableCell>
                    <TableCell>{row.departamento}</TableCell>
                    <TableCell>{row.valor_estimado ? formatCurrency(row.valor_estimado) : '-'}</TableCell>
                    <TableCell>{formatDate(row.created_at)}</TableCell>
                    <TableCell align="right">
                      <Button 
                        size="small" 
                        variant="outlined" 
                        color="primary"
                        startIcon={<VisibilityIcon />}
                        onClick={() => navigate(`/solicitacoes/${row.id}`)}
                      >
                        Detalhes
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!loading && solicitacoesDiretoria.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
                        <PendingIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1 }} />
                        <Typography variant="body1" color="text.secondary" gutterBottom>
                          Nenhuma solicitação aguardando aprovação.
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 400, textAlign: 'center' }}>
                          Todas as solicitações que precisam de aprovação aparecerão aqui.
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
