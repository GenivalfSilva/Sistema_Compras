import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Button,
  Stack,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  InputAdornment,
  Snackbar,
  Alert,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Chip
} from '@mui/material';
import { SolicitacoesAPI, type SolicitacaoListItem, type Cotacao, type CotacaoPayload, type SolicitacaoDetail } from '../../services/solicitacoes';
import AddIcon from '@mui/icons-material/Add';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import RefreshIcon from '@mui/icons-material/Refresh';

interface CotacaoFormData {
  fornecedor: string;
  valor_unitario: number;
  valor_total: number;
  prazo_entrega: number;
  condicoes_pagamento: string;
  observacoes: string;
}

export default function CotacoesPage() {
  const [items, setItems] = useState<SolicitacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [obs, setObs] = useState('');
  
  // Estado para o diálogo de adicionar cotação
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedSolicitacao, setSelectedSolicitacao] = useState<SolicitacaoDetail | null>(null);
  const [cotacoes, setCotacoes] = useState<Cotacao[]>([]);
  const [loadingCotacoes, setLoadingCotacoes] = useState(false);
  
  // Estado para o formulário de cotação
  const [formData, setFormData] = useState<CotacaoFormData>({
    fornecedor: '',
    valor_unitario: 0,
    valor_total: 0,
    prazo_entrega: 5,
    condicoes_pagamento: 'À vista',
    observacoes: ''
  });
  
  // Estado para notificações
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info' | 'warning'
  });

  const load = async () => {
    setLoading(true);
    try {
      const data = await SolicitacoesAPI.list();
      setItems(data.filter((r) => r.status === 'Em Cotação'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const moverParaPedido = async (id: number) => {
    await SolicitacoesAPI.updateStatus(id, { novo_status: 'Pedido de Compras', observacoes: obs });
    setSnackbar({
      open: true,
      message: 'Solicitação movida para Pedido de Compras com sucesso!',
      severity: 'success'
    });
    setObs('');
    await load();
  };
  
  const handleOpenDialog = async (solicitacaoId: number) => {
    setLoadingCotacoes(true);
    try {
      const solicitacao = await SolicitacoesAPI.get(solicitacaoId);
      setSelectedSolicitacao(solicitacao);
      
      // Carregar cotações existentes
      const cotacoesData = await SolicitacoesAPI.getCotacoes(solicitacaoId);
      setCotacoes(cotacoesData);
      
      // Calcular valor total inicial baseado no valor unitário
      const quantidade = solicitacao.itens && solicitacao.itens.length > 0 ? 
        solicitacao.itens[0].quantidade || 1 : 1;
      
      setFormData(prev => ({
        ...prev,
        valor_total: prev.valor_unitario * quantidade
      }));
      
      setDialogOpen(true);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      setSnackbar({
        open: true,
        message: 'Erro ao carregar dados da solicitação',
        severity: 'error'
      });
    } finally {
      setLoadingCotacoes(false);
    }
  };
  
  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedSolicitacao(null);
    setCotacoes([]);
    setFormData({
      fornecedor: '',
      valor_unitario: 0,
      valor_total: 0,
      prazo_entrega: 5,
      condicoes_pagamento: 'À vista',
      observacoes: ''
    });
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'valor_unitario' && selectedSolicitacao?.itens?.length) {
      const quantidade = selectedSolicitacao.itens[0].quantidade || 1;
      const valorUnitario = parseFloat(value) || 0;
      
      setFormData({
        ...formData,
        [name]: valorUnitario,
        valor_total: valorUnitario * quantidade
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };
  
  const handleSelectChange = (e: any) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  const handleAddCotacao = async () => {
    if (!selectedSolicitacao) return;
    
    if (!formData.fornecedor || formData.valor_unitario <= 0) {
      setSnackbar({
        open: true,
        message: 'Por favor, preencha o fornecedor e valor unitário',
        severity: 'error'
      });
      return;
    }
    
    try {
      const payload: CotacaoPayload = {
        fornecedor: formData.fornecedor,
        valor_unitario: formData.valor_unitario,
        valor_total: formData.valor_total,
        prazo_entrega: formData.prazo_entrega,
        condicoes_pagamento: formData.condicoes_pagamento,
        observacoes: formData.observacoes
      };
      
      await SolicitacoesAPI.addCotacao(selectedSolicitacao.id, payload);
      
      // Recarregar cotações
      const cotacoesData = await SolicitacoesAPI.getCotacoes(selectedSolicitacao.id);
      setCotacoes(cotacoesData);
      
      // Limpar formulário
      setFormData({
        fornecedor: '',
        valor_unitario: 0,
        valor_total: 0,
        prazo_entrega: 5,
        condicoes_pagamento: 'À vista',
        observacoes: ''
      });
      
      setSnackbar({
        open: true,
        message: 'Cotação adicionada com sucesso!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Erro ao adicionar cotação:', error);
      setSnackbar({
        open: true,
        message: 'Erro ao adicionar cotação',
        severity: 'error'
      });
    }
  };
  
  const handleSelectCotacao = async (cotacaoId: number) => {
    if (!selectedSolicitacao) return;
    
    try {
      await SolicitacoesAPI.selectCotacao(selectedSolicitacao.id, cotacaoId);
      
      // Recarregar cotações
      const cotacoesData = await SolicitacoesAPI.getCotacoes(selectedSolicitacao.id);
      setCotacoes(cotacoesData);
      
      setSnackbar({
        open: true,
        message: 'Cotação selecionada com sucesso!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Erro ao selecionar cotação:', error);
      setSnackbar({
        open: true,
        message: 'Erro ao selecionar cotação',
        severity: 'error'
      });
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', pt: 1 }}>
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
              <Typography variant="h4" fontWeight="bold">Cotações</Typography>
              <Typography variant="subtitle1">Gerencie as cotações de fornecedores</Typography>
            </Box>
            <Tooltip title="Atualizar lista">
              <IconButton color="inherit" onClick={load} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>
      </Card>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems="center" mb={2}>
        <TextField size="small" label="Observações" value={obs} onChange={(e) => setObs(e.target.value)} />
      </Stack>
      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Table size="small" sx={{ tableLayout: 'fixed' }} stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Data</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{row.numero_solicitacao_estoque}</TableCell>
                <TableCell>{row.descricao}</TableCell>
                <TableCell>{row.status}</TableCell>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Tooltip title="Adicionar Cotação">
                      <Button 
                        size="small" 
                        variant="outlined" 
                        color="primary"
                        startIcon={<AddIcon />}
                        onClick={() => handleOpenDialog(row.id)}
                      >
                        Cotação
                      </Button>
                    </Tooltip>
                    <Button 
                      size="small" 
                      variant="contained" 
                      color="primary"
                      startIcon={<ShoppingCartIcon />}
                      onClick={() => moverParaPedido(row.id)}
                    >
                      Criar Pedido
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!loading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
                    <ShoppingCartIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1 }} />
                    <Typography variant="body1" color="text.secondary" gutterBottom>
                      Nenhuma solicitação em cotação.
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 300, textAlign: 'center' }}>
                      As solicitações em cotação aparecerão aqui.
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>
      
      {/* Diálogo para adicionar cotação */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          Gerenciar Cotações - Solicitação #{selectedSolicitacao?.numero_solicitacao_estoque}
        </DialogTitle>
        <DialogContent dividers>
          {loadingCotacoes ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <Typography>Carregando...</Typography>
            </Box>
          ) : (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardHeader title="Detalhes da Solicitação" />
                    <Divider />
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary">Descrição</Typography>
                      <Typography variant="body1" paragraph>{selectedSolicitacao?.descricao}</Typography>
                      
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="subtitle2" color="text.secondary">Departamento</Typography>
                          <Typography variant="body1">{selectedSolicitacao?.departamento}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="subtitle2" color="text.secondary">Prioridade</Typography>
                          <Typography variant="body1">{selectedSolicitacao?.prioridade}</Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardHeader title="Itens Solicitados" />
                    <Divider />
                    <CardContent sx={{ p: 0 }}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Item</TableCell>
                            <TableCell>Quantidade</TableCell>
                            <TableCell>Unidade</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {selectedSolicitacao?.itens && selectedSolicitacao.itens.length > 0 ? (
                            selectedSolicitacao.itens.map((item: any, index: number) => (
                              <TableRow key={index}>
                                <TableCell>{item.nome || item.codigo || `Item ${index + 1}`}</TableCell>
                                <TableCell>{item.quantidade}</TableCell>
                                <TableCell>{item.unidade}</TableCell>
                              </TableRow>
                            ))
                          ) : (
                            <TableRow>
                              <TableCell colSpan={3} align="center">Nenhum item registrado</TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
              
              <Card variant="outlined" sx={{ mb: 3 }}>
                <CardHeader 
                  title="Adicionar Nova Cotação" 
                  titleTypographyProps={{ variant: 'h6' }}
                />
                <Divider />
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Fornecedor"
                        name="fornecedor"
                        value={formData.fornecedor}
                        onChange={handleInputChange}
                        required
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Condições de Pagamento</InputLabel>
                        <Select
                          name="condicoes_pagamento"
                          value={formData.condicoes_pagamento}
                          onChange={handleSelectChange}
                          label="Condições de Pagamento"
                        >
                          <MenuItem value="À vista">À vista</MenuItem>
                          <MenuItem value="30 dias">30 dias</MenuItem>
                          <MenuItem value="60 dias">60 dias</MenuItem>
                          <MenuItem value="90 dias">90 dias</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Valor Unitário"
                        name="valor_unitario"
                        type="number"
                        value={formData.valor_unitario}
                        onChange={handleInputChange}
                        InputProps={{
                          startAdornment: <InputAdornment position="start">R$</InputAdornment>,
                        }}
                        required
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Valor Total"
                        name="valor_total"
                        type="number"
                        value={formData.valor_total}
                        onChange={handleInputChange}
                        InputProps={{
                          startAdornment: <InputAdornment position="start">R$</InputAdornment>,
                        }}
                        required
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Prazo de Entrega (dias)"
                        name="prazo_entrega"
                        type="number"
                        value={formData.prazo_entrega}
                        onChange={handleInputChange}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Observações"
                        name="observacoes"
                        value={formData.observacoes}
                        onChange={handleInputChange}
                        multiline
                        rows={2}
                      />
                    </Grid>
                    <Grid item xs={12} sx={{ textAlign: 'right' }}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleAddCotacao}
                        startIcon={<AddIcon />}
                      >
                        Adicionar Cotação
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
              
              <Card variant="outlined">
                <CardHeader 
                  title="Cotações Registradas" 
                  titleTypographyProps={{ variant: 'h6' }}
                  action={
                    <Tooltip title="Comparar Cotações">
                      <IconButton>
                        <CompareArrowsIcon />
                      </IconButton>
                    </Tooltip>
                  }
                />
                <Divider />
                <CardContent sx={{ p: 0 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Fornecedor</TableCell>
                        <TableCell>Valor Unit.</TableCell>
                        <TableCell>Valor Total</TableCell>
                        <TableCell>Prazo</TableCell>
                        <TableCell>Pagamento</TableCell>
                        <TableCell align="right">Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {cotacoes.length > 0 ? (
                        cotacoes.map((cotacao) => (
                          <TableRow key={cotacao.id} selected={cotacao.selecionada}>
                            <TableCell>{cotacao.fornecedor}</TableCell>
                            <TableCell>R$ {cotacao.valor_unitario.toFixed(2)}</TableCell>
                            <TableCell>R$ {cotacao.valor_total.toFixed(2)}</TableCell>
                            <TableCell>{cotacao.prazo_entrega} dias</TableCell>
                            <TableCell>{cotacao.condicoes_pagamento}</TableCell>
                            <TableCell align="right">
                              {cotacao.selecionada ? (
                                <Chip 
                                  size="small" 
                                  color="success" 
                                  icon={<CheckCircleIcon />} 
                                  label="Selecionada" 
                                />
                              ) : (
                                <Button 
                                  size="small" 
                                  variant="outlined" 
                                  onClick={() => handleSelectCotacao(cotacao.id!)}
                                >
                                  Selecionar
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={6} align="center">
                            Nenhuma cotação registrada
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Fechar</Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar para notificações */}
      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={4000} 
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
