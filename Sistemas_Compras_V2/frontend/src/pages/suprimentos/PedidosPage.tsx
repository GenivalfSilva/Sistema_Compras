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
  IconButton,
  Tooltip
} from '@mui/material';
import { SolicitacoesAPI, type SolicitacaoListItem } from '../../services/solicitacoes';
import RefreshIcon from '@mui/icons-material/Refresh';
import SendIcon from '@mui/icons-material/Send';

export default function PedidosPage() {
  const [items, setItems] = useState<SolicitacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [obs, setObs] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const data = await SolicitacoesAPI.list();
      setItems(data.filter((r) => r.status === 'Pedido de Compras'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const enviarAprovacao = async (id: number) => {
    await SolicitacoesAPI.updateStatus(id, { novo_status: 'Aguardando Aprovação', observacoes: obs });
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
              <Typography variant="h4" fontWeight="bold">Pedidos de Compras</Typography>
              <Typography variant="subtitle1">Gerencie os pedidos e envie para aprovação</Typography>
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
        <TextField size="small" label="Observações" value={obs} onChange={(e) => setObs(e.target.value)} fullWidth />
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
                  <Button 
                    size="small" 
                    variant="contained" 
                    color="primary"
                    startIcon={<SendIcon />}
                    onClick={() => enviarAprovacao(row.id)}
                  >
                    Enviar para Aprovação
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!loading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>Nenhum pedido aguardando envio para aprovação.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
