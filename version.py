class Version(restful.Resource):
    def __init__(self):
        self.__parser = reqparse.RequestParser()

    def get(self):
        version = {
            'service': 'HotNet2 Service',
            'version': '0.1.0'
        }
        return version, 200
