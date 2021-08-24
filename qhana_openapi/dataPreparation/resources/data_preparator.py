import os
from threading import Thread

from flask import request, jsonify

from calculation.aggregator import AggregatorType
from calculation.entityComparer import EntityComparer
from calculation.transformer import TransformerType
from entityLoadingService import EntityLoadingService
from fileService import FileService
from numpySerializer import NumpySerializer


def run_wu_palmer_data_preparation(entities,
                                   output_file_path,
                                   attributes,
                                   aggregator_type=AggregatorType.mean,
                                   transformer_type=TransformerType.squareInverse):
    try:
        # create comparer based on all attributes we want to use
        # for calculation and the given aggregator and transformer.
        comparer = EntityComparer(aggregator_type, transformer_type)
        for attribute in attributes:
            comparer.add_attribute_comparer(attribute)

        # perform comparison
        result = comparer.calculate_pairwise_distance(entities)

        # serialize result
        # serialize the output data
        NumpySerializer.serialize(result, output_file_path)

    except Exception as ex:
        file = open(output_file_path, 'w')
        file.write(str(ex))
        file.close()


class DataPreparator:

    @staticmethod
    def perform_wu_palmer_data_preparation(job_id, input_data_url, attributes=None, aggregator_type=AggregatorType.mean,
                                           transformer_type=TransformerType.squareInverse):
        """
        Trigger the wu palmer data preparation algorithm.
        We have the following parameters (name : type : default : description):
        input_data_url : string : : download location of the input data
        job_id : int : : the id of the job
        attributes : [string] : : the attributes to prepare

        Note, that we take AttributeComparer = SymMaxMean
        and ElementComparer = WuPalmer for every attribute.
        """

        # load the data from url
        if attributes is None:
            attributes = []
        input_file_path = './static/input' + str(job_id)
        output_file_path = './static/output' + str(job_id)

        # response parameters
        message = "success"
        status_code = 200

        try:
            # delete old files if exist
            if os.path.exists(input_file_path):
                os.remove(input_file_path)
            if os.path.exists(output_file_path):
                os.remove(output_file_path)

            # download the input data and store it locally
            FileService.download_to_file(input_data_url, input_file_path)

            # deserialize the input data
            data_loading_service = EntityLoadingService()
            entities = data_loading_service.load_entities(input_file_path)

            # perform the real data preparation, i.e. start
            # a fire and forget the data preparation task
            thread = Thread(target=run_wu_palmer_data_preparation,
                            kwargs={
                                'entities': entities,
                                'output_file_path': output_file_path,
                                'attributes': attributes,
                                'aggregator_type': aggregator_type,
                                'transformer_Type': transformer_type
                            })
            thread.start()

        except Exception as ex:
            message = str(ex)
            status_code = 500

        return jsonify(message=message, status_code=status_code)

    @staticmethod
    def get_output(job_id):
        if request.method == 'GET':
            # define file paths
            input_file_path = './static/input' + str(job_id)
            output_file_path = './static/output' + str(job_id)

            if not os.path.exists(input_file_path):
                message = 'no job'
                status_code = 404
                output_data_url = ''
            elif not os.path.exists(output_file_path):
                message = 'job running'
                status_code = 201
                output_data_url = ''
            else:
                message = 'job finished'
                status_code = 200
                output_data_url = request.url_root[:-4] + 'static/output' + str(job_id)

            return jsonify(message=message, status_code=status_code, output_data_url=output_data_url)
