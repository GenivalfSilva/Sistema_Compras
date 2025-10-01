import { Box, Typography, Stack, TextField, Button, Paper, Select, MenuItem, InputLabel, FormControl, Snackbar, Alert } from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SolicitacoesAPI, type CreateSolicitacaoPayload } from '../../services/solicitacoes';

export default function NovaSolicitacaoPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<CreateSolicitacaoPayload>({
    departamento: '',
    prioridade: '',
    descricao: '',
    local_aplicacao: '',
    observacoes: '',
    valor_estimado: undefined,
    itens: [],
  });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{open:boolean; message:string; severity:'success'|'error'}>({open:false, message:'', severity:'success'});

  const onChange = (key: keyof CreateSolicitacaoPayload) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setForm((f) => ({ ...f, [key]: value }));
    };

  const onSubmit = async () => {
    setSaving(true);
    try {
      // Campos mínimos obrigatórios conforme serializer do backend
      const payload: CreateSolicitacaoPayload = {
        departamento: form.departamento || 'TI',
        prioridade: form.prioridade || 'Normal',
        descricao: form.descricao,
        local_aplicacao: form.local_aplicacao,
        observacoes: form.observacoes,
        valor_estimado: form.valor_estimado ? Number(form.valor_estimado) : undefined,
        itens: form.itens || [],
      };
      const created = await SolicitacoesAPI.create(payload);
      setToast({open:true, message:'Solicitação criada com sucesso!', severity:'success'});
      navigate(`/solicitacoes/${created.id}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Nova Solicitação
      </Typography>
      <Typography variant="body1" gutterBottom>
        Preencha os dados para criar uma nova solicitação.
      </Typography>

      <Paper sx={{ p: 2, mt: 2 }}>
        <Stack spacing={2}>
          <TextField label="Descrição" fullWidth placeholder="Descreva a necessidade" value={form.descricao} onChange={onChange('descricao')} />
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel id="dep-label">Departamento</InputLabel>
              <Select labelId="dep-label" label="Departamento" value={form.departamento} onChange={(e) => setForm(f=>({...f, departamento: String(e.target.value)}))}>
                {['TI','Produção','Estoque','Suprimentos','Diretoria'].map((opt)=> (
                  <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel id="pri-label">Prioridade</InputLabel>
              <Select labelId="pri-label" label="Prioridade" value={form.prioridade} onChange={(e) => setForm(f=>({...f, prioridade: String(e.target.value)}))}>
                {['Urgente','Alta','Normal','Baixa'].map((opt)=> (
                  <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField label="Local de Aplicação" fullWidth value={form.local_aplicacao} onChange={onChange('local_aplicacao')} />
            <TextField label="Valor Estimado" type="number" fullWidth value={form.valor_estimado as any} onChange={onChange('valor_estimado' as any)} />
          </Stack>
          <TextField label="Observações" fullWidth multiline minRows={2} value={form.observacoes} onChange={onChange('observacoes')} />
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Itens
            </Typography>
            {/* TODO: Tabela de itens com código, nome, quantidade, unidade, obs */}
            <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
              <Stack spacing={1}>
                {(form.itens as any[]).map((it: any, idx: number) => (
                  <Stack key={idx} direction={{ xs: 'column', md: 'row' }} spacing={1}>
                    <TextField label="Código" value={it.codigo || ''} onChange={(e)=>{
                      const itens = [...(form.itens as any[])]; itens[idx] = {...it, codigo:e.target.value}; setForm(f=>({...f, itens}));
                    }} />
                    <TextField sx={{ flex:1 }} label="Nome" value={it.nome || ''} onChange={(e)=>{
                      const itens = [...(form.itens as any[])]; itens[idx] = {...it, nome:e.target.value}; setForm(f=>({...f, itens}));
                    }} />
                    <TextField label="Unidade" value={it.unidade || 'UN'} onChange={(e)=>{
                      const itens = [...(form.itens as any[])]; itens[idx] = {...it, unidade:e.target.value}; setForm(f=>({...f, itens}));
                    }} />
                    <TextField type="number" label="Quantidade" value={it.quantidade ?? 1} onChange={(e)=>{
                      const itens = [...(form.itens as any[])]; itens[idx] = {...it, quantidade:Number(e.target.value)}; setForm(f=>({...f, itens}));
                    }} />
                    <Button color="error" onClick={()=>{
                      const itens = [...(form.itens as any[])]; itens.splice(idx,1); setForm(f=>({...f, itens}));
                    }}>Remover</Button>
                  </Stack>
                ))}
                <Button onClick={()=> setForm(f=>({...f, itens:[...(f.itens as any[]), {codigo:'', nome:'', unidade:'UN', quantidade:1}]}))}>Adicionar Item</Button>
              </Stack>
            </Paper>
          </Box>
          <Box>
            <Button variant="contained" onClick={onSubmit} disabled={saving || !form.descricao}>
              {saving ? 'Salvando...' : 'Criar Solicitação'}
            </Button>
          </Box>
        </Stack>
      </Paper>
      <Snackbar open={toast.open} autoHideDuration={2500} onClose={()=> setToast(t=>({...t, open:false}))}>
        <Alert onClose={()=> setToast(t=>({...t, open:false}))} severity={toast.severity} variant="filled">{toast.message}</Alert>
      </Snackbar>
    </Box>
  );
}
