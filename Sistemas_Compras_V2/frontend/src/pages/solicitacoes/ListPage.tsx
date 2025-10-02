import { useEffect, useState } from 'react';
import { 
  Typography, 
  Table, 
  TableHead, 
  TableRow, 
  TableCell, 
  TableBody, 
  Button, 
  Stack, 
  Card, 
  CardHeader, 
  Divider, 
  Box, 
  Chip, 
  IconButton, 
  Tooltip, 
  TextField, 
  InputAdornment,
  LinearProgress,
  Alert,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Skeleton
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { SolicitacoesAPI, type SolicitacaoListItem } from '../../services/solicitacoes';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { fetchProfile } from '../../features/auth/authSlice';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import VisibilityIcon from '@mui/icons-material/Visibility';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';

export default function SolicitacoesListPage() {
  const [items, setItems] = useState<SolicitacaoListItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<SolicitacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('todos');
  const [prioridadeFilter, setPrioridadeFilter] = useState('todas');
  
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const profile = useAppSelector((s) => s.auth.profile);
  const perms = profile?.permissions;
  const token = useAppSelector((s) => s.auth.tokens?.access) || localStorage.getItem('access');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await SolicitacoesAPI.list();
      setItems(data);
      setFilteredItems(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Erro ao carregar solicitações');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    load();
  }, []);

  // Garante que o perfil seja carregado para exibir corretamente o botão "Nova Solicitação"
  useEffect(() => {
    if (!profile && token) {
      dispatch(fetchProfile());
    }
  }, [dispatch, profile, token]);
  
  // Filtra os itens quando os filtros mudam
  useEffect(() => {
    let result = [...items];
    
    // Filtro por texto de busca
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(item => 
        item.descricao.toLowerCase().includes(term) ||
        String(item.numero_solicitacao_estoque).includes(term)
      );
    }
    
    // Filtro por status
    if (statusFilter !== 'todos') {
      result = result.filter(item => 
        (item.status_display || item.status).toLowerCase() === statusFilter.toLowerCase()
      );
    }
    
    // Filtro por prioridade
    if (prioridadeFilter !== 'todas') {
      result = result.filter(item => 
        (item.prioridade_display || item.prioridade).toLowerCase() === prioridadeFilter.toLowerCase()
      );
    }
    
    setFilteredItems(result);
  }, [items, searchTerm, statusFilter, prioridadeFilter]);
  
  // Helper function to get status color
  const getStatusColor = (status: string) => {
    const statusMap: Record<string, string> = {
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
    return statusMap[status] || 'default';
  };

  // Helper function to get priority color
  const getPriorityColor = (priority: string) => {
    const priorityMap: Record<string, string> = {
      'Urgente': 'error',
      'Alta': 'warning',
      'Normal': 'info',
      'Baixa': 'success'
    };
    return priorityMap[priority] || 'default';
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
  
  // Extrai status únicos para o filtro
  const uniqueStatuses = ['todos', ...Array.from(new Set(items.map(item => (item.status_display || item.status).toLowerCase())))];
  
  // Extrai prioridades únicas para o filtro
  const uniquePrioridades = ['todas', ...Array.from(new Set(items.map(item => (item.prioridade_display || item.prioridade).toLowerCase())))];

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Card sx={{ mb: 3, borderRadius: 2, overflow: 'hidden' }}>
        <Box 
          sx={{ 
            p: 3, 
            background: 'linear-gradient(45deg, #d91a2a 30%, #e14554 90%)',
            color: 'white'
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h4" fontWeight="bold">Solicitações</Typography>
              <Typography variant="subtitle1">Gerencie suas solicitações de compras</Typography>
            </Box>
            {Boolean(perms?.can_create_solicitation) && (
              <Button 
                variant="contained" 
                color="secondary" 
                component={RouterLink} 
                to="/solicitacoes/nova"
                startIcon={<AddCircleOutlineIcon />}
                sx={{ fontWeight: 'bold' }}
              >
                Nova Solicitação
              </Button>
            )}
          </Stack>
        </Box>
        
        {loading && <LinearProgress />}
        
        {error && (
          <Alert severity="error" sx={{ mx: 2, mt: 2 }}>{error}</Alert>
        )}
        
        <Box sx={{ p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
            <TextField
              placeholder="Buscar solicitações..."
              variant="outlined"
              size="small"
              fullWidth
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                labelId="status-filter-label"
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                {uniqueStatuses.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status === 'todos' ? 'Todos os Status' : status.charAt(0).toUpperCase() + status.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel id="prioridade-filter-label">Prioridade</InputLabel>
              <Select
                labelId="prioridade-filter-label"
                value={prioridadeFilter}
                label="Prioridade"
                onChange={(e) => setPrioridadeFilter(e.target.value)}
              >
                {uniquePrioridades.map((prioridade) => (
                  <MenuItem key={prioridade} value={prioridade}>
                    {prioridade === 'todas' ? 'Todas as Prioridades' : prioridade.charAt(0).toUpperCase() + prioridade.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Tooltip title="Atualizar">
              <IconButton onClick={load} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>
      </Card>

      <Card sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <CardHeader 
          title={`Solicitações (${filteredItems.length})`}
          titleTypographyProps={{ variant: 'h6' }}
        />
        <Divider />
        <Box sx={{ overflowX: 'auto' }}>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.50' }}>
                <TableCell>#</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Prioridade</TableCell>
                <TableCell>Data</TableCell>
                <TableCell align="right">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={`skeleton-${i}`}>
                  <TableCell><Skeleton width={60} /></TableCell>
                  <TableCell><Skeleton width={240} /></TableCell>
                  <TableCell><Skeleton width={120} /></TableCell>
                  <TableCell><Skeleton width={100} /></TableCell>
                  <TableCell><Skeleton width={160} /></TableCell>
                  <TableCell align="right"><Skeleton width={80} /></TableCell>
                </TableRow>
              ))}
              {!loading && filteredItems.map((row) => (
                <TableRow key={row.id} hover>
                  <TableCell>{row.numero_solicitacao_estoque || '-'}</TableCell>
                  <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row.descricao}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      size="small" 
                      label={row.status_display || row.status} 
                      color={getStatusColor(row.status_display || row.status) as any}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      size="small" 
                      label={row.prioridade_display || row.prioridade} 
                      color={getPriorityColor(row.prioridade_display || row.prioridade) as any}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{formatDate(row.created_at)}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Ver detalhes">
                      <IconButton 
                        size="small" 
                        color="primary" 
                        onClick={() => navigate(`/solicitacoes/${row.id}`)}
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {!loading && filteredItems.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Nenhuma solicitação encontrada.
                    </Typography>
                    {Boolean(perms?.can_create_solicitation) && (
                      <Button 
                        variant="outlined" 
                        startIcon={<AddCircleOutlineIcon />} 
                        sx={{ mt: 1 }}
                        component={RouterLink}
                        to="/solicitacoes/nova"
                      >
                        Criar Nova Solicitação
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Box>
      </Card>
    </Box>
  );
}
