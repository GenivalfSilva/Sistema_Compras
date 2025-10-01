import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Tabs, Tab, Table, TableHead, TableRow, TableCell, TableBody, Button, Stack, TextField } from '@mui/material';
import { AuditoriaAPI, type AuditoriaAdminLog, type HistoricoLoginLog } from '../../services/auditoria';

export default function AuditoriaPage() {
  const [tab, setTab] = useState(0);
  const [adminLogs, setAdminLogs] = useState<AuditoriaAdminLog[]>([]);
  const [loginLogs, setLoginLogs] = useState<HistoricoLoginLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [filtroUsuario, setFiltroUsuario] = useState('');
  const [filtroAcao, setFiltroAcao] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [a, l] = await Promise.all([
        AuditoriaAPI.listAdmin().catch(()=>[]),
        AuditoriaAPI.listLogin().catch(()=>[]),
      ]);
      setAdminLogs(a);
      setLoginLogs(l);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const adminFiltrado = adminLogs.filter((r) =>
    (!filtroUsuario || r.usuario?.toLowerCase().includes(filtroUsuario.toLowerCase())) &&
    (!filtroAcao || r.acao?.toLowerCase().includes(filtroAcao.toLowerCase()))
  );
  const loginFiltrado = loginLogs.filter((r) =>
    (!filtroUsuario || (r.username_tentativa?.toLowerCase().includes(filtroUsuario.toLowerCase())))
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Auditoria (Admin)
      </Typography>
      <Stack direction={{ xs:'column', md:'row' }} spacing={1} alignItems="center" mb={2}>
        <TextField size="small" label="Usuário" value={filtroUsuario} onChange={(e)=> setFiltroUsuario(e.target.value)} />
        <TextField size="small" label="Ação (admin)" value={filtroAcao} onChange={(e)=> setFiltroAcao(e.target.value)} />
        <Button variant="outlined" onClick={load} disabled={loading}>Atualizar</Button>
      </Stack>
      <Paper>
        <Tabs value={tab} onChange={(_,v)=> setTab(v)}>
          <Tab label="Auditoria Administrativa" />
          <Tab label="Histórico de Login" />
        </Tabs>
        {tab===0 && (
          <Box p={2}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data/Hora</TableCell>
                  <TableCell>Usuário</TableCell>
                  <TableCell>Ação</TableCell>
                  <TableCell>Módulo</TableCell>
                  <TableCell>Detalhes</TableCell>
                  <TableCell>Solicitação</TableCell>
                  <TableCell>IP</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {adminFiltrado.map((r)=> (
                  <TableRow key={r.id} hover>
                    <TableCell>{new Date(r.timestamp).toLocaleString()}</TableCell>
                    <TableCell>{r.usuario}</TableCell>
                    <TableCell>{r.acao_display || r.acao}</TableCell>
                    <TableCell>{r.modulo}</TableCell>
                    <TableCell sx={{ maxWidth: 360, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{r.detalhes}</TableCell>
                    <TableCell>{r.solicitacao_id ?? '-'}</TableCell>
                    <TableCell>{r.ip_address || '-'}</TableCell>
                  </TableRow>
                ))}
                {!loading && adminFiltrado.length===0 && (
                  <TableRow><TableCell colSpan={7}>Sem registros.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
        )}
        {tab===1 && (
          <Box p={2}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data/Hora</TableCell>
                  <TableCell>Username</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>IP</TableCell>
                  <TableCell>User Agent</TableCell>
                  <TableCell>Sessão</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loginFiltrado.map((r)=> (
                  <TableRow key={r.id} hover>
                    <TableCell>{new Date(r.timestamp).toLocaleString()}</TableCell>
                    <TableCell>{r.username_tentativa}</TableCell>
                    <TableCell>{r.status_display || r.status}</TableCell>
                    <TableCell>{r.ip_address || '-'}</TableCell>
                    <TableCell sx={{ maxWidth: 360, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{r.user_agent || '-'}</TableCell>
                    <TableCell>{r.sessao_id || '-'}</TableCell>
                  </TableRow>
                ))}
                {!loading && loginFiltrado.length===0 && (
                  <TableRow><TableCell colSpan={6}>Sem registros.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
