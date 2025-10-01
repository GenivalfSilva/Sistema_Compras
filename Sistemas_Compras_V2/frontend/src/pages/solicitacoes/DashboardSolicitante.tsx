import { useEffect, useState } from 'react';
import { Box, Paper, Typography, Stack, Button, Table, TableHead, TableRow, TableCell, TableBody, Alert, Skeleton, Divider } from '@mui/material';
import { SolicitacoesAPI, type SolicitacoesDashboard, type SolicitacaoListItem } from '../../services/solicitacoes';
import { useNavigate } from 'react-router-dom';

export default function DashboardSolicitante() {
  const [data, setData] = useState<SolicitacoesDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

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

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Meu Painel</Typography>
        <Button onClick={load} disabled={loading} variant="outlined">Atualizar</Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 2 }}>
        <Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">Total</Typography>
              {loading ? <Skeleton width={40} /> : (
                <Typography variant="h5">{resumo?.total ?? '-'}</Typography>
              )}
            </Paper>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">Pendentes</Typography>
              {loading ? <Skeleton width={40} /> : (
                <Typography variant="h5">{resumo?.pendentes ?? '-'}</Typography>
              )}
            </Paper>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">Aprovadas</Typography>
              {loading ? <Skeleton width={40} /> : (
                <Typography variant="h5">{resumo?.aprovadas ?? '-'}</Typography>
              )}
            </Paper>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">Finalizadas</Typography>
              {loading ? <Skeleton width={40} /> : (
                <Typography variant="h5">{resumo?.finalizadas ?? '-'}</Typography>
              )}
            </Paper>
          </Box>

          <Paper sx={{ mt: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>#</TableCell>
                  <TableCell>Descrição</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Prioridade</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading && Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={`skeleton-${i}`}>
                    <TableCell><Skeleton width={160} /></TableCell>
                    <TableCell><Skeleton width={60} /></TableCell>
                    <TableCell><Skeleton width={240} /></TableCell>
                    <TableCell><Skeleton width={120} /></TableCell>
                    <TableCell><Skeleton width={100} /></TableCell>
                  </TableRow>
                ))}
                {!loading && recentes.map((row) => (
                  <TableRow key={row.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/solicitacoes/${row.id}`)}>
                    <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                    <TableCell>{row.numero_solicitacao_estoque}</TableCell>
                    <TableCell>{row.descricao}</TableCell>
                    <TableCell>{row.status_display || row.status}</TableCell>
                    <TableCell>{row.prioridade_display || row.prioridade}</TableCell>
                  </TableRow>
                ))}
                {!loading && recentes.length === 0 && (
                  <TableRow><TableCell colSpan={5}>Sem solicitações recentes.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        </Box>

        <Box>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Resumo de SLA</Typography>
            <Stack spacing={1}>
              <Box>
                <Typography variant="body2" color="text.secondary">Vencidas</Typography>
                <Typography variant="h6">{sla?.vencidas ?? '-'}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Próximo Vencimento</Typography>
                <Typography variant="h6">{sla?.proximo_vencimento ?? '-'}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">OK</Typography>
                <Typography variant="h6">{sla?.ok ?? '-'}</Typography>
              </Box>
            </Stack>
          </Paper>

          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Por Status</Typography>
            <Stack spacing={1}>
              {Object.entries(porStatus).map(([k, v]) => {
                const pct = Math.round((v / maxStatus) * 100);
                return (
                  <Box key={k}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="caption" color="text.secondary">{k}</Typography>
                      <Typography variant="caption" color="text.secondary">{v}</Typography>
                    </Stack>
                    <Box sx={{ bgcolor: 'action.hover', height: 8, borderRadius: 1 }}>
                      <Box sx={{ bgcolor: 'primary.main', width: `${pct}%`, height: 8, borderRadius: 1 }} />
                    </Box>
                  </Box>
                );
              })}
              {Object.keys(porStatus).length === 0 && (
                <Typography variant="body2" color="text.secondary">Sem dados.</Typography>
              )}
            </Stack>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" gutterBottom>Por Prioridade</Typography>
            <Stack spacing={1}>
              {Object.entries(porPrioridade).map(([k, v]) => {
                const pct = Math.round((v / maxPrioridade) * 100);
                return (
                  <Box key={k}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="caption" color="text.secondary">{k}</Typography>
                      <Typography variant="caption" color="text.secondary">{v}</Typography>
                    </Stack>
                    <Box sx={{ bgcolor: 'action.hover', height: 8, borderRadius: 1 }}>
                      <Box sx={{ bgcolor: 'secondary.main', width: `${pct}%`, height: 8, borderRadius: 1 }} />
                    </Box>
                  </Box>
                );
              })}
              {Object.keys(porPrioridade).length === 0 && (
                <Typography variant="body2" color="text.secondary">Sem dados.</Typography>
              )}
            </Stack>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}
