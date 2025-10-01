import { useEffect, useState } from 'react';
import { Container, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Button, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { SolicitacoesAPI, type SolicitacaoListItem } from '../../services/solicitacoes';
import { useAppSelector } from '../../app/hooks';

export default function SolicitacoesListPage() {
  const [items, setItems] = useState<SolicitacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const perms = useAppSelector((s) => s.auth.profile?.permissions);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await SolicitacoesAPI.list();
        setItems(data);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <Container sx={{ mt: 4 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Solicitações</Typography>
        {Boolean(perms?.can_create_solicitation) && (
          <Button variant="contained" component={RouterLink} to="/solicitacoes/nova">
            Nova Solicitação
          </Button>
        )}
      </Stack>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Prioridade</TableCell>
              <TableCell>Data</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{row.numero_solicitacao_estoque}</TableCell>
                <TableCell>{row.descricao}</TableCell>
                <TableCell>{row.status_display || row.status}</TableCell>
                <TableCell>{row.prioridade_display || row.prioridade}</TableCell>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                <TableCell align="right">
                  <Button size="small" component={RouterLink} to={`/solicitacoes/${row.id}`}>
                    Detalhes
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!loading && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>Nenhuma solicitação encontrada.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>
    </Container>
  );
}
