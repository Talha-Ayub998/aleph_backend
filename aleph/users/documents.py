from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl import Document as ElasticsearchDocument
from django_elasticsearch_dsl.registries import registry
from users.models import *

@registry.register_document
class UserDocument(ElasticsearchDocument):
    class Index:
        name = 'users'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'group',
            'status',
        ]

@registry.register_document
class ProjectDocument(ElasticsearchDocument):
    class Index:
        name = 'projects'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Project
        fields = [
            'name',
            'description',
        ]

@registry.register_document
class DocumentDocument(ElasticsearchDocument):
    class Index:
        name = 'documents'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Document
        fields = [
            'file_name',
            'file_url',
            'uploaded_at',
        ]

    project = fields.ObjectField(properties={
        'name': fields.TextField(),
        'description': fields.TextField(),
    })

    def prepare_project(self, instance):
        return {
            'name': instance.project.name,
            'description': instance.project.description,
        }


@registry.register_document
class OCRTextDocument(ElasticsearchDocument):
    class Index:
        name = 'ocrtexts'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = OCRText
        fields = [
            'text',
            #'emails',
        ]

    document = fields.ObjectField(properties={
        'file_name': fields.TextField(),
        'file_url': fields.TextField(),
    })

    def prepare_document(self, instance):
        document_instance = instance.document
        return {
            'file_name': document_instance.file_name,
            'file_url': document_instance.file_url,
        }

    def __str__(self):
        return f"OCR Text for {self.document}"