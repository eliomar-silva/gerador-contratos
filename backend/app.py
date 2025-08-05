import os
import io
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from docxtpl import DocxTemplate
from datetime import datetime

app = Flask(__name__)

# Configuração CORS segura (ajuste os domínios conforme necessário)
CORS(app, resources={
    r"/gerar-contrato": {
        "origins": [
            "http://127.0.0.1:5500",
            "https://eliomar-silva.github.io"
        ],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'base-contrato.docx')

@app.route('/gerar-contrato', methods=['POST', 'OPTIONS'])
def gerar_contrato():
    try:
        # Verificação inicial
        if not os.path.exists(TEMPLATE_PATH):
            return jsonify({"erro": f"Template não encontrado em {TEMPLATE_PATH}"}), 500

        if not request.is_json:
            return jsonify({"erro": "Content-Type deve ser application/json"}), 400

        dados = request.json
        
        # Validação dos campos obrigatórios
        campos_obrigatorios = [
            'comprador', 'cpfComprador', 'enderecoComprador', 'cidadeComprador',
            'ufComprador', 'marca', 'modelo', 'cor', 'combustivel', 'dataEmissao',
            'placa', 'renavam', 'valor', 'formaPagamento'
        ]
        
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return jsonify({"erro": f"Campo obrigatório faltando: {campo}"}), 400

        # Processamento seguro do endereço
        try:
            partes_endereco = dados['enderecoComprador'].split(',')
            endereco = partes_endereco[0].strip() if len(partes_endereco) > 0 else ""
            numero = partes_endereco[1].strip() if len(partes_endereco) > 1 else "S/N"
            bairro = partes_endereco[2].strip() if len(partes_endereco) > 2 else ""
        except Exception as e:
            return jsonify({"erro": f"Formato de endereço inválido: {str(e)}"}), 400

        # Contexto com valores padrão para campos opcionais
        contexto = {
            'NOME': dados['comprador'],
            'CPF_CNPJ': dados.get('cpfComprador', ''),
            'ENDERECO': endereco,
            'NUMERO': numero,
            'BAIRRO': bairro,
            'CIDADE': dados.get('cidadeComprador', ''),
            'ESTADO_UF': dados.get('ufComprador', ''),
            'CEP': dados.get('cepComprador', ''),
            'TELEFONE_CELULAR': dados.get('telefoneComprador', ''),
            'EMAIL': dados.get('emailComprador', ''),
            'MARCA': dados['marca'],
            'MODELO': dados['modelo'],
            'COR': dados.get('cor', ''),
            'COMBUSTÍVEL': dados.get('combustivel', ''),
            'DIA_MES_ANO': dados.get('dataEmissao', datetime.now().strftime('%d/%m/%Y')),
            'ANO_FAB': dados.get('anoFab', ''),
            'ANO_MOD': dados.get('anoMod', ''),
            'QUILOMETRAGEM': dados.get('quilometragem', '0'),
            'PLACA': dados.get('placa', '').upper(),
            'RENAVAM': dados.get('renavam', ''),
            'CHASSI': dados.get('chassi', '').upper(),
            'VALOR': dados.get('valor', '0,00'),
            'DESCONTO': dados.get('desconto', '0,00'),
            'VALOR - DESCONTO': dados.get('valorFinal', '0,00'),
            'FORMA_PAGAMENTO': dados.get('formaPagamento', ''),
            'IPVA': dados.get('ipva', 'PAGO'),
            'MULTAS': dados.get('multas', 'NÃO'),
            'DIA_MES_ANO_2': dados.get('dataEmissao', datetime.now().strftime('%d/%m/%Y')),
            'DIA': dados.get('dia', datetime.now().strftime('%d')),
            'MES': dados.get('mes', datetime.now().strftime('%m')),
            'ANO': dados.get('ano', datetime.now().strftime('%Y')),
            'NOME_2': dados.get('comprador', ''),
            'CPF_CNPJ_2': dados.get('cpfComprador', '')
        }

        # Geração do documento
        doc = DocxTemplate(TEMPLATE_PATH)
        doc.render(contexto)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"Contrato_{dados['comprador'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
        )

    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Erro ao gerar contrato: {str(e)}", exc_info=True)
        return jsonify({"erro": "Ocorreu um erro interno ao gerar o contrato"}), 500

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
