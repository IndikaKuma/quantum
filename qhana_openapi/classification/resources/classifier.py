import connexion
from flask import jsonify

from SPSAOptimizer import SPSAOptimizer
from circuitExecutor import CircuitExecutor
from decisionBoundaryPlotter import DecisionBoundaryPlotter
from fileService import FileService
from listSerializer import ListSerializer
from numpySerializer import NumpySerializer
from pickleSerializer import PickleSerializer
from resultsSerializer import ResultsSerializer
from variationalSVMCircuitGenerator import VariationalSVMCircuitGenerator


def generate_url(url_root, route, file_name):
    return url_root + '/static/' + route + '/' + file_name + '.txt'


class Classifier:
    @staticmethod
    def initialize(job_id, data_url, optimizer_parameters_url, entanglement, feature_map_reps, variational_form_reps):
        """
               Initialize variational SVM classification
               * generates circuit template
               * initializes optimization parameters
           """

        # response parameters
        message = 'success'
        status_code = 200

        # # load the data from url or json body
        # data_url = request.args.get('data-url', type=str)
        # if data_url is None:
        #     data_url = (request.get_json())['data-url']
        #
        # if optimizer_parameters_url is None:
        #     optimizer_parameters_url = (request.get_json())['optimizer-parameters-url']

        # entanglement = request.args.get('entanglement', type=str, default='full')
        # feature_map_reps = request.args.get('feature-map-reps', type=int, default=1)
        # variational_form_reps = request.args.get('variational-form-reps', type=int, default=3)

        # file paths (inputs)
        data_file_path = './static/variational-svm-classification/initialization/data' \
                         + str(job_id) + '.txt'
        optimizer_parameters_file_path = './static/variational-svm-classification/initialization/optimizer-parameters' \
                                         + str(job_id) + '.txt'

        # file paths (outputs)
        circuit_template_file_path = './static/variational-svm-classification/initialization/circuit-template' \
                                     + str(job_id) + '.txt'
        thetas_file_path = './static/variational-svm-classification/initialization/thetas' \
                           + str(job_id) + '.txt'
        thetas_plus_file_path = './static/variational-svm-classification/initialization/thetas-plus' \
                                + str(job_id) + '.txt'
        thetas_minus_file_path = './static/variational-svm-classification/initialization/thetas-minus' \
                                 + str(job_id) + '.txt'
        delta_file_path = './static/variational-svm-classification/initialization/delta' \
                          + str(job_id) + '.txt'
        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/variational-svm-classification/initialization/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path,
                                        optimizer_parameters_file_path,
                                        circuit_template_file_path,
                                        thetas_file_path,
                                        thetas_plus_file_path,
                                        thetas_minus_file_path,
                                        delta_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_url, data_file_path)
            FileService.download_to_file(optimizer_parameters_url, optimizer_parameters_file_path)

            # deserialize the data
            data = NumpySerializer.deserialize(data_file_path)

            # TODO: Make feature map and variational form selectable
            # generate circuit template
            n_dimensions = data.shape[1]
            circuit_template, feature_map_parameters, var_form_parameters = \
                VariationalSVMCircuitGenerator.generateCircuitTemplate(n_dimensions, feature_map_reps,
                                                                       variational_form_reps, entanglement)

            # store circuit template
            # TODO: Fix problems with deserialization, then use
            # circuit_template = QiskitSerializer.deserialize(circuit_template_file_path)
            # WORKAROUND until https://github.com/Qiskit/qiskit-terra/issues/5710 is fixed
            PickleSerializer.serialize(circuit_template, circuit_template_file_path)

            # TODO: Optimizer initialization is still specific to SPSA optimizer -> generalize
            # deserialize optimizer parameters
            optimizer_parameters = NumpySerializer.deserialize(optimizer_parameters_file_path)
            if len(optimizer_parameters) is not 5:
                raise Exception("Wrong number of optimizer parameters. 5 parameters c0 through c4 expected.")

            # initialize thetas for optimization
            n_thetas = len(var_form_parameters)
            thetas, thetas_plus, thetas_minus, delta = SPSAOptimizer.initializeOptimization(n_thetas,
                                                                                            optimizer_parameters)

            NumpySerializer.serialize(thetas, thetas_file_path)
            NumpySerializer.serialize(thetas_plus, thetas_plus_file_path)
            NumpySerializer.serialize(thetas_minus, thetas_minus_file_path)
            NumpySerializer.serialize(delta, delta_file_path)

            # generate urls
            url_root = connexion.request.host_url
            circuit_template_url = generate_url(url_root,
                                                'variational-svm-classification/initialization',
                                                'circuit-template' + str(job_id))
            thetas_url = generate_url(url_root,
                                      'variational-svm-classification/initialization',
                                      'thetas' + str(job_id))
            thetas_plus_url = generate_url(url_root,
                                           'variational-svm-classification/initialization',
                                           'thetas-plus' + str(job_id))
            thetas_minus_url = generate_url(url_root,
                                            'variational-svm-classification/initialization',
                                            'thetas-minus' + str(job_id))
            delta_url = generate_url(url_root,
                                     'variational-svm-classification/initialization',
                                     'delta' + str(job_id))


        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       circuit_template_url=circuit_template_url,
                       thetas_url=thetas_url,
                       thetas_plus_url=thetas_plus_url,
                       thetas_minus_url=thetas_minus_url,
                       delta_url=delta_url), status_code

    @staticmethod
    def generates_circuit_parameterizations(job_id, data_url, circuit_template_url, thetas_url, thetas_plus_url,
                                            thetas_minus_url):
        """
            Generate circuit parameterizations
            * takes circuit template, data, and thetas to generate parameterizations for the circuit execution
        """

        # response parameters
        message = 'success'
        status_code = 200

        # file paths (inputs)
        data_file_path = './static/variational-svm-classification/circuit-generation/data' \
                         + str(job_id) + '.txt'
        circuit_template_file_path = './static/variational-svm-classification/circuit-generation/circuit-template' \
                                     + str(job_id) + '.txt'
        thetas_file_path = './static/variational-svm-classification/circuit-generation/thetas' \
                           + str(job_id) + '.txt'
        thetas_plus_file_path = './static/variational-svm-classification/circuit-generation/thetas-plus' \
                                + str(job_id) + '.txt'
        thetas_minus_file_path = './static/variational-svm-classification/circuit-generation/thetas-minus' \
                                 + str(job_id) + '.txt'

        # file paths (outputs)
        parameterizations_file_path = './static/variational-svm-classification/circuit-generation/parameterizations' \
                                      + str(job_id) + '.txt'

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/variational-svm-classification/circuit-generation/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path,
                                        circuit_template_file_path,
                                        thetas_file_path,
                                        thetas_plus_file_path,
                                        thetas_minus_file_path,
                                        parameterizations_file_path)

            # download and store locally
            FileService.download_to_file(data_url, data_file_path)
            FileService.download_to_file(circuit_template_url, circuit_template_file_path)

            if thetas_url is not None and thetas_url != '':
                FileService.download_to_file(thetas_url, thetas_file_path)
            if thetas_plus_url is not None and thetas_plus_url != '':
                FileService.download_to_file(thetas_plus_url, thetas_plus_file_path)
            if thetas_minus_url is not None and thetas_minus_url != '':
                FileService.download_to_file(thetas_minus_url, thetas_minus_file_path)

            # deserialize inputs
            data = NumpySerializer.deserialize(data_file_path)

            # TODO: Fix problems with deserialization, then use
            # circuit_template = QiskitSerializer.deserialize(circuit_template_file_path)
            # WORKAROUND until https://github.com/Qiskit/qiskit-terra/issues/5710 is fixed
            circuit_template = PickleSerializer.deserialize(circuit_template_file_path)

            thetas = NumpySerializer.deserialize(
                thetas_file_path) if thetas_url is not None and thetas_url != '' else None
            thetas_plus = NumpySerializer.deserialize(
                thetas_plus_file_path) if thetas_plus_url is not None and thetas_plus_url != '' else None
            thetas_minus = NumpySerializer.deserialize(
                thetas_minus_file_path) if thetas_minus_url is not None and thetas_minus_url != '' else None

            thetas_array = []
            for t in [thetas, thetas_plus, thetas_minus]:
                if t is not None:
                    thetas_array.append(t)

            # generate parameterizations
            parameterizations = VariationalSVMCircuitGenerator.generateCircuitParameterizations(circuit_template, data,
                                                                                                thetas_array)

            # serialize outputs
            ListSerializer.serialize(parameterizations, parameterizations_file_path)

            url_root = connexion.request.host_url
            parameterizations_url = generate_url(url_root,
                                                 'variational-svm-classification/circuit-generation',
                                                 'parameterizations' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       parameterizations_url=parameterizations_url)

    @staticmethod
    def execute_circuits(job_id, circuit_template_url, parameterizations_url, backend_name, token, shots):
        """
            Execute circuits
            * assigns parameters of circuit template for each parameterization
            * runs the circuit for each parameterization
            * returns results as a list
        """

        # response parameters
        message = 'success'
        status_code = 200

        # file paths (inputs)
        circuit_template_file_path = './static/variational-svm-classification/circuit-execution/circuit-template' \
                                     + str(job_id) + '.txt'
        parameterizations_file_path = './static/variational-svm-classification/circuit-execution/parameterizations' \
                                      + str(job_id) + '.txt'

        # file paths (outputs)
        results_file_path = './static/variational-svm-classification/circuit-execution/results' \
                            + str(job_id) + '.txt'

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/variational-svm-classification/circuit-execution/')

            # delete old files if exist
            FileService.delete_if_exist(circuit_template_file_path,
                                        parameterizations_file_path,
                                        results_file_path)

            # download and store locally
            FileService.download_to_file(circuit_template_url, circuit_template_file_path)
            FileService.download_to_file(parameterizations_url, parameterizations_file_path)

            # deserialize inputs

            # TODO: Fix problems with deserialization, then use
            # circuit_template = QiskitSerializer.deserialize(circuit_template_file_path)
            # WORKAROUND until https://github.com/Qiskit/qiskit-terra/issues/5710 is fixed
            circuit_template = PickleSerializer.deserialize(circuit_template_file_path)

            parameterizations = ListSerializer.deserialize(parameterizations_file_path)

            results, is_statevector = CircuitExecutor.runCircuit(circuit_template, parameterizations, backend_name,
                                                                 token,
                                                                 shots, add_measurements=True)

            ResultsSerializer.serialize(results, results_file_path)
            url_root = connexion.request.host_url
            results_url = generate_url(url_root,
                                       'variational-svm-classification/circuit-execution',
                                       'results' + str(job_id))
        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       results_url=results_url,
                       is_statevector=is_statevector)

    #
    #
    # @app.route('/api/variational-svm-classification/optimization/<int:job_id>', methods=['POST'])
    @staticmethod
    def optimize(job_id, results_url, labels_url, thetas_in_url, delta_in_url, optimizer_parameters_url, iteration,
                 is_statevector):
        """
            Optimize parameters
            * evaluates the results from circuit execution
            * optimizes thetas using SPSA optimizer
            * generates thetas and delta for the next round (thetas_plus, thetas_minus)
        """

        # response parameters
        message = 'success'
        status_code = 200

        is_statevector = False if is_statevector in ['False', '', 'No', 'None'] else True

        # file paths (inputs)
        results_file_path = './static/variational-svm-classification/optimization/results' \
                            + str(job_id) + '.txt'
        labels_file_path = './static/variational-svm-classification/optimization/labels' \
                           + str(job_id) + '.txt'
        thetas_in_file_path = './static/variational-svm-classification/optimization/thetas-in' \
                              + str(job_id) + '.txt'
        delta_in_file_path = './static/variational-svm-classification/optimization/delta-in' \
                             + str(job_id) + '.txt'
        optimizer_parameters_file_path = './static/variational-svm-classification/optimization/optimizer-parameters' \
                                         + str(job_id) + '.txt'

        # file paths (inputs)
        thetas_out_file_path = './static/variational-svm-classification/optimization/thetas-out' \
                               + str(job_id) + '.txt'
        thetas_plus_file_path = './static/variational-svm-classification/optimization/thetas-plus' \
                                + str(job_id) + '.txt'
        thetas_minus_file_path = './static/variational-svm-classification/optimization/thetas-minus' \
                                 + str(job_id) + '.txt'
        delta_out_file_path = './static/variational-svm-classification/optimization/delta-out' \
                              + str(job_id) + '.txt'

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/variational-svm-classification/optimization/')

            # delete old files if exist
            FileService.delete_if_exist(results_file_path,
                                        labels_file_path,
                                        thetas_in_file_path,
                                        delta_in_file_path,
                                        optimizer_parameters_file_path,
                                        thetas_out_file_path,
                                        thetas_plus_file_path,
                                        thetas_minus_file_path,
                                        delta_out_file_path)

            # download and store locally
            FileService.download_to_file(results_url, results_file_path)
            FileService.download_to_file(labels_url, labels_file_path)
            FileService.download_to_file(thetas_in_url, thetas_in_file_path)
            FileService.download_to_file(delta_in_url, delta_in_file_path)
            FileService.download_to_file(optimizer_parameters_url, optimizer_parameters_file_path)

            results = ResultsSerializer.deserialize(results_file_path)
            labels = NumpySerializer.deserialize(labels_file_path)
            thetas = NumpySerializer.deserialize(thetas_in_file_path)
            delta = NumpySerializer.deserialize(delta_in_file_path)
            optimizer_parameters = NumpySerializer.deserialize(optimizer_parameters_file_path)

            # make that sure labels are integers
            labels = labels.astype(int)

            thetas_out, thetas_plus, thetas_minus, delta_out, costs_curr = \
                SPSAOptimizer.optimize(results, labels, thetas, delta, iteration, optimizer_parameters, is_statevector)

            NumpySerializer.serialize(thetas_out, thetas_out_file_path)
            NumpySerializer.serialize(thetas_plus, thetas_plus_file_path)
            NumpySerializer.serialize(thetas_minus, thetas_minus_file_path)
            NumpySerializer.serialize(delta_out, delta_out_file_path)

            # generate urls
            url_root = connexion.request.host_url
            thetas_out_url = generate_url(url_root,
                                          'variational-svm-classification/optimization',
                                          'thetas-out' + str(job_id))
            thetas_plus_url = generate_url(url_root,
                                           'variational-svm-classification/optimization',
                                           'thetas-plus' + str(job_id))
            thetas_minus_url = generate_url(url_root,
                                            'variational-svm-classification/optimization',
                                            'thetas-minus' + str(job_id))
            delta_url = generate_url(url_root,
                                     'variational-svm-classification/optimization',
                                     'delta-out' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       thetas_out_url=thetas_out_url,
                       thetas_plus_url=thetas_plus_url,
                       thetas_minus_url=thetas_minus_url,
                       delta_url=delta_url,
                       costs_curr=costs_curr)

    @staticmethod
    def generate_grid(job_id, data_url, resolution):
        """
            Takes original data and generates a grid of new data points that surrounds original data
            - resolution parameter r determines the dimensions of the grid, e.g. r x r for 2 dimensional data
        """

        # response parameters
        message = 'success'
        status_code = 200

        # load the data from url or json body

        # file paths (inputs)
        data_file_path = './static/plots/grid-generation/data' \
                         + str(job_id) + '.txt'

        # file paths (inputs)
        grid_file_path = './static/plots/grid-generation/grid' \
                         + str(job_id) + '.txt'

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/plots/grid-generation/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path,
                                        grid_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_url, data_file_path)

            # deserialize the data
            data = NumpySerializer.deserialize(data_file_path)

            grid = DecisionBoundaryPlotter.generate_grid(data, resolution)

            NumpySerializer.serialize(grid, grid_file_path)

            # generate urls
            url_root = connexion.request.host_url
            grid_url = generate_url(url_root,
                                    'plots/grid-generation',
                                    'grid' + str(job_id))
        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       grid_url=grid_url)

    # # TODO: Remove when QuantumCircuit serialization/deserialization is fixed
    #
    # @app.route('/api/plots/prediction/<int:job_id>', methods=['POST'])
    @staticmethod
    def predict(job_id, results_url, n_classes, is_statevector):
        """
            Predict
            * evaluates results and computes predictions from them
        """

        # response parameters
        message = 'success'
        status_code = 200

        is_statevector = False if is_statevector in ['False', '', 'No', 'None'] else True

        # file paths (inputs)
        results_file_path = './static/plots/predictions/results' \
                            + str(job_id) + '.txt'

        # file paths (inputs)
        labels_file_path = './static/plots/predictions/labels' \
                           + str(job_id) + '.txt'

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/plots/predictions/')

            # delete old files if exist
            FileService.delete_if_exist(results_file_path,
                                        labels_file_path)

            # download and store locally
            FileService.download_to_file(results_url, results_file_path)

            results = ResultsSerializer.deserialize(results_file_path)

            labels = DecisionBoundaryPlotter.predict(results, n_classes, is_statevector)

            NumpySerializer.serialize(labels, labels_file_path)

            # generate urls
            url_root = connexion.request.host_url
            predictions_url = generate_url(url_root,
                                           'plots/predictions',
                                           'labels' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       predictions_url=predictions_url)

    #
    #
    # @app.route('/api/plots/plot/<int:job_id>', methods=['POST'])
    @staticmethod
    def plot_boundary(job_id, data_url, labels_url, grid_url, predicitons_url):
        """
            Plots data and decision boundary
        """

        # response parameters
        message = 'success'
        status_code = 200

        # file paths (inputs)
        data_file_path = './static/plots/plot/data' \
                         + str(job_id) + '.txt'

        labels_file_path = './static/plots/plot/labels' \
                           + str(job_id) + '.txt'

        grid_file_path = './static/plots/plot/grid' \
                         + str(job_id) + '.txt'

        predictions_file_path = './static/plots/plot/predictions' \
                                + str(job_id) + '.txt'

        # file paths (outputs)
        plot_file_path = './static/plots/plot/plot' \
                         + str(job_id) + '.png'

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/plots/plot/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path,
                                        labels_file_path,
                                        grid_file_path,
                                        predictions_file_path,
                                        plot_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_url, data_file_path)
            FileService.download_to_file(labels_url, labels_file_path)
            FileService.download_to_file(grid_url, grid_file_path)
            FileService.download_to_file(predicitons_url, predictions_file_path)

            # deserialize the data
            data = NumpySerializer.deserialize(data_file_path)
            labels = NumpySerializer.deserialize(labels_file_path)
            grid = NumpySerializer.deserialize(grid_file_path)
            predictions = NumpySerializer.deserialize(predictions_file_path)

            labels = labels.astype(int)
            predictions = predictions.astype(int)

            DecisionBoundaryPlotter.save_plot(data, labels, grid, predictions, plot_file_path)

            # generate urls
            url_root = connexion.request.host_url
            plot_url = url_root + '/static/plots/plot/plot' + str(job_id) + '.png'

        except Exception as ex:
            message = str(ex)
            status_code = 500
            return jsonify(message=message, status_code=status_code)

        return jsonify(message=message,
                       status_code=status_code,
                       plot_url=plot_url)

# # @app.route('/static/variational-svm-classification/initialization/circuit-template<int:job_id>.txt', methods=['GET'])
#     def get_pickle_circuit(job_id):
#         payload = open('./static/variational-svm-classification/initialization/circuit-template' + str(job_id) + '.txt',
#                        'rb').read()
#         content_type = 'application/python-pickle'
#         return Response(response=payload, mimetype=content_type)
