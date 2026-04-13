# Digest Sueco 🇸🇪

Curadoria automática de notícias políticas da Suécia, traduzidas e
contextualizadas em português do Brasil. Publicada toda **segunda e quinta-feira**.

---

## Setup em 5 passos

### 1. Criar o repositório no GitHub

1. Acesse [github.com/new](https://github.com/new)
2. Nome do repositório: `digest-sueco`
3. Deixe como **Public** (necessário para GitHub Pages gratuito)
4. Clique em **Create repository**

---

### 2. Fazer upload dos arquivos

Na página do repositório recém-criado, clique em **uploading an existing file**
e suba toda a estrutura desta pasta:

```
digest-sueco/
├── .github/
│   └── workflows/
│       └── digest.yml
├── scripts/
│   └── generate_digest.py
├── index.html          ← o digest atual (baixe do Claude e renomeie)
└── README.md
```

**Importante:** o arquivo `index.html` deve ser o último digest gerado pelo
Claude. Ele serve como página inicial enquanto a automação ainda não rodou.

---

### 3. Adicionar a chave da API da Anthropic

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Vá em **API Keys** → **Create Key**
3. Copie a chave (começa com `sk-ant-...`)
4. No GitHub, vá em **Settings → Secrets and variables → Actions**
5. Clique em **New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: cole a chave
6. Clique em **Add secret**

---

### 4. Ativar o GitHub Pages

1. No repositório, vá em **Settings → Pages**
2. Em **Source**, selecione: `Deploy from a branch`
3. Branch: `main` / Folder: `/ (root)`
4. Clique em **Save**

Após 1–2 minutos, seu digest estará acessível em:

```
https://SEU_USUARIO.github.io/digest-sueco
```

Esse é o link fixo que você compartilha com os amigos.

---

### 5. Testar a geração manual

Para testar sem esperar segunda ou quinta:

1. No repositório, vá em **Actions**
2. Clique em **Gerar Digest Sueco**
3. Clique em **Run workflow → Run workflow**
4. Aguarde ~2 minutos
5. Recarregue a página do GitHub Pages

---

## Como funciona

```
Segunda e quinta, 07h CET
        ↓
GitHub Actions acorda
        ↓
Python chama a API da Anthropic com web_search ativado
        ↓
Claude busca notícias suecas dos últimos 3 dias
(SVT, SR/Ekot, Regeringen.se, Morgontidningen)
        ↓
Gera o HTML completo com 3–4 notícias expandidas,
contexto político e indicador de viés editorial por fonte
        ↓
Commit automático do index.html no repositório
        ↓
GitHub Pages publica instantaneamente
```

---

## Custo estimado

- **GitHub Actions:** gratuito (2.000 minutos/mês no plano free; cada execução
  usa ~2 minutos → 4 execuções/mês = 8 minutos)
- **GitHub Pages:** gratuito para repositórios públicos
- **API Anthropic:** ~$0.03–0.08 por execução (modelo claude-sonnet-4,
  com web_search). 8 execuções/mês ≈ $0.50/mês

---

## Personalização

Para mudar os dias/horários de publicação, edite o arquivo
`.github/workflows/digest.yml`:

```yaml
schedule:
  - cron: '0 6 * * 1'   # segunda, 07h CET
  - cron: '0 6 * * 4'   # quinta,  07h CET
```

Referência de cron: [crontab.guru](https://crontab.guru)

---

## Problemas comuns

**O workflow falhou com erro de API:**
Verifique se o secret `ANTHROPIC_API_KEY` está correto em Settings → Secrets.

**A página não atualiza:**
O GitHub Pages pode demorar até 5 minutos para refletir mudanças.
Force o recarregamento com Ctrl+Shift+R.

**O JSON veio malformado:**
Raro, mas pode ocorrer. Rode o workflow manualmente novamente.
