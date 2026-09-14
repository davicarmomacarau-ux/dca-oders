# DCA Orders

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Inter&size=34&duration=2500&pause=1000&color=7C8E6A&center=true&vCenter=true&width=820&lines=DCA+Orders%3A+Marketplace+de+Pedidos;WhatsApp+First+Commerce;Flask+SQLite+HTML+CSS+JS" alt="DCA Orders" />

</div>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14+-green" />
  <img src="https://img.shields.io/badge/flask-3.1.2-blue" />
  <img src="https://img.shields.io/badge/sqlite-local-lightgrey" />
  <img src="https://img.shields.io/badge/whatsapp-integrado-25D366" />
</p>

## 🚀 Visão geral

O DCA Orders é uma plataforma de pedidos digitais para restaurantes, lanchonetes e padarias com:

- cardápio com carrinho e checkout;
- cadastro de lojas;
- fluxo de marketplace com campanhas, ofertas e ranking por ROI;
- integração com WhatsApp para pedidos e conversão;
- previsão por hora e público para campanhas.

## 🧩 Stack

- Python + Flask
- SQLite (fallback local)
- Jinja2 templates
- HTML + CSS + JavaScript
- PostgreSQL-ready design prepared for future production migration

## 🌍 Como rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abra:

http://127.0.0.1:5000

## 🏪 Fluxos principais

### Cadastro de loja

```text
/register
```

### Cardápio

```text
/menu/<slug>
```

### Admin

```text
/admin
```

### Marketplace

```text
/marketplace
```

## 📣 Integração WhatsApp

O projeto gera links oficiais com o formato:

```text
https://wa.me/<numero>?text=<mensagem>
```

com botão próprio para campanhas, ofertas e pedidos.

## 📦 Banco local

O projeto utiliza SQLite com fallback local em:

```text
dca_orders.sqlite3
```

## 🧪 Testes

```bash
python -m pytest -q
```

## 🧠 Roadmap

- migrar para PostgreSQL em produção;
- autenticação admin segura;
- painel de análise mais robusto;
- ranking comercial com dados reais e previsões por loja.

## ✨ Projeto

DCA Orders conecta loja, cardápio, WhatsApp e marketplace para criar operação digital com fluxo de pedidos e campanhas.
