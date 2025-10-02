# Correção de Permissões

## Problema

Alguns usuários podem estar enfrentando o erro "Você não tem permissão para executar essa ação" ao tentar criar novas solicitações. Isso ocorre porque o usuário não possui a permissão `can_create_solicitation` necessária para essa operação.

## Solução

Foi criado um script para adicionar a permissão necessária aos usuários. Para executar:

1. Navegue até a pasta `backend` do projeto
2. Execute o arquivo `fix_permissions.bat` (Windows) ou `python fix_permissions.py` (Linux/Mac)
3. O script adicionará a permissão `can_create_solicitation` ao usuário Leonardo.Fragoso

## Permissões do Sistema

As principais permissões do sistema são:

- `can_create_solicitation`: Permite criar novas solicitações
- `can_manage_stock`: Permite gerenciar o estoque
- `can_manage_procurement`: Permite gerenciar compras (suprimentos)
- `can_approve`: Permite aprovar solicitações (diretoria)
- `is_admin`: Acesso administrativo completo

## Verificação

Para verificar se a permissão foi adicionada corretamente:

1. Faça logout e login novamente no sistema
2. Tente criar uma nova solicitação
3. Se o problema persistir, verifique o console do navegador para mais detalhes

## Suporte

Em caso de problemas, entre em contato com o administrador do sistema.
