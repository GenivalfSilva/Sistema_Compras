import { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Stack, 
  Button, 
  Table, 
  TableHead, 
  TableRow, 
  TableCell, 
  TableBody, 
  Alert, 
  Skeleton, 
  Divider, 
  Card, 
  CardContent, 
  CardHeader, 
  IconButton, 
  Chip, 
  Tooltip,
  LinearProgress,
  Badge,
  Avatar,
  AvatarGroup,
  Paper,
  useTheme,
  alpha,
  CircularProgress
} from '@mui/material';
import { SolicitacoesAPI, type SolicitacoesDashboard, type SolicitacaoListItem } from '../../services/solicitacoes';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../app/hooks';
// Ícones
import RefreshIcon from '@mui/icons-material/Refresh';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import VisibilityIcon from '@mui/icons-material/Visibility';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import AssignmentIcon from '@mui/icons-material/Assignment';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import DescriptionIcon from '@mui/icons-material/Description';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import DonutLargeIcon from '@mui/icons-material/DonutLarge';

export default function DashboardSolicitante() {
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

  const resumo = data?.resumo;
  const sla = data?.sla;
  const recentes: SolicitacaoListItem[] = data?.solicitacoes_recentes || [];
  const porStatus = data?.por_status || {};
  const porPrioridade = data?.por_prioridade || {};
  const maxStatus = Math.max(1, ...Object.values(porStatus));
  const maxPrioridade = Math.max(1, ...Object.values(porPrioridade));

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

  // Helper function to get priority color
  const getPriorityColor = (priority: string): MuiColor => {
    const priorityMap: Record<string, MuiColor> = {
      'Urgente': 'error',
      'Alta': 'warning',
      'Normal': 'info',
      'Baixa': 'success'
    };
    return priorityMap[priority] || 'secondary';
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
                    Meu Painel
                  </Typography>
                  <Typography variant="subtitle1">
                    Bem-vindo, {profile?.username || 'Usuário'} | {profile?.perfil || 'Solicitante'}
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" sx={{ mt: 1, maxWidth: 500, opacity: 0.9 }}>
                Acompanhe suas solicitações, verifique prazos e crie novas requisições de compras.
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Atualizar dados">
                <IconButton 
                  onClick={load} 
                  disabled={loading} 
                  sx={{ 
                    color: 'white',
                    bgcolor: alpha(theme.palette.common.white, 0.1),
                    '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.2) }
                  }}
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Button 
                variant="contained" 
                color="secondary" 
                startIcon={<AddCircleOutlineIcon />}
                onClick={() => navigate('/solicitacoes/nova')}
                sx={{ 
                  fontWeight: 'bold',
                  boxShadow: theme.shadows[5],
                  '&:hover': { boxShadow: theme.shadows[8] }
                }}
              >
                Nova Solicitação
              </Button>
            </Stack>
          </Stack>
        </Box>

        {loading && <LinearProgress color="secondary" />}

        {error && (
          <Alert severity="error" sx={{ mx: 2, mt: 2 }} variant="filled">{error}</Alert>
        )}
      </Card>

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3, flex: 1, overflow: 'auto' }}>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 70%' } }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
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
                    <AssignmentIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Total</Typography>
                </Stack>
                {loading ? <Skeleton width={40} height={40} /> : (
                  <Typography variant="h4" fontWeight="bold">{resumo?.total ?? '0'}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Solicitações</Typography>
                  {resumo?.total && resumo.total > 0 && (
                    <Chip size="small" label="Ativas" color="info" variant="outlined" sx={{ height: 18, fontSize: '0.7rem' }} />
                  )}
                </Stack>
              </CardContent>
            </Card>
            
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
                    <PendingIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Pendentes</Typography>
                </Stack>
                {loading ? <Skeleton width={40} height={40} /> : (
                  <Typography variant="h4" fontWeight="bold" color="warning.main">{resumo?.pendentes ?? '0'}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Em andamento</Typography>
                  {resumo?.pendentes && resumo.pendentes > 0 && (
                    <Chip size="small" label="Aguardando" color="warning" variant="outlined" sx={{ height: 18, fontSize: '0.7rem' }} />
                  )}
                </Stack>
              </CardContent>
            </Card>
            
            <Card sx={{ 
              height: '100%', 
              borderRadius: 2,
              boxShadow: theme.shadows[2],
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] },
              position: 'relative',
              overflow: 'hidden'
            }}>
              <Box sx={{ position: 'absolute', top: 0, left: 0, width: 4, height: '100%', bgcolor: 'success.main' }} />
              <CardContent sx={{ p: 2, pb: '16px !important' }}>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Avatar sx={{ bgcolor: alpha(theme.palette.success.main, 0.1), color: 'success.main' }}>
                    <CheckCircleIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Aprovadas</Typography>
                </Stack>
                {loading ? <Skeleton width={40} height={40} /> : (
                  <Typography variant="h4" fontWeight="bold" color="success.main">{resumo?.aprovadas ?? '0'}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Confirmadas</Typography>
                  {resumo?.aprovadas && resumo.aprovadas > 0 && (
                    <Chip size="small" label="Aprovado" color="success" variant="outlined" sx={{ height: 18, fontSize: '0.7rem' }} />
                  )}
                </Stack>
              </CardContent>
            </Card>
            
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
                    <DoneAllIcon />
                  </Avatar>
                  <Typography variant="subtitle2" color="text.secondary">Finalizadas</Typography>
                </Stack>
                {loading ? <Skeleton width={40} height={40} /> : (
                  <Typography variant="h4" fontWeight="bold" color="primary.main">{resumo?.finalizadas ?? '0'}</Typography>
                )}
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">Concluídas</Typography>
                  {resumo?.finalizadas && resumo.finalizadas > 0 && (
                    <Chip size="small" label="Entregue" color="primary" variant="outlined" sx={{ height: 18, fontSize: '0.7rem' }} />
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Box>

          <Card sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: theme.shadows[2] }}>
            <CardHeader 
              title="Solicitações Recentes" 
              titleTypographyProps={{ fontWeight: 'bold' }}
              avatar={
                <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main' }}>
                  <DescriptionIcon />
                </Avatar>
              }
              action={
                <Button 
                  variant="outlined" 
                  color="primary"
                  size="small"
                  onClick={() => navigate('/solicitacoes')}
                  endIcon={<VisibilityIcon />}
                  sx={{ borderRadius: 20 }}
                >
                  Ver todas
                </Button>
              }
            />
            <Divider />
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="medium">
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
                      <TableCell><Skeleton variant="text" width={160} /></TableCell>
                      <TableCell><Skeleton variant="text" width={60} /></TableCell>
                      <TableCell><Skeleton variant="text" width={240} /></TableCell>
                      <TableCell><Skeleton variant="rounded" width={120} height={24} /></TableCell>
                      <TableCell><Skeleton variant="rounded" width={100} height={24} /></TableCell>
                      <TableCell align="right"><Skeleton variant="circular" width={32} height={32} /></TableCell>
                    </TableRow>
                  ))}
                  {!loading && recentes.map((row) => (
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
                            boxShadow: `0 0 0 2px ${alpha(theme.palette[getStatusColor(row.status_display || row.status) as 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success'].main, 0.2)}`
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
                        <Tooltip title={row.descricao} enterDelay={500}>
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
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small" 
                          label={row.status_display || row.status} 
                          color={getStatusColor(row.status_display || row.status) as any}
                          variant="outlined"
                          sx={{ 
                            fontWeight: 500,
                            '& .MuiChip-label': { px: 1 }
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small" 
                          label={row.prioridade_display || row.prioridade} 
                          color={getPriorityColor(row.prioridade_display || row.prioridade) as any}
                          variant="outlined"
                          sx={{ 
                            fontWeight: 500,
                            '& .MuiChip-label': { px: 1 }
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Ver detalhes">
                          <IconButton 
                            size="small" 
                            color="primary" 
                            sx={{ 
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.2) }
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/solicitacoes/${row.id}`);
                            }}
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!loading && recentes.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
                          <DescriptionIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1 }} />
                          <Typography variant="body1" color="text.secondary" gutterBottom>
                            Nenhuma solicitação encontrada.
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 300, textAlign: 'center' }}>
                            Crie uma nova solicitação para iniciar o processo de compras.
                          </Typography>
                          <Button 
                            variant="contained" 
                            color="primary"
                            startIcon={<AddCircleOutlineIcon />} 
                            onClick={() => navigate('/solicitacoes/nova')}
                          >
                            Criar Nova Solicitação
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Box>
            {!loading && recentes.length > 0 && (
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                <Button 
                  variant="outlined" 
                  color="primary"
                  size="small"
                  startIcon={<AddCircleOutlineIcon />}
                  onClick={() => navigate('/solicitacoes/nova')}
                  sx={{ borderRadius: 20 }}
                >
                  Nova Solicitação
                </Button>
              </Box>
            )}
          </Card>
        </Box>

        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 30%' } }}>
          {/* Seção de Resumo de SLA e Distribuição em um layout mais compacto */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Resumo de SLA */}
            <Card sx={{ borderRadius: 2, boxShadow: theme.shadows[2] }}>
              <CardHeader 
                title="Resumo de SLA" 
                titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }}
                avatar={
                  <Avatar sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), color: 'info.main' }}>
                    <AccessTimeIcon />
                  </Avatar>
                }
              />
              <Divider />
              <CardContent sx={{ p: 2 }}>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'error.main', width: 32, height: 32, mr: 1.5 }}>
                        <ErrorIcon fontSize="small" />
                      </Avatar>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">Vencidas</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Prazo expirado
                        </Typography>
                      </Box>
                    </Box>
                    <Badge 
                      badgeContent={sla?.vencidas ?? 0} 
                      color="error" 
                      sx={{ 
                        '& .MuiBadge-badge': {
                          fontWeight: 'bold',
                          minWidth: 20,
                          height: 20
                        }
                      }}
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'warning.main', width: 32, height: 32, mr: 1.5 }}>
                        <PendingIcon fontSize="small" />
                      </Avatar>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">Próximo Vencimento</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Próximas do prazo
                        </Typography>
                      </Box>
                    </Box>
                    <Badge 
                      badgeContent={sla?.proximo_vencimento ?? 0} 
                      color="warning" 
                      sx={{ 
                        '& .MuiBadge-badge': {
                          fontWeight: 'bold',
                          minWidth: 20,
                          height: 20
                        }
                      }}
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'success.main', width: 32, height: 32, mr: 1.5 }}>
                        <CheckCircleIcon fontSize="small" />
                      </Avatar>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">OK</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Dentro do prazo
                        </Typography>
                      </Box>
                    </Box>
                    <Badge 
                      badgeContent={sla?.ok ?? 0} 
                      color="success" 
                      sx={{ 
                        '& .MuiBadge-badge': {
                          fontWeight: 'bold',
                          minWidth: 20,
                          height: 20
                        }
                      }}
                    />
                  </Box>
                  
                  <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center' }}>
                    <CircularProgress 
                      variant="determinate" 
                      value={sla ? ((sla.ok || 0) / Math.max(1, (sla.ok || 0) + (sla.proximo_vencimento || 0) + (sla.vencidas || 0))) * 100 : 0} 
                      size={60}
                      thickness={8}
                      color="success"
                      sx={{ m: 1 }}
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Distribuição */}
            <Card sx={{ borderRadius: 2, boxShadow: theme.shadows[2] }}>
              <CardHeader 
                title="Distribuição" 
                titleTypographyProps={{ variant: 'h6', fontWeight: 'bold' }}
                avatar={
                  <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main' }}>
                    <DonutLargeIcon />
                  </Avatar>
                }
              />
              <Divider />
              <CardContent sx={{ p: 2 }}>
                {/* Por Status */}
                <Typography variant="subtitle2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                  <TrendingUpIcon sx={{ mr: 0.5, fontSize: 18, color: 'primary.main' }} /> Por Status
                </Typography>
                
                <Stack spacing={1.5} sx={{ mb: 3 }}>
                  {Object.entries(porStatus).map(([k, v]) => {
                    const pct = Math.round((v / maxStatus) * 100);
                    const statusColor = getStatusColor(k) as 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
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
                  {Object.keys(porStatus).length === 0 && (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 1 }}>
                      <ShoppingCartIcon sx={{ fontSize: 24, color: 'text.secondary', opacity: 0.4, mb: 0.5 }} />
                      <Typography variant="caption" color="text.secondary" align="center">
                        Sem dados disponíveis
                      </Typography>
                    </Box>
                  )}
                </Stack>

                {/* Por Prioridade */}
                <Typography variant="subtitle2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                  <PriorityHighIcon sx={{ mr: 0.5, fontSize: 18, color: 'secondary.main' }} /> Por Prioridade
                </Typography>
                
                <Stack spacing={1.5}>
                  {Object.entries(porPrioridade).map(([k, v]) => {
                    const pct = Math.round((v / maxPrioridade) * 100);
                    const priorityColor = getPriorityColor(k) as 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
                    return (
                      <Box key={k}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                          <Stack direction="row" spacing={0.5} alignItems="center">
                            <Box 
                              sx={{ 
                                width: 8, 
                                height: 8, 
                                borderRadius: '50%', 
                                bgcolor: `${priorityColor}.main`,
                                boxShadow: `0 0 0 2px ${alpha(theme.palette[priorityColor].main, 0.2)}`
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
                            bgcolor: alpha(theme.palette[priorityColor].main, 0.1), 
                            height: 6, 
                            borderRadius: 3,
                            overflow: 'hidden'
                          }}
                        >
                          <Box 
                            sx={{ 
                              bgcolor: `${priorityColor}.main`, 
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
                  {Object.keys(porPrioridade).length === 0 && (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 1 }}>
                      <LocalShippingIcon sx={{ fontSize: 24, color: 'text.secondary', opacity: 0.4, mb: 0.5 }} />
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
    </Box>
  );
}
