"""
Digest Sueco — gerador automático
Busca notícias políticas suecas dos últimos 3 dias,
traduz e contextualiza em português, e gera o index.html.

Roda via GitHub Actions toda segunda e quinta-feira.
Requer: ANTHROPIC_API_KEY no environment.
"""

import os
import json
import datetime
import anthropic

# ── configuração ──────────────────────────────────────────
SOURCES = [
    "svt.se/nyheter/inrikes",
    "svt.se/nyheter/ekonomi",
    "sverigesradio.se/ekot",
    "morgontidningen.se",
    "regeringen.se/pressmeddelanden",
]

TODAY = datetime.date.today()
DATE_PTBR = TODAY.strftime("%-d de %B de %Y").replace(
    "January","janeiro").replace("February","fevereiro").replace(
    "March","março").replace("April","abril").replace(
    "May","maio").replace("June","junho").replace(
    "July","julho").replace("August","agosto").replace(
    "September","setembro").replace("October","outubro").replace(
    "November","novembro").replace("December","dezembro")

WEEKDAY_PTBR = ["Segunda-feira","Terça-feira","Quarta-feira",
                "Quinta-feira","Sexta-feira","Sábado","Domingo"][TODAY.weekday()]

# ── prompt ────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é o editor do Digest Sueco, uma curadoria de notícias
políticas da Suécia traduzidas e contextualizadas em português do Brasil.

Suas regras:
1. Use SOMENTE fontes suecas em sueco (SVT, Sveriges Radio/Ekot, Regeringen.se,
   Morgontidningen, Expressen, Aftonbladet). Evite fontes em inglês, exceto para
   tópicos explicitamente internacionais.
2. Para cada notícia, indique qual artigo específico você usou (título + data).
3. Cada notícia deve ter 4–6 parágrafos expandidos — não apenas resumo.
4. Inclua uma pull quote relevante por notícia.
5. Na seção de contexto, explique o posicionamento político de cada fonte usada
   (esquerda / centro-esquerda / centro / centro-direita / direita / institucional).
6. Foque exclusivamente em política interna sueca.
7. Selecione 3 a 4 notícias dos últimos 3 dias.
8. Responda SOMENTE com JSON válido, sem markdown, sem texto fora do JSON.

Formato de resposta (JSON puro):
{
  "date": "11 de abril de 2026",
  "weekday": "Quinta-feira",
  "stories": [
    {
      "tag": "Migração",
      "tag_class": "migracao",
      "date_str": "7 abr 2026 · SVT Nyheter",
      "headline": "Título em português",
      "paragraphs": ["parágrafo 1", "parágrafo 2", "..."],
      "pull_quote": "Citação marcante do artigo",
      "context": "Contexto político em 2–3 parágrafos",
      "sources": [
        {
          "name": "SVT Nyheter",
          "bias_class": "c",
          "bias_label": "Centro / Público",
          "article": "Título do artigo lido, data",
          "note": "Descrição do veículo e como cobriu esse tema"
        }
      ]
    }
  ]
}

Classes de viés (bias_class): l, cl, c, cr, r, n
  l  = esquerda
  cl = centro-esquerda
  c  = centro / público / técnico
  cr = centro-direita
  r  = direita
  n  = institucional / neutro
"""

USER_PROMPT = f"""Hoje é {WEEKDAY_PTBR}, {DATE_PTBR}.

Busque as notícias políticas suecas mais relevantes dos últimos 3 dias nas
seguintes fontes (em sueco): SVT Nyheter, Sveriges Radio Ekot, Regeringen.se,
Morgontidningen, Expressen.

Selecione 3 ou 4 notícias de foco político. Gere o digest completo no formato
JSON especificado. Lembre-se: artigos expandidos, fontes reais lidas, contexto
de viés editorial para cada fonte."""

# ── HTML template ─────────────────────────────────────────
HTML_HEAD = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Digest Sueco · {date}</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,600;1,8..60,300&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink: #e8e0d0; --paper: #16130e; --paper-dark: #1f1a12;
    --paper-mid: #262018; --rust: #d96b3a; --gold: #d4a44a;
    --slate: #a8b8cc; --muted: #7a7060; --divider: #3a3228;
    --left: #5b9bd6; --center-left: #4ab0c0; --center: #7aaa50;
    --center-right: #c8a040; --right: #d96b3a; --neutral: #909090;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--paper); color: var(--ink);
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 16px; line-height: 1.75; min-height: 100vh; }}
  body::before {{ content: ''; position: fixed; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
    pointer-events: none; z-index: 0; }}
  .wrapper {{ position: relative; z-index: 1; max-width: 800px;
    margin: 0 auto; padding: 0 28px 100px; }}
  .masthead {{ text-align: center; padding: 52px 0 28px;
    border-bottom: 3px double var(--divider); margin-bottom: 28px; }}
  .masthead-eyebrow {{ font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; letter-spacing: 0.28em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 14px; }}
  .masthead h1 {{ font-family: 'Playfair Display', serif;
    font-size: clamp(40px,9vw,72px); font-weight: 700;
    letter-spacing: -0.025em; line-height: 0.95; }}
  .masthead h1 em {{ color: var(--rust); font-style: italic; }}
  .masthead-meta {{ margin-top: 18px; display: flex;
    justify-content: center; gap: 24px; flex-wrap: wrap; }}
  .masthead-meta span {{ font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: var(--muted); letter-spacing: 0.12em; }}
  .masthead-meta span::before {{ content: '◆ '; color: var(--divider); }}
  .legend {{ background: var(--paper-dark); border: 1px solid var(--divider);
    border-radius: 3px; padding: 14px 18px; margin-bottom: 40px; }}
  .legend-title {{ font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    text-transform: uppercase; letter-spacing: 0.25em;
    color: var(--muted); margin-bottom: 10px; }}
  .legend-items {{ display: flex; flex-wrap: wrap; gap: 10px 22px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; }}
  .ldot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}
  .ldot.l  {{ background: var(--left); }}
  .ldot.cl {{ background: var(--center-left); }}
  .ldot.c  {{ background: var(--center); }}
  .ldot.cr {{ background: var(--center-right); }}
  .ldot.r  {{ background: var(--right); }}
  .ldot.n  {{ background: var(--neutral); }}
  .section-title {{ font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    text-transform: uppercase; letter-spacing: 0.32em; color: var(--muted);
    text-align: center; margin: 44px 0 36px; display: flex;
    align-items: center; gap: 14px; }}
  .section-title::before, .section-title::after {{ content: ''; flex: 1;
    height: 1px; background: var(--divider); }}
  .story {{ margin-bottom: 64px; padding-bottom: 56px;
    border-bottom: 1px solid var(--divider);
    animation: fadeUp 0.6s ease both; }}
  .story:last-of-type {{ border-bottom: none; }}
  @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(18px); }}
    to {{ opacity:1; transform:translateY(0); }} }}
  .story:nth-of-type(1) {{ animation-delay:.10s }}
  .story:nth-of-type(2) {{ animation-delay:.20s }}
  .story:nth-of-type(3) {{ animation-delay:.30s }}
  .story:nth-of-type(4) {{ animation-delay:.40s }}
  .story-meta {{ display: flex; align-items: center; gap: 10px;
    margin-bottom: 14px; flex-wrap: wrap; }}
  .tag {{ font-family: 'IBM Plex Mono', monospace; font-size: 9.5px;
    text-transform: uppercase; letter-spacing: 0.16em;
    padding: 3px 9px; border-radius: 2px; color: white; }}
  .tag.economia {{ background: #2a7a3a; }}
  .tag.politica {{ background: #1a4a8a; }}
  .tag.migracao {{ background: #6b3a9a; }}
  .tag.defesa   {{ background: #7a3a1a; }}
  .tag.energia  {{ background: #3a6a7a; }}
  .story-date {{ font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: var(--muted); }}
  .story h2 {{ font-family: 'Playfair Display', serif;
    font-size: clamp(24px,4.5vw,34px); font-weight: 700;
    line-height: 1.15; margin-bottom: 20px; letter-spacing: -0.015em; }}
  .story-body p {{ font-size: 16.5px; margin-bottom: 18px; line-height: 1.82; }}
  .story-body p:last-child {{ margin-bottom: 0; }}
  .story-body > p:first-child::first-letter {{ font-family: 'Playfair Display', serif;
    font-size: 4.2em; font-weight: 700; float: left; line-height: 0.72;
    margin: 0.05em 0.12em 0 0; color: var(--rust); }}
  .pull {{ margin: 28px 0; padding: 18px 24px;
    border-left: 4px solid var(--rust); background: var(--paper-dark);
    font-family: 'Playfair Display', serif; font-style: italic;
    font-size: 17.5px; color: var(--slate); line-height: 1.6; }}
  .context {{ margin-top: 30px; background: var(--paper-mid);
    border-radius: 3px; overflow: hidden; }}
  .context-header {{ background: var(--gold); padding: 9px 18px;
    font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    letter-spacing: 0.28em; text-transform: uppercase; color: white; }}
  .context-body {{ padding: 18px 20px 16px; }}
  .context-body p {{ font-size: 14.5px; color: var(--slate);
    line-height: 1.72; margin-bottom: 12px; }}
  .context-body p:last-child {{ margin-bottom: 0; }}
  .sources {{ margin-top: 20px; padding-top: 16px;
    border-top: 1px dashed var(--divider); }}
  .sources-header {{ font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    text-transform: uppercase; letter-spacing: 0.22em;
    color: var(--muted); margin-bottom: 14px; }}
  .source-row {{ display: grid; grid-template-columns: auto 1fr;
    gap: 10px 14px; align-items: start; margin-bottom: 13px; }}
  .sbadge {{ display: inline-flex; align-items: center; gap: 5px;
    font-family: 'IBM Plex Mono', monospace; font-size: 10.5px;
    font-weight: 500; padding: 3px 9px; border-radius: 3px;
    white-space: nowrap; border: 1.5px solid; line-height: 1.4; }}
  .sbadge .sdot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
  .sbadge.l  {{ color:var(--left);        border-color:var(--left);        background:rgba(91,155,214,.07); }}
  .sbadge.cl {{ color:var(--center-left); border-color:var(--center-left); background:rgba(74,176,192,.07); }}
  .sbadge.c  {{ color:var(--center);      border-color:var(--center);      background:rgba(122,170,80,.07); }}
  .sbadge.cr {{ color:var(--center-right);border-color:var(--center-right);background:rgba(200,160,64,.07); }}
  .sbadge.r  {{ color:var(--right);       border-color:var(--right);       background:rgba(217,107,58,.08); }}
  .sbadge.n  {{ color:var(--neutral);     border-color:var(--neutral);     background:rgba(144,144,144,.07); }}
  .source-note {{ font-size: 13px; color: var(--muted); line-height: 1.57; padding-top: 2px; }}
  .source-note strong {{ color: var(--slate); font-weight: 600; font-style: italic; }}
  .footer {{ text-align: center; margin-top: 64px; padding-top: 32px;
    border-top: 3px double var(--divider); }}
  .footer-orn {{ font-family: 'Playfair Display', serif; font-size: 22px;
    color: var(--divider); letter-spacing: 14px; margin-bottom: 16px; }}
  .footer p {{ font-family: 'IBM Plex Mono', monospace; font-size: 10.5px;
    color: var(--muted); letter-spacing: 0.06em; line-height: 1.9; }}
  .send-block {{ margin-top: 36px; padding: 22px 24px;
    background: var(--paper-dark); border: 1px solid var(--divider);
    border-radius: 4px; text-align: left; }}
  .send-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    text-transform: uppercase; letter-spacing: 0.25em;
    color: var(--gold); margin-bottom: 12px; }}
  .send-row {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .send-input {{ flex: 1; min-width: 220px; background: var(--paper-mid);
    border: 1px solid var(--divider); border-radius: 3px; color: var(--ink);
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    padding: 9px 12px; outline: none; transition: border-color 0.2s; }}
  .send-input:focus {{ border-color: var(--gold); }}
  .send-input::placeholder {{ color: var(--muted); }}
  .send-btn {{ background: var(--gold); color: #16130e; border: none;
    border-radius: 3px; font-family: 'IBM Plex Mono', monospace;
    font-size: 11px; font-weight: 500; letter-spacing: 0.08em;
    padding: 9px 18px; cursor: pointer; white-space: nowrap;
    transition: opacity 0.15s; }}
  .send-btn:hover {{ opacity: 0.85; }}
  .send-hint {{ margin-top: 9px; font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: var(--muted); line-height: 1.5; }}
  @media (max-width: 580px) {{
    .wrapper {{ padding: 0 16px 64px; }}
    .masthead {{ padding: 36px 0 20px; }}
    .source-row {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="wrapper">
"""

HTML_MASTHEAD = """
  <header class="masthead">
    <div class="masthead-eyebrow">Edição {weekday} · Suécia em português</div>
    <h1>Digest <em>Sueco</em></h1>
    <div class="masthead-meta">
      <span>{date}</span>
      <span>Göteborg → Brasil</span>
      <span>{n_stories} notícias</span>
    </div>
  </header>

  <div class="legend">
    <div class="legend-title">Posicionamento político das fontes</div>
    <div class="legend-items">
      <div class="legend-item"><span class="ldot l"></span> Esquerda</div>
      <div class="legend-item"><span class="ldot cl"></span> Centro-esquerda</div>
      <div class="legend-item"><span class="ldot c"></span> Centro / Público</div>
      <div class="legend-item"><span class="ldot cr"></span> Centro-direita</div>
      <div class="legend-item"><span class="ldot r"></span> Direita</div>
      <div class="legend-item"><span class="ldot n"></span> Institucional</div>
    </div>
  </div>

  <div class="section-title">Política sueca · últimos 3 dias</div>
"""

HTML_STORY = """
  <article class="story">
    <div class="story-meta">
      <span class="tag {tag_class}">{tag}</span>
      <span class="story-date">{date_str}</span>
    </div>
    <h2>{headline}</h2>
    <div class="story-body">
      {paragraphs_html}
    </div>
    <div class="pull">{pull_quote}</div>
    <div class="context">
      <div class="context-header">Contexto &amp; Fontes Usadas</div>
      <div class="context-body">
        {context_html}
        <div class="sources">
          <div class="sources-header">Fontes lidas diretamente nesta notícia</div>
          {sources_html}
        </div>
      </div>
    </div>
  </article>
"""

HTML_FOOTER = """
  <footer class="footer">
    <div class="footer-orn">— ✦ —</div>
    <p>
      Digest Sueco · notícias políticas da Suécia em português<br>
      Fontes: SVT Nyheter, Sveriges Radio/Ekot, Regeringen.se, Morgontidningen<br>
      Posicionamentos baseados no Reuters Institute &amp; Nordicom (Univ. Gotemburgo)<br><br>
      <strong>Göteborg · {date}</strong>
    </p>
    <div class="send-block">
      <div class="send-label">Enviar esta edição por email</div>
      <div class="send-row">
        <input type="email" id="recipientInput" class="send-input"
          placeholder="email@exemplo.com  (separe vários com vírgula)" />
        <button class="send-btn" onclick="openGmail()">Abrir no Gmail ↗</button>
      </div>
      <div class="send-hint">Abre um rascunho no Gmail já preenchido. Você só clica em Enviar.</div>
    </div>
  </footer>
</div>

<script>
function openGmail() {{
  const raw = document.getElementById('recipientInput').value.trim();
  const to = raw || '';
  const subject = encodeURIComponent('Digest Sueco · {date}');
  const stories = document.querySelectorAll('.story');
  let body = 'DIGEST SUECO · {date}\\nNotícias políticas da Suécia em português\\n' + '─'.repeat(42) + '\\n\\n';
  stories.forEach((story, i) => {{
    const tag  = story.querySelector('.tag')?.innerText || '';
    const h2   = story.querySelector('h2')?.innerText || '';
    const paras = story.querySelectorAll('.story-body p');
    let text = '';
    paras.forEach(p => {{ text += p.innerText + '\\n\\n'; }});
    body += (i+1) + '. [' + tag + ']\\n' + h2 + '\\n\\n' + text.trim() + '\\n\\n' + '─'.repeat(42) + '\\n\\n';
  }});
  const url = 'https://mail.google.com/mail/?view=cm&fs=1'
    + (to ? '&to=' + encodeURIComponent(to) : '')
    + '&su=' + subject
    + '&body=' + encodeURIComponent(body);
  window.open(url, '_blank');
}}
document.getElementById('recipientInput').addEventListener('keydown', e => {{ if (e.key==='Enter') openGmail(); }});
</script>
</body>
</html>
"""

# ── builder ───────────────────────────────────────────────
def build_html(data: dict) -> str:
    html = HTML_HEAD.format(date=data["date"])
    html += HTML_MASTHEAD.format(
        weekday=data["weekday"],
        date=data["date"],
        n_stories=len(data["stories"])
    )

    for story in data["stories"]:
        paras_html = "\n      ".join(
            f"<p>{p}</p>" for p in story["paragraphs"]
        )
        context_html = "\n        ".join(
            f"<p>{p}</p>" for p in story["context"].split("\n\n") if p.strip()
        )
        sources_html = ""
        for src in story["sources"]:
            bc = src["bias_class"]
            color_map = {
                "l":"var(--left)","cl":"var(--center-left)","c":"var(--center)",
                "cr":"var(--center-right)","r":"var(--right)","n":"var(--neutral)"
            }
            col = color_map.get(bc, "var(--neutral)")
            sources_html += f"""
          <div class="source-row">
            <span class="sbadge {bc}"><span class="sdot" style="background:{col}"></span>{src['name']}</span>
            <span class="source-note"><strong>{src['article']}</strong> {src['note']}</span>
          </div>"""

        html += HTML_STORY.format(
            tag=story["tag"],
            tag_class=story.get("tag_class", "politica"),
            date_str=story["date_str"],
            headline=story["headline"],
            paragraphs_html=paras_html,
            pull_quote=story["pull_quote"],
            context_html=context_html,
            sources_html=sources_html,
        )

    html += HTML_FOOTER.format(date=data["date"])
    return html


# ── main ──────────────────────────────────────────────────
def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não encontrada nas variáveis de ambiente.")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Gerando digest para {DATE_PTBR}...")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT}],
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }]
    )

    # Extrai o JSON da resposta
    raw = ""
    for block in message.content:
        if block.type == "text":
            raw = block.text
            break

    # Remove eventuais markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    data = json.loads(raw)

    html = build_html(data)

    # Salva como index.html na raiz do projeto
    out_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ index.html gerado com {len(data['stories'])} notícias.")


if __name__ == "__main__":
    main()
