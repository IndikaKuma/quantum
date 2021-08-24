import logging

import connexion

logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__, specification_dir="openapi/")
app.add_api('datapreparation-api.yaml',
            arguments={'title': 'QHana Data Preparation Microservice'})
app.run(host='0.0.0.0', port=5002, debug=True)
