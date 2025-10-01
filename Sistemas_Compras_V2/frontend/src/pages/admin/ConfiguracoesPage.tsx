import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, TextField, Button, Stack, Snackbar, Alert, Divider } from '@mui/material';
import { ConfiguracoesAPI, type Configuracao, type ConfiguracaoSLA, type LimiteAprovacao } from '../../services/configuracoes';

export default function ConfiguracoesPage() {
  const [configs, setConfigs] = useState<Configuracao[]>([]);
  const [sla, setSla] = useState<ConfiguracaoSLA[]>([]);
  const [limites, setLimites] = useState<LimiteAprovacao[]>([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{open:boolean; message:string; severity:'success'|'error'}>({open:false, message:'', severity:'success'});

  const [novoSLA, setNovoSLA] = useState<Omit<ConfiguracaoSLA,'id'>>({departamento:'', sla_urgente:1, sla_alta:2, sla_normal:3, sla_baixa:5, ativo:true});
  const [novoLimite, setNovoLimite] = useState<Omit<LimiteAprovacao,'id'>>({nome:'', valor_minimo:0, valor_maximo:0, aprovador:'Gerência', ativo:true});

  const load = async () => {
    setLoading(true);
    try {
      const [c, s, l] = await Promise.all([
        ConfiguracoesAPI.listConfigs().catch(()=>[]),
        ConfiguracoesAPI.listSLA().catch(()=>[]),
        ConfiguracoesAPI.listLimits().catch(()=>[]),
      ]);
      setConfigs(c);
      setSla(s);
      setLimites(l);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const salvarConfig = async (row: Configuracao) => {
    const updated = await ConfiguracoesAPI.updateConfig(row.id, { valor: row.valor, tipo: row.tipo, descricao: row.descricao });
    setToast({open:true, message:'Configuração salva', severity:'success'});
    setConfigs((arr)=> arr.map((c)=> c.id===row.id? updated : c));
  };

  const salvarSLA = async (row: ConfiguracaoSLA) => {
    const updated = await ConfiguracoesAPI.updateSLA(row.id, row);
    setToast({open:true, message:'SLA salvo', severity:'success'});
    setSla((arr)=> arr.map((c)=> c.id===row.id? updated : c));
  };

  const criarSLA = async () => {
    const created = await ConfiguracoesAPI.createSLA(novoSLA);
    setToast({open:true, message:'SLA criado', severity:'success'});
    setSla((arr)=> [created, ...arr]);
    setNovoSLA({departamento:'', sla_urgente:1, sla_alta:2, sla_normal:3, sla_baixa:5, ativo:true});
  };

  const salvarLimite = async (row: LimiteAprovacao) => {
    const updated = await ConfiguracoesAPI.updateLimit(row.id, row);
    setToast({open:true, message:'Limite salvo', severity:'success'});
    setLimites((arr)=> arr.map((c)=> c.id===row.id? updated : c));
  };

  const criarLimite = async () => {
    const created = await ConfiguracoesAPI.createLimit(novoLimite);
    setToast({open:true, message:'Limite criado', severity:'success'});
    setLimites((arr)=> [created, ...arr]);
    setNovoLimite({nome:'', valor_minimo:0, valor_maximo:0, aprovador:'Gerência', ativo:true});
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Configurações (Admin)
      </Typography>
      <Stack direction="row" spacing={1} alignItems="center" mb={2}>
        <Button variant="outlined" onClick={load} disabled={loading}>Atualizar</Button>
      </Stack>

      {/* Configurações Gerais */}
      <Typography variant="h6" gutterBottom>Configurações Gerais</Typography>
      <Paper sx={{ mb:3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Chave</TableCell>
              <TableCell>Valor</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {configs.map((c)=> (
              <TableRow key={c.id} hover>
                <TableCell>{c.chave}</TableCell>
                <TableCell width={280}><TextField size="small" fullWidth value={c.valor} onChange={(e)=> setConfigs(arr=> arr.map(x=> x.id===c.id? {...x, valor:e.target.value}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" value={c.tipo||''} onChange={(e)=> setConfigs(arr=> arr.map(x=> x.id===c.id? {...x, tipo:e.target.value}: x))} /></TableCell>
                <TableCell><TextField size="small" fullWidth value={c.descricao||''} onChange={(e)=> setConfigs(arr=> arr.map(x=> x.id===c.id? {...x, descricao:e.target.value}: x))} /></TableCell>
                <TableCell align="right"><Button size="small" variant="contained" onClick={()=> salvarConfig(c)}>Salvar</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Divider sx={{ my: 2 }} />

      {/* SLA */}
      <Typography variant="h6" gutterBottom>Configuração de SLA</Typography>
      <Paper sx={{ mb:2, p:2 }}>
        <Typography variant="subtitle1">Novo SLA</Typography>
        <Stack direction={{ xs:'column', md:'row' }} spacing={1} mt={1}>
          <TextField label="Departamento" size="small" value={novoSLA.departamento} onChange={(e)=> setNovoSLA(s=> ({...s, departamento:e.target.value}))} />
          <TextField label="Urgente" type="number" size="small" value={novoSLA.sla_urgente} onChange={(e)=> setNovoSLA(s=> ({...s, sla_urgente:Number(e.target.value)}))} />
          <TextField label="Alta" type="number" size="small" value={novoSLA.sla_alta} onChange={(e)=> setNovoSLA(s=> ({...s, sla_alta:Number(e.target.value)}))} />
          <TextField label="Normal" type="number" size="small" value={novoSLA.sla_normal} onChange={(e)=> setNovoSLA(s=> ({...s, sla_normal:Number(e.target.value)}))} />
          <TextField label="Baixa" type="number" size="small" value={novoSLA.sla_baixa} onChange={(e)=> setNovoSLA(s=> ({...s, sla_baixa:Number(e.target.value)}))} />
          <Button variant="contained" onClick={criarSLA} disabled={!novoSLA.departamento}>Criar</Button>
        </Stack>
      </Paper>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Departamento</TableCell>
              <TableCell>Urgente</TableCell>
              <TableCell>Alta</TableCell>
              <TableCell>Normal</TableCell>
              <TableCell>Baixa</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sla.map((r)=> (
              <TableRow key={r.id} hover>
                <TableCell width={180}><TextField size="small" value={r.departamento} onChange={(e)=> setSla(arr=> arr.map(x=> x.id===r.id? {...x, departamento:e.target.value}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" type="number" value={r.sla_urgente} onChange={(e)=> setSla(arr=> arr.map(x=> x.id===r.id? {...x, sla_urgente:Number(e.target.value)}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" type="number" value={r.sla_alta} onChange={(e)=> setSla(arr=> arr.map(x=> x.id===r.id? {...x, sla_alta:Number(e.target.value)}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" type="number" value={r.sla_normal} onChange={(e)=> setSla(arr=> arr.map(x=> x.id===r.id? {...x, sla_normal:Number(e.target.value)}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" type="number" value={r.sla_baixa} onChange={(e)=> setSla(arr=> arr.map(x=> x.id===r.id? {...x, sla_baixa:Number(e.target.value)}: x))} /></TableCell>
                <TableCell align="right"><Button size="small" variant="contained" onClick={()=> salvarSLA(r)}>Salvar</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Divider sx={{ my: 2 }} />

      {/* Limites de Aprovação */}
      <Typography variant="h6" gutterBottom>Limites de Aprovação</Typography>
      <Paper sx={{ mb:2, p:2 }}>
        <Typography variant="subtitle1">Novo Limite</Typography>
        <Stack direction={{ xs:'column', md:'row' }} spacing={1} mt={1}>
          <TextField label="Nome" size="small" value={novoLimite.nome} onChange={(e)=> setNovoLimite(s=> ({...s, nome:e.target.value}))} />
          <TextField label="Mínimo" type="number" size="small" value={novoLimite.valor_minimo} onChange={(e)=> setNovoLimite(s=> ({...s, valor_minimo:Number(e.target.value)}))} />
          <TextField label="Máximo" type="number" size="small" value={novoLimite.valor_maximo} onChange={(e)=> setNovoLimite(s=> ({...s, valor_maximo:Number(e.target.value)}))} />
          <TextField label="Aprovador" size="small" value={novoLimite.aprovador} onChange={(e)=> setNovoLimite(s=> ({...s, aprovador:e.target.value}))} />
          <Button variant="contained" onClick={criarLimite} disabled={!novoLimite.nome || novoLimite.valor_minimo>=novoLimite.valor_maximo}>Criar</Button>
        </Stack>
      </Paper>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Nome</TableCell>
              <TableCell>Mínimo</TableCell>
              <TableCell>Máximo</TableCell>
              <TableCell>Aprovador</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {limites.map((r)=> (
              <TableRow key={r.id} hover>
                <TableCell width={220}><TextField size="small" value={r.nome} onChange={(e)=> setLimites(arr=> arr.map(x=> x.id===r.id? {...x, nome:e.target.value}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" type="number" value={r.valor_minimo} onChange={(e)=> setLimites(arr=> arr.map(x=> x.id===r.id? {...x, valor_minimo:Number(e.target.value)}: x))} /></TableCell>
                <TableCell width={120}><TextField size="small" type="number" value={r.valor_maximo} onChange={(e)=> setLimites(arr=> arr.map(x=> x.id===r.id? {...x, valor_maximo:Number(e.target.value)}: x))} /></TableCell>
                <TableCell width={200}><TextField size="small" value={r.aprovador} onChange={(e)=> setLimites(arr=> arr.map(x=> x.id===r.id? {...x, aprovador:e.target.value}: x))} /></TableCell>
                <TableCell align="right"><Button size="small" variant="contained" onClick={()=> salvarLimite(r)}>Salvar</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Snackbar open={toast.open} autoHideDuration={2500} onClose={()=> setToast(t=>({...t, open:false}))}>
        <Alert onClose={()=> setToast(t=>({...t, open:false}))} severity={toast.severity} variant="filled">{toast.message}</Alert>
      </Snackbar>
    </Box>
  );
}
