import logging

import connexion

logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__, specification_dir="openapi/")
app.add_api('clustering-api.yaml',
            arguments={'title': 'QHana Clustering Microservice'})
app.run(host='0.0.0.0', port=5001, debug=True)
