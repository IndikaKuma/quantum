"""
Author: Daniel Fink
Email: daniel-fink@outlook.com
"""

import os

import connexion
import numpy as np
from flask import request, jsonify
from sklearn.cluster import KMeans

from clusteringCircuitExecutor import ClusteringCircuitExecutor
from clusteringCircuitGenerator import ClusteringCircuitGenerator
from convergenceCalculationService import ConvergenceCalculationService
from dataProcessingService import DataProcessingService
from fileService import FileService
from numpySerializer import NumpySerializer
from qiskitSerializer import QiskitSerializer
from quantumBackendFactory import QuantumBackendFactory


def generate_url(url_root, route, file_name):
    return url_root + '/static/' + route + '/' + file_name + '.txt'


class Clusterer:

    @staticmethod
    def initialize_centroids(job_id, k):
        """
        Create k random centroids in the range [0, 1] x [0, 1].
        """
        centroids_file_path = './static/centroid-calculation/initialization/centroids' \
                              + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        centroids_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/centroid-calculation/initialization/')

            # delete old files if exist
            FileService.delete_if_exist(centroids_file_path)

            # generate k centroids
            centroids = DataProcessingService.generate_random_data(k)

            # serialize the data
            NumpySerializer.serialize(centroids, centroids_file_path)

            # generate urls
            url_root = connexion.request.host_url
            centroids_url = generate_url(url_root,
                                         'centroid-calculation/initialization',
                                         'centroids' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message,
                       status_code=status_code,
                       centroids_url=centroids_url)

    @staticmethod
    def calculate_angles(job_id, data_url, centroids_url, base_vector_x, base_vector_y):
        """
        Performs the pre processing of a general rotational clustering algorithm,
        i.e. the angle calculations.

        We take the data and centroids and calculate the centroid and data angles.
        """
        data_file_path = './static/angle-calculation/rotational-clustering/data' \
                         + str(job_id) + '.txt'
        centroids_file_path = './static/angle-calculation/rotational-clustering/centroids' \
                              + str(job_id) + '.txt'
        centroid_angles_file_path = './static/angle-calculation/rotational-clustering/centroid_angles' \
                                    + str(job_id) + '.txt'
        data_angles_file_path = './static/angle-calculation/rotational-clustering/data_angles' \
                                + str(job_id) + '.txt'

        base_vector = np.array([base_vector_x, base_vector_y])

        # response parameters
        message = 'success'
        status_code = 200
        data_angles_url = ''
        centroid_angles_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/angle-calculation/rotational-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path,
                                        centroids_file_path,
                                        centroid_angles_file_path,
                                        data_angles_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_url, data_file_path)
            FileService.download_to_file(centroids_url, centroids_file_path)

            # deserialize the data
            data = NumpySerializer.deserialize(data_file_path)
            centroids = NumpySerializer.deserialize(centroids_file_path)

            # map data and centroids to standardized unit sphere
            data = DataProcessingService.normalize(DataProcessingService.standardize(data))
            centroids = DataProcessingService.normalize(DataProcessingService.standardize(centroids))

            # calculate the angles
            data_angles = DataProcessingService.calculate_angles(data, base_vector)
            centroid_angles = DataProcessingService.calculate_angles(centroids, base_vector)

            # serialize the data
            NumpySerializer.serialize(data_angles, data_angles_file_path)
            NumpySerializer.serialize(centroid_angles, centroid_angles_file_path)

            # generate urls
            url_root = connexion.request.host_url
            data_angles_url = generate_url(url_root,
                                           'angle-calculation/rotational-clustering',
                                           'data_angles' + str(job_id))
            centroid_angles_url = generate_url(url_root,
                                               'angle-calculation/rotational-clustering',
                                               'centroid_angles' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message,
                       status_code=status_code,
                       data_angles_url=data_angles_url,
                       centroid_angles_url=centroid_angles_url)

    @staticmethod
    def generate_negative_rotation_circuits(job_id, data_angles_url, centroid_angles_url, max_qubits):
        """
        Generates the negative rotation clustering quantum circuits.

        We take the data and centroid angles and return a url to a file with the
        quantum circuits as qasm strings.
        """
        data_angles_file_path = './static/circuit-generation/negative-rotation-clustering/data_angles' \
                                + str(job_id) + '.txt'
        centroid_angles_file_path = './static/circuit-generation/negative-rotation-clustering/centroid_angles' \
                                    + str(job_id) + '.txt'
        circuits_file_path = './static/circuit-generation/negative-rotation-clustering/circuits' \
                             + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        circuits_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/circuit-generation/negative-rotation-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(data_angles_file_path, centroid_angles_file_path, circuits_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_angles_url, data_angles_file_path)
            FileService.download_to_file(centroid_angles_url, centroid_angles_file_path)

            # deserialize the data and centroid angles
            data_angles = NumpySerializer.deserialize(data_angles_file_path)
            centroid_angles = NumpySerializer.deserialize(centroid_angles_file_path)

            # perform circuit generation
            circuits = ClusteringCircuitGenerator.generate_negative_rotation_clustering(max_qubits,
                                                                                        data_angles,
                                                                                        centroid_angles)

            # serialize the quantum circuits
            QiskitSerializer.serialize(circuits, circuits_file_path)

            # generate url
            url_root = connexion.request.host_url
            circuits_url = generate_url(url_root,
                                        'circuit-generation/negative-rotation-clustering',
                                        'circuits' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, circuits_url=circuits_url)

    @staticmethod
    def generate_destructive_interference_circuits(job_id, data_angles_url, centroid_angles_url, max_qubits):
        """
        Generates the destructive interference clustering quantum circuits.

        We take the data and centroid angles and return a url to a file with the
        quantum circuits as qasm strings.
        """

        data_angles_file_path = './static/circuit-generation/destructive-interference-clustering/data_angles' \
                                + str(job_id) + '.txt'
        centroid_angles_file_path = './static/circuit-generation/destructive-interference-clustering/centroid_angles' \
                                    + str(job_id) + '.txt'
        circuits_file_path = './static/circuit-generation/destructive-interference-clustering/circuits' \
                             + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        circuits_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/circuit-generation/destructive-interference-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(data_angles_file_path, centroid_angles_file_path, circuits_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_angles_url, data_angles_file_path)
            FileService.download_to_file(centroid_angles_url, centroid_angles_file_path)

            # deserialize the data and centroid angles
            data_angles = NumpySerializer.deserialize(data_angles_file_path)
            centroid_angles = NumpySerializer.deserialize(centroid_angles_file_path)

            # perform circuit generation
            circuits = ClusteringCircuitGenerator.generate_destructive_interference_clustering(max_qubits,
                                                                                               data_angles,
                                                                                               centroid_angles)

            # serialize the quantum circuits
            QiskitSerializer.serialize(circuits, circuits_file_path)

            # generate url
            url_root = connexion.request.host_url
            circuits_url = generate_url(url_root,
                                        'circuit-generation/destructive-interference-clustering',
                                        'circuits' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, circuits_url=circuits_url)

    # @app.route('/api/circuit-generation/state-preparation-clustering/<int:job_id>', methods=['POST'])
    @staticmethod
    def generate_state_preparation_circuits(job_id, data_angles_url, centroid_angles_url, max_qubits):
        """
        Generates the state preparation clustering quantum circuits.

        We take the data and centroid angles and return a url to a file with the
        quantum circuits as qasm strings.
        """

        # load the data from url

        data_angles_file_path = './static/circuit-generation/state-preparation-clustering/data_angles' \
                                + str(job_id) + '.txt'
        centroid_angles_file_path = './static/circuit-generation/state-preparation-clustering/centroid_angles' \
                                    + str(job_id) + '.txt'
        circuits_file_path = './static/circuit-generation/state-preparation-clustering/circuits' \
                             + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        circuits_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/circuit-generation/state-preparation-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(data_angles_file_path, centroid_angles_file_path, circuits_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_angles_url, data_angles_file_path)
            FileService.download_to_file(centroid_angles_url, centroid_angles_file_path)

            # deserialize the data and centroid angles
            data_angles = NumpySerializer.deserialize(data_angles_file_path)
            centroid_angles = NumpySerializer.deserialize(centroid_angles_file_path)

            # perform circuit generation
            circuits = ClusteringCircuitGenerator.generate_state_preparation_clustering(max_qubits,
                                                                                        data_angles,
                                                                                        centroid_angles)

            # serialize the quantum circuits
            QiskitSerializer.serialize(circuits, circuits_file_path)

            # generate url
            url_root = connexion.request.host_url
            circuits_url = generate_url(url_root,
                                        'circuit-generation/state-preparation-clustering',
                                        'circuits' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, circuits_url=circuits_url)

    # @app.route('/api/circuit-execution/negative-rotation-clustering/<int:job_id>', methods=['POST'])
    @staticmethod
    def execute_negative_rotation_circuits(job_id, circuits_url, k, backend_name, token, shots_per_circuit):
        """
        Executes the negative rotation clustering algorithm given the generated
        quantum circuits.
        """

        # load the data from url

        circuits_file_path = './static/circuit-execution/negative-rotation-clustering/circuits' \
                             + str(job_id) + '.txt'
        cluster_mapping_file_path = './static/circuit-execution/negative-rotation-clustering/cluster_mapping' \
                                    + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        cluster_mapping_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/circuit-execution/negative-rotation-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(circuits_file_path)

            # download the circuits and store it locally
            FileService.download_to_file(circuits_url, circuits_file_path)

            # deserialize the circuits
            circuits = QiskitSerializer.deserialize(circuits_file_path)

            # create the quantum backend
            backend = QuantumBackendFactory.create_backend(backend_name, token)

            # execute the circuits
            cluster_mapping = ClusteringCircuitExecutor.execute_negative_rotation_clustering(circuits,
                                                                                             k,
                                                                                             backend,
                                                                                             shots_per_circuit)

            # serialize the data
            NumpySerializer.serialize(cluster_mapping, cluster_mapping_file_path)

            # generate urls
            url_root = connexion.request.host_url
            cluster_mapping_url = generate_url(url_root,
                                               'circuit-execution/negative-rotation-clustering',
                                               'cluster_mapping' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, cluster_mapping_url=cluster_mapping_url)

    @staticmethod
    def execute_destructive_interference_circuits(job_id, circuits_url, k, backend_name, token, shots_per_circuit):
        """
        Executes the destructive interference clustering algorithm given the generated
        quantum circuits.
        """

        # load the data from url

        circuits_file_path = './static/circuit-execution/destructive-interference-clustering/circuits' \
                             + str(job_id) + '.txt'
        cluster_mapping_file_path = './static/circuit-execution/destructive-interference-clustering/cluster_mapping' \
                                    + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        cluster_mapping_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/circuit-execution/destructive-interference-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(circuits_file_path)

            # download the circuits and store it locally
            FileService.download_to_file(circuits_url, circuits_file_path)

            # deserialize the circuits
            circuits = QiskitSerializer.deserialize(circuits_file_path)

            # create the quantum backend
            backend = QuantumBackendFactory.create_backend(backend_name, token)

            # execute the circuits
            cluster_mapping = ClusteringCircuitExecutor \
                .execute_destructive_interference_clustering(circuits,
                                                             k,
                                                             backend,
                                                             shots_per_circuit)

            # serialize the data
            NumpySerializer.serialize(cluster_mapping, cluster_mapping_file_path)

            # generate urls
            url_root = connexion.request.host_url
            cluster_mapping_url = generate_url(url_root,
                                               'circuit-execution/destructive-interference-clustering',
                                               'cluster_mapping' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, cluster_mapping_url=cluster_mapping_url)

    @staticmethod
    def execute_state_preparation_circuits(job_id, circuits_url, k, backend_name, token, shots_per_circuit):
        """
        Executes the state preparation clustering algorithm given the generated
        quantum circuits.
        """

        # load the data from url

        circuits_file_path = './static/circuit-execution/state-preparation-clustering/circuits' \
                             + str(job_id) + '.txt'
        cluster_mapping_file_path = './static/circuit-execution/state-preparation-clustering/cluster_mapping' \
                                    + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        cluster_mapping_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/circuit-execution/state-preparation-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(circuits_file_path)

            # download the circuits and store it locally
            FileService.download_to_file(circuits_url, circuits_file_path)

            # deserialize the circuits
            circuits = QiskitSerializer.deserialize(circuits_file_path)

            # create the quantum backend
            backend = QuantumBackendFactory.create_backend(backend_name, token)

            # execute the circuits
            cluster_mapping = ClusteringCircuitExecutor \
                .execute_state_preparation_clustering(circuits,
                                                      k,
                                                      backend,
                                                      shots_per_circuit)

            # serialize the data
            NumpySerializer.serialize(cluster_mapping, cluster_mapping_file_path)

            # generate urls
            url_root = connexion.request.host_url
            cluster_mapping_url = generate_url(url_root,
                                               'circuit-execution/state-preparation-clustering',
                                               'cluster_mapping' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, cluster_mapping_url=cluster_mapping_url)

    @staticmethod
    def perform_sklearn_clustering(job_id, data_url, centroids_url):
        """
        Executes one iteration of sklearn clustering algorithm.
        """
        data_file_path = './static/classical-clustering/sklearn-clustering/data' \
                         + str(job_id) + '.txt'
        centroids_file_path = './static/classical-clustering/sklearn-clustering/centroids' \
                              + str(job_id) + '.txt'
        cluster_mapping_file_path = './static/classical-clustering/sklearn-clustering/cluster_mapping' \
                                    + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        cluster_mapping_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/classical-clustering/sklearn-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path, centroids_file_path, cluster_mapping_file_path)

            # download the data, centroids and store it locally
            FileService.download_to_file(data_url, data_file_path)
            FileService.download_to_file(centroids_url, centroids_file_path)

            # deserialize the data
            data = NumpySerializer.deserialize(data_file_path)
            centroids = NumpySerializer.deserialize(centroids_file_path)
            k = centroids.shape[0]

            # execute the sklearn clustering
            kmeans_algorithm = KMeans(n_clusters=k, random_state=0, max_iter=1, tol=0.0000001, init=centroids)
            cluster_mapping = kmeans_algorithm.fit(data).labels_.astype(np.int)

            # serialize the data
            NumpySerializer.serialize(cluster_mapping, cluster_mapping_file_path)

            # generate urls
            url_root = connexion.request.host_url
            cluster_mapping_url = generate_url(url_root,
                                               'classical-clustering/sklearn-clustering',
                                               'cluster_mapping' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, cluster_mapping_url=cluster_mapping_url)

    @staticmethod
    def calculate_centroids(job_id, data_url, cluster_mapping_url, old_centroids_url):
        """
        Performs the post processing of a general rotational clustering algorithm,
        i.e. the centroid calculations.

        We take the cluster mapping, data and old centroids and calculate the
        new centroids.
        """

        # load the data from url

        data_file_path = './static/centroid-calculation/rotational-clustering/data' \
                         + str(job_id) + '.txt'
        cluster_mapping_file_path = './static/centroid-calculation/rotational-clustering/cluster_mapping' \
                                    + str(job_id) + '.txt'
        old_centroids_file_path = './static/centroid-calculation/rotational-clustering/old_centroids' \
                                  + str(job_id) + '.txt'
        centroids_file_path = './static/centroid-calculation/rotational-clustering/centroids' \
                              + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        centroids_url = ''

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/centroid-calculation/rotational-clustering/')

            # delete old files if exist
            FileService.delete_if_exist(data_file_path, cluster_mapping_file_path, old_centroids_file_path,
                                        centroids_file_path)

            # download the data and store it locally
            FileService.download_to_file(data_url, data_file_path)
            FileService.download_to_file(cluster_mapping_url, cluster_mapping_file_path)
            FileService.download_to_file(old_centroids_url, old_centroids_file_path)

            # deserialize the data
            data = NumpySerializer.deserialize(data_file_path)
            cluster_mapping = NumpySerializer.deserialize(cluster_mapping_file_path)
            old_centroids = NumpySerializer.deserialize(old_centroids_file_path)

            # map data and centroids to standardized unit sphere
            data = DataProcessingService.normalize(DataProcessingService.standardize(data))
            old_centroids = DataProcessingService.normalize(DataProcessingService.standardize(old_centroids))

            # calculate new centroids
            centroids = DataProcessingService.calculate_centroids(cluster_mapping, old_centroids, data)

            # serialize the data
            NumpySerializer.serialize(centroids, centroids_file_path)

            # generate urls
            url_root = connexion.request.host_url
            centroids_url = generate_url(url_root,
                                         'centroid-calculation/rotational-clustering',
                                         'centroids' + str(job_id))

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, centroids_url=centroids_url)

    @staticmethod
    def check_convergence(job_id, new_centroids_url, old_centroids_url, eps):
        """
        Performs the convergence check for a general KMeans clustering algorithm.

        We take the old and new centroids, calculate their pairwise distance and sum them up
        and divide it by k.

        If the resulting value is less then the given eps, we return convergence, if not,
        we return not converged.
        """

        # load the data from url
        old_centroids_file_path = './static/convergence-check/old_centroids' + str(job_id) + '.txt'
        new_centroids_file_path = './static/convergence-check/new_centroids' + str(job_id) + '.txt'

        # response parameters
        message = 'success'
        status_code = 200
        convergence = False
        distance = 0.0

        try:
            # create working folder if not exist
            FileService.create_folder_if_not_exist('./static/convergence-check/')

            # delete old files if exist
            FileService.delete_if_exist(old_centroids_file_path, new_centroids_file_path)

            # download the data and store it locally
            FileService.download_to_file(old_centroids_url, old_centroids_file_path)
            FileService.download_to_file(new_centroids_url, new_centroids_file_path)

            # deserialize the data
            old_centroids = NumpySerializer.deserialize(old_centroids_file_path)
            new_centroids = NumpySerializer.deserialize(new_centroids_file_path)

            # check convergence
            distance = ConvergenceCalculationService.calculate_averaged_euclidean_distance(old_centroids, new_centroids)

            convergence = distance < eps

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code, convergence=convergence, distance=distance)

    @staticmethod
    def get_negative_rotation_circuits(job_id):
        """
        Get the result for the negative rotation clustering quantum circuit generation.
        """

        if request.method == 'GET':
            # define file paths
            data_file_path = './static/negative_rotation_data' + str(job_id) + '.txt'
            circuits_file_path = './static/negative_rotation_circuits' + str(job_id) + '.txt'

            if not os.path.exists(data_file_path):
                message = 'no job'
                status_code = 404
                circuits_url = ''
            elif not os.path.exists(circuits_file_path):
                message = 'job running'
                status_code = 201
                circuits_url = ''
            else:
                message = 'job finished'
                status_code = 200
                circuits_url = request.url_root[:-4] + 'static/negative_rotation_circuits' + str(job_id) + '.txt'

            return jsonify(message=message, status_code=status_code, circuits_url=circuits_url)
