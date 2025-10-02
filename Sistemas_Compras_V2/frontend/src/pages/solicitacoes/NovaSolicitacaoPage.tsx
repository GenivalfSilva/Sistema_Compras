import { 
  Box, 
  Typography, 
  Stack, 
  TextField, 
  Button, 
  Select, 
  MenuItem, 
  InputLabel, 
  FormControl, 
  Snackbar, 
  Alert, 
  Card, 
  CardContent, 
  CardHeader, 
  Divider, 
  IconButton, 
  Tooltip, 
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody
} from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SolicitacoesAPI, type CreateSolicitacaoPayload } from '../../services/solicitacoes';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';

export default function NovaSolicitacaoPage() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [form, setForm] = useState<CreateSolicitacaoPayload>({
    departamento: 'TI',
    prioridade: 'Normal',
    descricao: '',
    local_aplicacao: '',
    observacoes: '',
    valor_estimado: undefined,
    itens: [],
  });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{open:boolean; message:string; severity:'success'|'error'}>({open:false, message:'', severity:'success'});
  const [errors, setErrors] = useState<{[key: string]: string}>({});

  const onChange = (key: keyof CreateSolicitacaoPayload) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setForm((f) => ({ ...f, [key]: value }));
      
      // Clear error when field is edited
      if (errors[key]) {
        setErrors(prev => {
          const newErrors = {...prev};
          delete newErrors[key];
          return newErrors;
        });
      }
    };
    
  const handleNext = () => {
    // Validate current step
    if (activeStep === 0) {
      const stepErrors: {[key: string]: string} = {};
      if (!form.descricao) stepErrors.descricao = 'Descrição é obrigatória';
      if (!form.local_aplicacao) stepErrors.local_aplicacao = 'Local de aplicação é obrigatório';
      
      if (Object.keys(stepErrors).length > 0) {
        setErrors(stepErrors);
        return;
      }
    }
    
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const addItem = () => {
    setForm(f => ({
      ...f, 
      itens: [...(f.itens as any[]), {codigo: '', nome: '', unidade: 'UN', quantidade: 1}]
    }));
  };
  
  const removeItem = (index: number) => {
    const itens = [...(form.itens as any[])];
    itens.splice(index, 1);
    setForm(f => ({...f, itens}));
  };
  
  const updateItem = (index: number, field: string, value: any) => {
    const itens = [...(form.itens as any[])];
    itens[index] = {...itens[index], [field]: value};
    setForm(f => ({...f, itens}));
  };

  const onSubmit = async () => {
    // Final validation
    const finalErrors: {[key: string]: string} = {};
    if (!form.descricao) finalErrors.descricao = 'Descrição é obrigatória';
    if (!form.local_aplicacao) finalErrors.local_aplicacao = 'Local de aplicação é obrigatório';
    
    if (Object.keys(finalErrors).length > 0) {
      setErrors(finalErrors);
      setActiveStep(0); // Go back to first step if there are errors
      return;
    }
    
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
    } catch (e: any) {
      setToast({open:true, message: e?.response?.data?.detail || e?.message || 'Erro ao criar solicitação', severity:'error'});
    } finally {
      setSaving(false);
    }
  };

  const steps = [
    {
      label: 'Informações Básicas',
      description: 'Preencha os dados principais da solicitação',
    },
    {
      label: 'Itens Solicitados',
      description: 'Adicione os produtos ou serviços que deseja solicitar',
    },
    {
      label: 'Revisão e Envio',
      description: 'Revise os dados e envie sua solicitação',
    },
  ];

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Card sx={{ mb: 3, borderRadius: 2, overflow: 'hidden' }}>
        <Box 
          sx={{ 
            p: 3, 
            background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
            color: 'white'
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h4" fontWeight="bold">Nova Solicitação</Typography>
              <Typography variant="subtitle1">Preencha os dados para criar uma nova solicitação</Typography>
            </Box>
            <Button 
              variant="outlined" 
              color="inherit" 
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/solicitacoes')}
              sx={{ borderColor: 'white', color: 'white' }}
            >
              Voltar para Solicitações
            </Button>
          </Stack>
        </Box>
        
        {saving && <LinearProgress />}
      </Card>

      <Card sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <CardContent>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel>
                  <Typography variant="subtitle1" fontWeight="bold">{step.label}</Typography>
                </StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {step.description}
                  </Typography>
                  
                  {index === 0 && (
                    <Box sx={{ display: 'grid', gap: 2 }}>
                      <Box>
                        <TextField 
                          label="Descrição" 
                          fullWidth 
                          placeholder="Descreva a necessidade" 
                          value={form.descricao} 
                          onChange={onChange('descricao')}
                          required
                          error={!!errors.descricao}
                          helperText={errors.descricao}
                        />
                      </Box>
                      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                        <FormControl fullWidth>
                          <InputLabel id="dep-label">Departamento</InputLabel>
                          <Select 
                            labelId="dep-label" 
                            label="Departamento" 
                            value={form.departamento} 
                            onChange={(e) => setForm(f=>({...f, departamento: String(e.target.value)}))}
                          >
                            {['TI','Produção','Estoque','Suprimentos','Diretoria'].map((opt)=> (
                              <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                        <FormControl fullWidth>
                          <InputLabel id="pri-label">Prioridade</InputLabel>
                          <Select 
                            labelId="pri-label" 
                            label="Prioridade" 
                            value={form.prioridade} 
                            onChange={(e) => setForm(f=>({...f, prioridade: String(e.target.value)}))}
                          >
                            {['Urgente','Alta','Normal','Baixa'].map((opt)=> (
                              <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Box>
                      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                        <TextField 
                          label="Local de Aplicação" 
                          fullWidth 
                          value={form.local_aplicacao} 
                          onChange={onChange('local_aplicacao')}
                          required
                          error={!!errors.local_aplicacao}
                          helperText={errors.local_aplicacao}
                          placeholder="Ex: Sala de Reuniões - 3º Andar"
                        />
                        <TextField 
                          label="Valor Estimado (R$)" 
                          type="number" 
                          fullWidth 
                          value={form.valor_estimado as any} 
                          onChange={onChange('valor_estimado' as any)}
                          placeholder="Opcional"
                          InputProps={{
                            startAdornment: <Typography variant="body2" sx={{ mr: 1 }}>R$</Typography>,
                          }}
                        />
                      </Box>
                      <Box>
                        <TextField 
                          label="Observações" 
                          fullWidth 
                          multiline 
                          minRows={3} 
                          value={form.observacoes} 
                          onChange={onChange('observacoes')}
                          placeholder="Informações adicionais sobre a solicitação"
                        />
                      </Box>
                    </Box>
                  )}
                  
                  {index === 1 && (
                    <Box>
                      <Card variant="outlined" sx={{ mb: 2 }}>
                        <CardHeader 
                          title="Itens Solicitados" 
                          titleTypographyProps={{ variant: 'h6' }}
                          action={
                            <Button 
                              variant="contained" 
                              color="primary" 
                              startIcon={<AddCircleOutlineIcon />}
                              onClick={addItem}
                              size="small"
                            >
                              Adicionar Item
                            </Button>
                          }
                        />
                        <Divider />
                        <CardContent>
                          {(form.itens as any[]).length === 0 ? (
                            <Box sx={{ textAlign: 'center', py: 3 }}>
                              <ShoppingCartIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
                              <Typography variant="body2" color="text.secondary">
                                Nenhum item adicionado. Clique em "Adicionar Item" para incluir produtos ou serviços.
                              </Typography>
                            </Box>
                          ) : (
                            <Stack spacing={2}>
                              {(form.itens as any[]).map((item, index) => (
                                <Card key={index} variant="outlined" sx={{ p: 2 }}>
                                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '2fr 4fr 2fr 2fr 2fr' }, gap: 2, alignItems: 'center' }}>
                                    <TextField 
                                      label="Código" 
                                      fullWidth 
                                      size="small"
                                      value={item.codigo || ''} 
                                      onChange={(e) => updateItem(index, 'codigo', e.target.value)}
                                    />
                                    <TextField 
                                      label="Nome do Item" 
                                      fullWidth 
                                      size="small"
                                      value={item.nome || ''} 
                                      onChange={(e) => updateItem(index, 'nome', e.target.value)}
                                    />
                                    <TextField 
                                      label="Unidade" 
                                      fullWidth 
                                      size="small"
                                      value={item.unidade || 'UN'} 
                                      onChange={(e) => updateItem(index, 'unidade', e.target.value)}
                                    />
                                    <TextField 
                                      label="Quantidade" 
                                      type="number" 
                                      fullWidth 
                                      size="small"
                                      value={item.quantidade || 1} 
                                      onChange={(e) => updateItem(index, 'quantidade', Number(e.target.value))}
                                      inputProps={{ min: 1 }}
                                    />
                                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                                      <Tooltip title="Remover Item">
                                        <IconButton color="error" onClick={() => removeItem(index)}>
                                          <DeleteIcon />
                                        </IconButton>
                                      </Tooltip>
                                    </Box>
                                  </Box>
                                </Card>
                              ))}
                            </Stack>
                          )}
                        </CardContent>
                      </Card>
                    </Box>
                  )}
                  
                  {index === 2 && (
                    <Box>
                      <Card variant="outlined" sx={{ mb: 3 }}>
                        <CardHeader title="Resumo da Solicitação" titleTypographyProps={{ variant: 'h6' }} />
                        <Divider />
                        <CardContent>
                          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                            <Box>
                              <Typography variant="subtitle2" color="text.secondary">Departamento</Typography>
                              <Typography variant="body1">{form.departamento}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="subtitle2" color="text.secondary">Prioridade</Typography>
                              <Typography variant="body1">{form.prioridade}</Typography>
                            </Box>
                            <Box sx={{ gridColumn: { md: '1 / span 2' } }}>
                              <Typography variant="subtitle2" color="text.secondary">Descrição</Typography>
                              <Typography variant="body1">{form.descricao}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="subtitle2" color="text.secondary">Local de Aplicação</Typography>
                              <Typography variant="body1">{form.local_aplicacao}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="subtitle2" color="text.secondary">Valor Estimado</Typography>
                              <Typography variant="body1">
                                {form.valor_estimado ? `R$ ${Number(form.valor_estimado).toFixed(2)}` : 'Não informado'}
                              </Typography>
                            </Box>
                            {form.observacoes && (
                              <Box sx={{ gridColumn: { md: '1 / span 2' } }}>
                                <Typography variant="subtitle2" color="text.secondary">Observações</Typography>
                                <Typography variant="body1">{form.observacoes}</Typography>
                              </Box>
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                      
                      <Card variant="outlined">
                        <CardHeader 
                          title={`Itens (${(form.itens as any[]).length})`} 
                          titleTypographyProps={{ variant: 'h6' }} 
                        />
                        <Divider />
                        <CardContent>
                          {(form.itens as any[]).length === 0 ? (
                            <Typography variant="body2" color="text.secondary" align="center">
                              Nenhum item adicionado.
                            </Typography>
                          ) : (
                            <Box sx={{ overflowX: 'auto' }}>
                              <Table size="small">
                                <TableHead>
                                  <TableRow>
                                    <TableCell>Código</TableCell>
                                    <TableCell>Nome</TableCell>
                                    <TableCell>Unidade</TableCell>
                                    <TableCell align="right">Quantidade</TableCell>
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {(form.itens as any[]).map((item, idx) => (
                                    <TableRow key={idx}>
                                      <TableCell>{item.codigo || '-'}</TableCell>
                                      <TableCell>{item.nome || '-'}</TableCell>
                                      <TableCell>{item.unidade || 'UN'}</TableCell>
                                      <TableCell align="right">{item.quantidade || 1}</TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Box>
                  )}
                  
                  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                    <Button
                      disabled={index === 0}
                      onClick={handleBack}
                    >
                      Voltar
                    </Button>
                    <Box>
                      {index === steps.length - 1 ? (
                        <Button
                          variant="contained"
                          onClick={onSubmit}
                          disabled={saving}
                          startIcon={<SaveIcon />}
                        >
                          {saving ? 'Enviando...' : 'Enviar Solicitação'}
                        </Button>
                      ) : (
                        <Button
                          variant="contained"
                          onClick={handleNext}
                        >
                          Próximo
                        </Button>
                      )}
                    </Box>
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>
      
      <Snackbar open={toast.open} autoHideDuration={4000} onClose={()=> setToast(t=>({...t, open:false}))}>
        <Alert onClose={()=> setToast(t=>({...t, open:false}))} severity={toast.severity} variant="filled">{toast.message}</Alert>
      </Snackbar>
    </Box>
  );
}
