import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Button, Stack } from '@mui/material';
import { UsuariosAPI, type UsuarioV1, type UsuarioDjango } from '../../services/usuarios';

export default function UsuariosPage() {
  const [v1, setV1] = useState<UsuarioV1[]>([]);
  const [dj, setDj] = useState<UsuarioDjango[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [v1res, djres] = await Promise.all([
        UsuariosAPI.listV1().catch(()=>[]),
        UsuariosAPI.listDjango().catch(()=>[]),
      ]);
      setV1(v1res);
      setDj(djres);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Gestão de Usuários (Admin)
      </Typography>
      <Stack direction="row" spacing={1} alignItems="center" mb={2}>
        <Button variant="outlined" onClick={load} disabled={loading}>Atualizar</Button>
        <Typography variant="body2">{v1.length} usuários V1 • {dj.length} usuários Django</Typography>
      </Stack>

      <Typography variant="h6" gutterBottom>Usuários V1</Typography>
      <Paper sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Nome</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Perfil</TableCell>
              <TableCell>Departamento</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {v1.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell>{u.nome}</TableCell>
                <TableCell>{u.username}</TableCell>
                <TableCell>{u.perfil}</TableCell>
                <TableCell>{u.departamento}</TableCell>
              </TableRow>
            ))}
            {!loading && v1.length === 0 && (
              <TableRow><TableCell colSpan={4}>Sem usuários V1.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>

      <Typography variant="h6" gutterBottom>Usuários Django</Typography>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Ativo</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dj.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell>{u.username}</TableCell>
                <TableCell>{u.email || '-'}</TableCell>
                <TableCell>{u.is_active ? 'Sim' : 'Não'}</TableCell>
              </TableRow>
            ))}
            {!loading && dj.length === 0 && (
              <TableRow><TableCell colSpan={3}>Sem usuários Django.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
