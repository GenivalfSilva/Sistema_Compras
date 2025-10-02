import { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Stack, 
  Card, 
  CardContent, 
  CardHeader, 
  Divider, 
  Avatar, 
  Chip, 
  Button, 
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  LinearProgress,
  Alert,
  useTheme,
  alpha
} from '@mui/material';
import { SolicitacoesAPI, type SolicitacoesDashboard, type SolicitacaoListItem } from '../../services/solicitacoes';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../app/hooks';

// Ícones
import RefreshIcon from '@mui/icons-material/Refresh';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import PendingIcon from '@mui/icons-material/Pending';
import ReceiptIcon from '@mui/icons-material/Receipt';
import AssignmentIcon from '@mui/icons-material/Assignment';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DonutLargeIcon from '@mui/icons-material/DonutLarge';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

export default function DashboardSuprimentos() {
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
  
  // Filtrar solicitações relevantes para o perfil Suprimentos
  const solicitacoesSuprimentos = recentes.filter(
    item => ['Suprimentos', 'Em Cotação', 'Pedido de Compras', 'Aguardando Aprovação'].includes(item.status)
  );

  // Contagem por status para o perfil Suprimentos
  const contagemStatus = {
    'Suprimentos': solicitacoesSuprimentos.filter(item => item.status === 'Suprimentos').length,
    'Em Cotação': solicitacoesSuprimentos.filter(item => item.status === 'Em Cotação').length,
    'Pedido de Compras': solicitacoesSuprimentos.filter(item => item.status === 'Pedido de Compras').length,
    'Aguardando Aprovação': solicitacoesSuprimentos.filter(item => item.status === 'Aguardando Aprovação').length,
  };

  // Tipo para cores do Material-UI
  type MuiColor = 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';

  // Helper function to get status color
  const getStatusColor = (status: string): MuiColor => {
    const statusMap: Record<string, MuiColor> = {
      'Solicitação': 'info',
      'Requisição': 'info',
      'Suprimentos': 'info',
      'Em Cotação': 'warning',
      'Pedido de Compras': 'warning',
      'Aguardando Aprovação': 'warning',
      'Aprovado': 'success',
      'Reprovado': 'error',
      'Compra feita': 'success',
      'Aguardando Entrega': 'warning',
      'Pedido Finalizado': 'success'
    };
    return statusMap[status] || 'primary';
  };

  // Format date to be more readable
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
            background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 50%, ${theme.palette.primary.light} 100%)`,
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
                  {profile?.username?.charAt(0).toUpperCase() || 'U'}
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold" sx={{ textShadow: '0px 2px 4px rgba(0,0,0,0.2)' }}>
                    Painel Suprimentos
                  </Typography>
                  <Typography variant="subtitle1">
                    Bem-vindo, {profile?.username || 'Usuário'} | {profile?.perfil || 'Suprimentos'}
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" sx={{ mt: 1, maxWidth: 500, opacity: 0.9 }}>
                Gerencie requisições, cotações e pedidos de compras em um só lugar.
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Button 
                variant="contained" 
                color="secondary" 
                startIcon={<RefreshIcon />}
                onClick={load}
                disabled={loading}
                sx={{ 
                  fontWeight: 'bold',
                  boxShadow: theme.shadows[5],
                  '&:hover': { boxShadow: theme.shadows[8] }
                }}
              >
                Atualizar
              </Button>
            </Stack>
          </Stack>
        </Box>

        {loading && <LinearProgress color="secondary" />}

        {error && (
          <Alert severity="error" sx={{ mx: 2, mt: 2 }} variant="filled">{error}</Alert>
        )}
      </Card>

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3, flex: 1, overflow: 'hidden' }}>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 70%' }, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Cards de resumo */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
            {/* Card Suprimentos */}
            <Card sx={{ 
              height: '100%', 
              borderRadius: 2,
              boxShadow: theme.shadows[2],
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] }
            }}>
              <CardContent sx={{ p: 2, pb: '16px !important' }}>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), color: 'info.main' }}>
                    <ShoppingCartIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Suprimentos</Typography>
                </Stack>
                {loading ? <LinearProgress /> : (
                  <Typography variant="h4" fontWeight="bold">{contagemStatus['Suprimentos'] || 0}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Para processar</Typography>
                  <Chip 
                    size="small" 
                    label="Pendentes" 
                    color="info" 
                    variant="outlined" 
                    sx={{ height: 18, fontSize: '0.7rem' }} 
                    onClick={() => navigate('/suprimentos/processar')}
                  />
                </Stack>
              </CardContent>
            </Card>
            
            {/* Card Em Cotação */}
            <Card sx={{ 
              height: '100%', 
              borderRadius: 2,
              boxShadow: theme.shadows[2],
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] },
              position: 'relative',
              overflow: 'hidden'
            }}>
              <Box sx={{ position: 'absolute', top: 0, left: 0, width: 4, height: '100%', bgcolor: 'warning.main' }} />
              <CardContent sx={{ p: 2, pb: '16px !important' }}>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.warning.main, 0.1), color: 'warning.main' }}>
                    <ReceiptIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Em Cotação</Typography>
                </Stack>
                {loading ? <LinearProgress /> : (
                  <Typography variant="h4" fontWeight="bold" color="warning.main">{contagemStatus['Em Cotação'] || 0}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Em andamento</Typography>
                  <Chip 
                    size="small" 
                    label="Cotações" 
                    color="warning" 
                    variant="outlined" 
                    sx={{ height: 18, fontSize: '0.7rem' }} 
                    onClick={() => navigate('/suprimentos/cotacoes')}
                  />
                </Stack>
              </CardContent>
            </Card>
            
            {/* Card Pedidos */}
            <Card sx={{ 
              height: '100%', 
              borderRadius: 2,
              boxShadow: theme.shadows[2],
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] },
              position: 'relative',
              overflow: 'hidden'
            }}>
              <Box sx={{ position: 'absolute', top: 0, left: 0, width: 4, height: '100%', bgcolor: 'primary.main' }} />
              <CardContent sx={{ p: 2, pb: '16px !important' }}>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main' }}>
                    <LocalShippingIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Pedidos</Typography>
                </Stack>
                {loading ? <LinearProgress /> : (
                  <Typography variant="h4" fontWeight="bold" color="primary.main">{contagemStatus['Pedido de Compras'] || 0}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Para aprovação</Typography>
                  <Chip 
                    size="small" 
                    label="Pedidos" 
                    color="primary" 
                    variant="outlined" 
                    sx={{ height: 18, fontSize: '0.7rem' }} 
                    onClick={() => navigate('/suprimentos/pedidos')}
                  />
                </Stack>
              </CardContent>
            </Card>
            
            {/* Card Aguardando */}
            <Card sx={{ 
              height: '100%', 
              borderRadius: 2,
              boxShadow: theme.shadows[2],
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] },
              position: 'relative',
              overflow: 'hidden'
            }}>
              <Box sx={{ position: 'absolute', top: 0, left: 0, width: 4, height: '100%', bgcolor: 'secondary.main' }} />
              <CardContent sx={{ p: 2, pb: '16px !important' }}>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main' }}>
                    <PendingIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Aguardando</Typography>
                </Stack>
                {loading ? <LinearProgress /> : (
                  <Typography variant="h4" fontWeight="bold" color="secondary.main">{contagemStatus['Aguardando Aprovação'] || 0}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Aprovação</Typography>
                  <Chip 
                    size="small" 
                    label="Diretoria" 
                    color="secondary" 
                    variant="outlined" 
                    sx={{ height: 18, fontSize: '0.7rem' }} 
                  />
                </Stack>
              </CardContent>
            </Card>
          </Box>

          {/* Tabela de solicitações */}
          <Card sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: theme.shadows[2], flex: 1, display: 'flex', flexDirection: 'column' }}>
            <CardHeader 
              title="Solicitações em Andamento" 
              titleTypographyProps={{ fontWeight: 'bold' }}
              avatar={
                <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main' }}>
                  <AssignmentIcon />
                </Avatar>
              }
            />
            <Divider />
            <Box sx={{ flex: 1, overflow: 'auto' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                    <TableCell>Data</TableCell>
                    <TableCell>#</TableCell>
                    <TableCell>Descrição</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Prioridade</TableCell>
                    <TableCell align="right">Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading && Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={`skeleton-${i}`}>
                      <TableCell colSpan={6} align="center">
                        <LinearProgress />
                      </TableCell>
                    </TableRow>
                  ))}
                  {!loading && solicitacoesSuprimentos.map((row) => (
                    <TableRow 
                      key={row.id} 
                      hover 
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.02) },
                        transition: 'background-color 0.2s'
                      }}
                      onClick={() => navigate(`/solicitacoes/${row.id}`)}
                    >
                      <TableCell>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Box sx={{ 
                            width: 8, 
                            height: 8, 
                            borderRadius: '50%', 
                            bgcolor: `${getStatusColor(row.status_display || row.status)}.main`,
                            boxShadow: `0 0 0 2px ${alpha(theme.palette[getStatusColor(row.status_display || row.status)].main, 0.2)}`
                          }} />
                          <Typography variant="body2">{formatDate(row.created_at)}</Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium" color="text.primary">
                          {row.numero_solicitacao_estoque || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            maxWidth: 250, 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis', 
                            whiteSpace: 'nowrap' 
                          }}
                        >
                          {row.descricao}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small" 
                          label={row.status_display || row.status} 
                          color={getStatusColor(row.status_display || row.status)}
                          variant="outlined"
                          sx={{ fontWeight: 500 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small" 
                          label={row.prioridade_display || row.prioridade} 
                          color={row.prioridade === 'Alta' ? 'error' : row.prioridade === 'Normal' ? 'warning' : 'info'}
                          variant="outlined"
                          sx={{ fontWeight: 500 }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Button 
                          size="small" 
                          variant="outlined" 
                          color="primary"
                          startIcon={<VisibilityIcon />}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/solicitacoes/${row.id}`);
                          }}
                        >
                          Detalhes
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!loading && solicitacoesSuprimentos.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
                          <ShoppingCartIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1 }} />
                          <Typography variant="body1" color="text.secondary" gutterBottom>
                            Nenhuma solicitação em andamento.
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 300, textAlign: 'center' }}>
                            Todas as solicitações em andamento aparecerão aqui.
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Box>
          </Card>
        </Box>

        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 30%' }, display: 'flex', flexDirection: 'column', gap: 3, overflow: 'auto' }}>
          {/* Ações Rápidas */}
          <Card sx={{ borderRadius: 2, boxShadow: theme.shadows[2] }}>
            <CardHeader 
              title="Ações Rápidas" 
              titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }}
              avatar={
                <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main' }}>
                  <ShoppingCartIcon />
                </Avatar>
              }
            />
            <Divider />
            <CardContent>
              <Stack spacing={2}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  fullWidth 
                  startIcon={<ShoppingCartIcon />}
                  onClick={() => navigate('/suprimentos/processar')}
                >
                  Processar Requisições
                </Button>
                <Button 
                  variant="contained" 
                  color="warning" 
                  fullWidth 
                  startIcon={<ReceiptIcon />}
                  onClick={() => navigate('/suprimentos/cotacoes')}
                >
                  Gerenciar Cotações
                </Button>
                <Button 
                  variant="contained" 
                  color="info" 
                  fullWidth 
                  startIcon={<LocalShippingIcon />}
                  onClick={() => navigate('/suprimentos/pedidos')}
                >
                  Pedidos de Compras
                </Button>
              </Stack>
            </CardContent>
          </Card>

          {/* Estatísticas */}
          <Card sx={{ borderRadius: 2, boxShadow: theme.shadows[2], flex: 1, overflow: 'auto' }}>
            <CardHeader 
              title="Estatísticas" 
              titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }}
              avatar={
                <Avatar sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), color: 'info.main' }}>
                  <DonutLargeIcon />
                </Avatar>
              }
            />
            <Divider />
            <CardContent>
              <Typography variant="subtitle2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                <TrendingUpIcon sx={{ mr: 0.5, fontSize: 18, color: 'primary.main' }} /> Por Status
              </Typography>
              
              <Stack spacing={1.5} sx={{ mb: 3 }}>
                {Object.entries(contagemStatus).map(([k, v]) => {
                  const total = Object.values(contagemStatus).reduce((a, b) => a + b, 0);
                  const pct = total > 0 ? Math.round((v / total) * 100) : 0;
                  const statusColor = getStatusColor(k);
                  return (
                    <Box key={k}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                        <Stack direction="row" spacing={0.5} alignItems="center">
                          <Box 
                            sx={{ 
                              width: 8, 
                              height: 8, 
                              borderRadius: '50%', 
                              bgcolor: `${statusColor}.main`,
                              boxShadow: `0 0 0 2px ${alpha(theme.palette[statusColor].main, 0.2)}`
                            }} 
                          />
                          <Typography variant="body2" fontSize="0.8rem">{k}</Typography>
                        </Stack>
                        <Typography variant="body2" fontWeight="bold" fontSize="0.8rem">
                          {v} <Typography component="span" variant="caption" color="text.secondary" fontSize="0.7rem">({pct}%)</Typography>
                        </Typography>
                      </Stack>
                      <Box 
                        sx={{ 
                          mt: 0.5, 
                          bgcolor: alpha(theme.palette[statusColor].main, 0.1), 
                          height: 6, 
                          borderRadius: 3,
                          overflow: 'hidden'
                        }}
                      >
                        <Box 
                          sx={{ 
                            bgcolor: `${statusColor}.main`, 
                            width: `${pct}%`, 
                            height: 6,
                            borderRadius: 3,
                            transition: 'width 1s ease-in-out'
                          }} 
                        />
                      </Box>
                    </Box>
                  );
                })}
                {Object.values(contagemStatus).reduce((a, b) => a + b, 0) === 0 && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 1 }}>
                    <ShoppingCartIcon sx={{ fontSize: 24, color: 'text.secondary', opacity: 0.4, mb: 0.5 }} />
                    <Typography variant="caption" color="text.secondary" align="center">
                      Sem dados disponíveis
                    </Typography>
                  </Box>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
}
