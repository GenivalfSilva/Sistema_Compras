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
  Card,
  CardContent,
  CardHeader,
  Divider,
  Alert,
  AlertTitle,
  Chip,
  Tooltip,
  IconButton
} from '@mui/material';
import { SolicitacoesAPI, type SolicitacaoListItem } from '../../services/solicitacoes';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import ReceiptIcon from '@mui/icons-material/Receipt';

export default function ProcessarRequisicoesPage() {
  const [items, setItems] = useState<SolicitacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [obs, setObs] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const data = await SolicitacoesAPI.list();
      setItems(data.filter((r) => r.status === 'Suprimentos'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const mover = async (id: number) => {
    await SolicitacoesAPI.updateStatus(id, { novo_status: 'Em Cotação', observacoes: obs });
    setObs('');
    await load();
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
              <Typography variant="h4" fontWeight="bold">Processar Requisições</Typography>
              <Typography variant="subtitle1">
                Etapa 1: Análise inicial das solicitações recebidas do Estoque
              </Typography>
            </Box>
            <Tooltip title="Atualizar lista">
              <IconButton color="inherit" onClick={load} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>
      </Card>

      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>Sobre esta etapa</AlertTitle>
        <Typography variant="body2">
          Nesta etapa, você deve analisar as requisições recebidas do setor de Estoque e movê-las para a fase de cotação.
          Esta é a <strong>primeira etapa</strong> do processo de compras no departamento de Suprimentos.
        </Typography>
        <Box sx={{ mt: 1 }}>
          <Typography variant="subtitle2">Fluxo de trabalho:</Typography>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
            <Chip size="small" label="Estoque" variant="outlined" />
            <ArrowForwardIcon fontSize="small" />
            <Chip size="small" label="Suprimentos" color="primary" variant="filled" />
            <ArrowForwardIcon fontSize="small" />
            <Chip size="small" label="Em Cotação" variant="outlined" />
            <ArrowForwardIcon fontSize="small" />
            <Chip size="small" label="Pedido de Compras" variant="outlined" />
          </Stack>
        </Box>
      </Alert>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems="center" mb={2}>
        <TextField 
          size="small" 
          label="Observações" 
          value={obs} 
          onChange={(e) => setObs(e.target.value)} 
          placeholder="Adicione observações antes de mover para cotação"
          fullWidth
        />
      </Stack>

      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Table size="small" sx={{ tableLayout: 'fixed' }} stickyHeader>
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.50' }}>
              <TableCell>#</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell>Departamento</TableCell>
              <TableCell>Prioridade</TableCell>
              <TableCell>Data</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{row.numero_solicitacao_estoque}</TableCell>
                <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.descricao}
                </TableCell>
                <TableCell>{row.departamento}</TableCell>
                <TableCell>
                  <Chip 
                    size="small" 
                    label={row.prioridade} 
                    color={row.prioridade === 'Urgente' ? 'error' : row.prioridade === 'Alta' ? 'warning' : 'default'} 
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                <TableCell align="right">
                  <Button 
                    size="small" 
                    variant="contained" 
                    color="primary"
                    startIcon={<ArrowForwardIcon />}
                    onClick={() => mover(row.id)}
                  >
                    Enviar para Cotação
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!loading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
                    <ReceiptIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1 }} />
                    <Typography variant="body1" color="text.secondary" gutterBottom>
                      Nenhuma requisição para processar no momento.
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 400, textAlign: 'center' }}>
                      As requisições enviadas pelo setor de Estoque aparecerão aqui para serem processadas.
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
