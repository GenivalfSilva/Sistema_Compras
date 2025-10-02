import { Box, Typography, Paper, Stack, Chip, Button, TextField, Card } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { SolicitacoesAPI, type SolicitacaoDetail } from '../../services/solicitacoes';
import { getAllowedTransitions } from '../../utils/solicitacoes';

export default function DetalheSolicitacaoPage() {
  const { id } = useParams();
  const [data, setData] = useState<SolicitacaoDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [obs, setObs] = useState('');
  const [aprovObs, setAprovObs] = useState('');

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const res = await SolicitacoesAPI.get(Number(id));
        setData(res);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const onTransition = async (novo_status: string) => {
    if (!id) return;
    setSaving(true);
    try {
      await SolicitacoesAPI.updateStatus(Number(id), { novo_status, observacoes: obs });
      const res = await SolicitacoesAPI.get(Number(id));
      setData(res);
      setObs('');
    } finally {
      setSaving(false);
    }
  };

  const onApprove = async (acao: 'aprovar' | 'reprovar') => {
    if (!id) return;
    setSaving(true);
    try {
      await SolicitacoesAPI.approval(Number(id), { acao, observacoes: aprovObs });
      const res = await SolicitacoesAPI.get(Number(id));
      setData(res);
      setAprovObs('');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
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
              <Typography variant="h4" fontWeight="bold">Detalhe da Solicitação</Typography>
              <Typography variant="subtitle1">Solicitação #{data?.numero_solicitacao_estoque || id}</Typography>
            </Box>
          </Stack>
        </Box>
      </Card>
      <Paper sx={{ p: 2 }}>
        {loading && <Typography>Carregando...</Typography>}
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Box flex={1}>
              <Typography variant="subtitle2">Descrição</Typography>
              <Typography>{data?.descricao || '-'}</Typography>
            </Box>
            <Box minWidth={240}>
              <Typography variant="subtitle2">Status</Typography>
              <Chip label={data?.status || '-'} color="primary" />
            </Box>
          </Stack>
          <Box>
            <Typography variant="subtitle2">Itens</Typography>
            <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
              <Typography variant="body2">Tabela de itens (em construção)</Typography>
            </Paper>
          </Box>
          {/* Transições de Status */}
          {data && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Próximas ações
              </Typography>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems="center">
                <TextField
                  size="small"
                  label="Observações"
                  value={obs}
                  onChange={(e) => setObs(e.target.value)}
                />
                {getAllowedTransitions(data.status).map((st) => (
                  <Button key={st} variant="outlined" disabled={saving} onClick={() => onTransition(st)}>
                    Mover para: {st}
                  </Button>
                ))}
              </Stack>
            </Box>
          )}
          {/* Aprovação (Diretoria) */}
          {data?.status === 'Aguardando Aprovação' && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Aprovação da Diretoria
              </Typography>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems="center">
                <TextField
                  size="small"
                  label="Observações"
                  value={aprovObs}
                  onChange={(e) => setAprovObs(e.target.value)}
                />
                <Button variant="contained" color="success" disabled={saving} onClick={() => onApprove('aprovar')}>
                  Aprovar
                </Button>
                <Button variant="contained" color="error" disabled={saving} onClick={() => onApprove('reprovar')}>
                  Reprovar
                </Button>
              </Stack>
            </Box>
          )}
        </Stack>
        <Box mt={2}>
          <Button variant="outlined" sx={{ mr: 1 }}>Voltar</Button>
          {/* Botão genérico mantido apenas como placeholder */}
          <Button variant="contained" disabled>
            Mover para próxima etapa
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
