import logging

import connexion

logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__, specification_dir="openapi/")
app.add_api('classification-api.yaml',
            arguments={'title': 'Classification API'})
app.run(host='0.0.0.0', port=5000, debug=True)
