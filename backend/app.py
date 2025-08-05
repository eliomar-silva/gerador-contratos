import os
import io
import logging
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from docxtpl import DocxTemplate
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enhanced CORS configuration
CORS(app, resources={
    r"/.*": {
        "origins": [
            "http://127.0.0.1:5500",
            "https://eliomar-silva.github.io",
            "https://eliomar-silva.github.io/gerador-contratos/frontend/"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 86400
    }
})

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'base-contrato.docx')

def format_currency(value, format_for='calculation'):
    """
    Converte e formata valores monetários
    :param value: Valor de entrada (string ou número)
    :param format_for: 'calculation' para float ou 'display' para string formatada
    :return: Float ou string formatada
    """
    try:
        if isinstance(value, (int, float)):
            value_float = float(value)
        else:
            value_str = str(value).replace('R$', '').strip()
            value_float = float(value_str.replace('.', '').replace(',', '.'))
        
        if format_for == 'display':
            # Formata como 00.000,00
            return f"{value_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return value_float
    except ValueError:
        logger.warning(f"Valor monetário inválido: {value}")
        return 0.0 if format_for == 'calculation' else "0,00"

@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    allowed_origins = [
        "http://127.0.0.1:5500",
        "https://eliomar-silva.github.io",
        "https://eliomar-silva.github.io/gerador-contratos/frontend/"
    ]
    origin = request.headers.get('Origin')
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/gerar-contrato', methods=['OPTIONS'])
def handle_options():
    """Handle CORS preflight requests"""
    return jsonify({"status": "ok"}), 200

@app.route('/gerar-contrato', methods=['POST'])
def generate_contract():
    """Main endpoint to generate contracts"""
    try:
        logger.info("Starting contract processing")
        
        # Verify template exists
        if not os.path.exists(TEMPLATE_PATH):
            error_msg = f"Template not found at {TEMPLATE_PATH}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

        # Validate content type
        if not request.is_json:
            error_msg = "Content-Type must be application/json"
            logger.warning(error_msg)
            return jsonify({"error": error_msg}), 400

        data = request.json
        logger.debug(f"Received data: {data}")
        
        # Validate required fields
        required_fields = [
            'comprador', 'cpfComprador', 'enderecoComprador', 'cidadeComprador',
            'ufComprador', 'marca', 'modelo', 'cor', 'combustivel', 'dataEmissao',
            'placa', 'renavam', 'valor', 'formaPagamento'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                error_msg = f"Missing required field: {field}"
                logger.warning(error_msg)
                return jsonify({"error": error_msg}), 400

        # Process address safely
        try:
            address_parts = [part.strip() for part in data['enderecoComprador'].split(',')]
            address = address_parts[0] if len(address_parts) > 0 else ""
            number = address_parts[1] if len(address_parts) > 1 else "S/N"
            neighborhood = address_parts[2] if len(address_parts) > 2 else ""
        except Exception as e:
            error_msg = f"Invalid address format: {str(e)}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400

        # Convert and validate monetary values
        try:
            value = format_currency(data.get('valor', '0'))
            discount = format_currency(data.get('desconto', '0'))
            final_value = value - discount
        except Exception as e:
            error_msg = f"Invalid monetary values: {str(e)}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400

        # Prepare template context
        emission_date = data.get('dataEmissao', datetime.now().strftime('%d/%m/%Y'))
        context = {
            'NOME': data['comprador'],
            'CPF_CNPJ': data.get('cpfComprador', ''),
            'ENDERECO': address,
            'NUMERO': number,
            'BAIRRO': neighborhood,
            'CIDADE': data.get('cidadeComprador', ''),
            'ESTADO_UF': data.get('ufComprador', ''),
            'CEP': data.get('cepComprador', ''),
            'TELEFONE_CELULAR': data.get('telefoneComprador', ''),
            'EMAIL': data.get('emailComprador', ''),
            'MARCA': data['marca'],
            'MODELO': data['modelo'],
            'COR': data.get('cor', ''),
            'COMBUSTÍVEL': data.get('combustivel', ''),
            'DIA_MES_ANO': emission_date,
            'ANO_FAB': data.get('anoFab', ''),
            'ANO_MOD': data.get('anoMod', ''),
            'QUILOMETRAGEM': data.get('quilometragem', '0'),
            'PLACA': data.get('placa', '').upper(),
            'RENAVAM': data.get('renavam', ''),
            'CHASSI': data.get('chassi', '').upper(),
            'VALOR': format_currency(data.get('valor', '0'), 'display'),
            'DESCONTO': format_currency(data.get('desconto', '0'), 'display'),
            'VALOR_FINAL': format_currency(final_value, 'display'),
            'FORMA_PAGAMENTO': data.get('formaPagamento', ''),
            'IPVA': data.get('ipva', 'PAGO'),
            'MULTAS': data.get('multas', 'NÃO'),
            'DIA_MES_ANO_2': emission_date,
            'DIA': data.get('dia', datetime.now().strftime('%d')),
            'MES': data.get('mes', datetime.now().strftime('%m')),
            'ANO': data.get('ano', datetime.now().strftime('%Y')),
            'NOME_2': data.get('comprador', ''),
            'CPF_CNPJ_2': data.get('cpfComprador', '')
        }

        logger.info("Rendering DOCX template")
        doc = DocxTemplate(TEMPLATE_PATH)
        doc.render(context)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        filename = f"Contrato_{data['comprador'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
        logger.info(f"Contract generated successfully: {filename}")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename
        )

    except KeyError as e:
        error_msg = f"Missing required field: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        error_msg = f"Error generating contract: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({"error": "An internal error occurred while generating the contract"}), 500

@app.route('/healthcheck', methods=['GET', 'OPTIONS'])
def healthcheck():
    """Service health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Gerador de Contratos",
        "version": "1.0.0",
        "endpoints": {
            "generate_contract": "/gerar-contrato (POST)",
            "healthcheck": "/healthcheck (GET)"
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)

