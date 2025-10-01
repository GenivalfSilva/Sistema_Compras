import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Button, Stack, TextField } from '@mui/material';
import { SolicitacoesAPI, type SolicitacaoListItem } from '../../services/solicitacoes';

export default function CotacoesPage() {
  const [items, setItems] = useState<SolicitacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [obs, setObs] = useState('');

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
    setObs('');
    await load();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Cotações (Suprimentos)
      </Typography>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems="center" mb={2}>
        <TextField size="small" label="Observações" value={obs} onChange={(e) => setObs(e.target.value)} />
        <Button variant="outlined" onClick={load} disabled={loading}>Atualizar</Button>
      </Stack>
      <Paper>
        <Table size="small">
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
                  <Button size="small" variant="contained" onClick={() => moverParaPedido(row.id)}>Criar Pedido</Button>
                </TableCell>
              </TableRow>
            ))}
            {!loading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>Nenhuma solicitação em cotação.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
