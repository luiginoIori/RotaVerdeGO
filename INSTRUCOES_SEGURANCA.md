# INSTRUÇÕES - Sistema de Autenticação Rota Verde

## 📋 Visão Geral
Sistema de autenticação implementado para proteger o acesso ao aplicativo de fluxo de caixa.

## 🔐 Funcionalidades de Segurança

### 1. **Validador Executável**
- Arquivo: `auth_validator.py`
- Compilado para: `password_validator.exe`
- **NÃO EDITÁVEL** após compilação
- Controle automático de tentativas
- Hash seguro das senhas com SHA-256

### 2. **Tela de Login Integrada**
- Interface visual no Streamlit
- Validação em tempo real
- Controle de sessão
- Design responsivo

### 3. **Controle de Sessão**
- Usuário permanece logado durante o uso
- Botão de logout na sidebar
- Verificação automática em todas as páginas
- Informações do usuário na interface

## 🚀 Como Usar

### **Passo 1: Compilar o Validador (Opcional)**
```bash
# Instalar PyInstaller se não tiver
pip install pyinstaller

# Executar script de compilação
python compile_validator.py
```

### **Passo 2: Executar o Sistema**
```bash
# Executar aplicação principal
streamlit run app.py
```

### **Passo 3: Fazer Login**
- Acesse o sistema pelo browser
- Digite uma das senhas válidas
- Clique em "Entrar no Sistema"

## 🔑 Senhas Padrão

### **Opção 1: Admin**
```
RotaVerde2024
```

### **Opção 2: Usuário**
```
FluxoCaixa@2024
```

## 🛠️ Configurações Técnicas

### **Segurança**
- Senhas hash SHA-256 com salt
- Controle de tentativas (3 máximo)
- Bloqueio temporário (5 minutos)
- Delay anti-força bruta

### **Sessão**
- Controle por `st.session_state`
- Logout automático ao fechar
- Verificação em todas as páginas
- Informações do usuário visíveis

## 📁 Arquivos do Sistema

```
📦 Rota Verde/
├── 🔐 auth_validator.py          # Validador de senha (fonte)
├── 🔧 compile_validator.py       # Script de compilação
├── 💻 password_validator.exe     # Validador compilado
├── 🚀 executar_validador.bat     # Facilitador Windows
├── 📱 app.py                     # Aplicação principal
├── 📋 INSTRUCOES_SEGURANCA.md    # Este arquivo
└── 📊 (outros arquivos do sistema)
```

## ⚙️ Personalização

### **Adicionar Nova Senha**
1. Usar função `add_new_password()` no validador
2. Copiar hash gerado
3. Adicionar ao dicionário `_valid_hashes`
4. Recompilar o executável

### **Alterar Tempo de Bloqueio**
```python
# Em auth_validator.py, linha ~24
self._lockout_time = 300  # segundos (5 min padrão)
```

### **Alterar Número Máximo de Tentativas**
```python
# Em auth_validator.py, linha ~23
self._max_attempts = 3  # tentativas padrão
```

## 🔧 Solução de Problemas

### **Problema: Não consegue compilar executável**
**Solução:**
```bash
pip install --upgrade pyinstaller
python -m pip install --upgrade pip
```

### **Problema: Senha não funciona**
**Verificações:**
1. Conferir se digitou corretamente
2. Verificar se não tem espaços extras
3. Aguardar se estiver bloqueado

### **Problema: Sessão expira rapidamente**
**Causa:** Normal do Streamlit
**Solução:** Fazer login novamente

### **Problema: Interface não carrega**
**Verificações:**
1. Streamlit instalado: `pip install streamlit`
2. Todas as dependências instaladas
3. Porta 8501 disponível

## 🛡️ Boas Práticas de Segurança

### **Em Produção:**
1. ❌ Remover checkbox "Mostrar dica de senha"
2. ❌ Não compartilhar senhas por texto
3. ✅ Usar HTTPS se em servidor
4. ✅ Trocar senhas padrão
5. ✅ Backup regular dos dados

### **Para Desenvolvedores:**
1. 📝 Senhas apenas em arquivo compilado
2. 🔒 Não versionar senhas em Git
3. 🧪 Testar bloqueio de tentativas
4. 📊 Monitorar logs de acesso

## 📞 Suporte

### **Esqueci a Senha**
- Contate o administrador do sistema
- Use o validador executável para teste
- Verifique as dicas de senha (desenvolvimento)

### **Sistema Bloqueado**
- Aguarde 5 minutos após 3 tentativas
- Reinicie o navegador se necessário
- Verifique se não há problema de digitação

---

## ✅ Checklist de Implementação

- [✅] Validador de senha criado
- [✅] Sistema compilável configurado  
- [✅] Tela de login implementada
- [✅] Controle de sessão ativo
- [✅] Proteção em todas as páginas
- [✅] Interface de usuário na sidebar
- [✅] Botão de logout funcional
- [✅] Documentação completa

**Status: 🎉 SISTEMA COMPLETAMENTE IMPLEMENTADO**

---
*Rota Verde - Sistema de Gestão de Fluxo de Caixa | Versão Segura*