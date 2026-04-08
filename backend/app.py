import os
import io
import logging
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from docxtpl import DocxTemplate
from datetime import datetime

# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 🔥 CORS SIMPLES E FUNCIONAL
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'base-contrato.docx')


# ================= FUNÇÕES =================
def format_currency(value, format_for='calculation'):
    try:
        if isinstance(value, (int, float)):
            value_float = float(value)
        else:
            value_str = str(value).replace('R$', '').strip()
            value_float = float(value_str.replace('.', '').replace(',', '.'))

        if format_for == 'display':
            return f"{value_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return value_float
    except:
        return 0.0 if format_for == 'calculation' else "0,00"


# ================= ROTAS =================

@app.route('/wake-up')
def wake_up():
    return jsonify({
        "status": "awake",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/healthcheck')
def healthcheck():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/gerar-contrato', methods=['POST'])
def generate_contract():
    try:
        logger.info("Gerando contrato...")

        # Verifica template
        if not os.path.exists(TEMPLATE_PATH):
            return jsonify({"error": "Template não encontrado"}), 500

        # Verifica JSON
        if not request.is_json:
            return jsonify({"error": "Envie JSON"}), 400

        data = request.json

        # Campos obrigatórios
        required_fields = [
            'comprador', 'cpfComprador', 'enderecoComprador',
            'cidadeComprador', 'ufComprador',
            'marca', 'modelo', 'placa',
            'renavam', 'valor', 'formaPagamento'
        ]

        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400

        # Endereço
        parts = data['enderecoComprador'].split(',')
        address = parts[0].strip() if len(parts) > 0 else ""
        number = parts[1].strip() if len(parts) > 1 else "S/N"
        neighborhood = parts[2].strip() if len(parts) > 2 else ""

        # Valores
        value = format_currency(data.get('valor', 0))
        discount = format_currency(data.get('desconto', 0))
        final_value = value - discount

        today = datetime.now()

        context = {
            'NOME': data['comprador'],
            'CPF_CNPJ': data['cpfComprador'],
            'ENDERECO': address,
            'NUMERO': number,
            'BAIRRO': neighborhood,
            'CIDADE': data['cidadeComprador'],
            'ESTADO_UF': data['ufComprador'],
            'CEP': data.get('cepComprador', ''),
            'TELEFONE_CELULAR': data.get('telefoneComprador', ''),
            'EMAIL': data.get('emailComprador', ''),
            'MARCA': data['marca'],
            'MODELO': data['modelo'],
            'COR': data.get('cor', ''),
            'COMBUSTÍVEL': data.get('combustivel', ''),
            'DIA_MES_ANO': today.strftime('%d/%m/%Y'),
            'ANO_FAB': data.get('anoFab', ''),
            'ANO_MOD': data.get('anoMod', ''),
            'QUILOMETRAGEM': data.get('quilometragem', '0'),
            'PLACA': data['placa'].upper(),
            'RENAVAM': data['renavam'],
            'CHASSI': data.get('chassi', '').upper(),
            'VALOR': format_currency(value, 'display'),
            'DESCONTO': format_currency(discount, 'display'),
            'VALOR_FINAL': format_currency(final_value, 'display'),
            'FORMA_PAGAMENTO': data['formaPagamento'],
            'IPVA': data.get('ipva', 'PAGO'),
            'MULTAS': data.get('multas', 'NÃO'),
            'DIA': today.strftime('%d'),
            'MES': today.strftime('%m'),
            'ANO': today.strftime('%Y'),
            'NOME_2': data['comprador'],
            'CPF_CNPJ_2': data['cpfComprador']
        }

        # Gerar DOCX
        doc = DocxTemplate(TEMPLATE_PATH)
        doc.render(context)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f"{data['comprador'].upper()}.docx"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logger.error(e, exc_info=True)
        return jsonify({"error": "Erro interno"}), 500


# ================= RUN =================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
