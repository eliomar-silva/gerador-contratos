# Gerador de Contratos Automatizado

Sistema para gerar contratos de compra e venda a partir de XMLs de notas fiscais.

## Estrutura de Pastas

- `frontend/`: Interface do usuário (HTML/CSS/JS)
- `backend/`: Servidor Python com lógica de geração de contratos
  - `app.py`: Servidor Flask
  - `requirements.txt`: Dependências Python
  - `base-contrato.docx`: Template do contrato

## Como Executar

### Pré-requisitos

- Python 3.7+
- Node.js (opcional para servidor frontend)

### Passo a Passo

1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py