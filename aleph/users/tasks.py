# tasks.py
from celery import shared_task
from helpers.s3 import *
from helpers.checksum import *
from helpers.ocr import *
import time
import fitz  # PyMuPDF
from users.models import *

@shared_task
def process_document(project_id, file_name, temp_file_path, bucket_name, unique_key):
    status = {
        'error': None
    }
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return {'error': 'Project does not exist'}

    s3_service = S3Service(
        region_name=os.getenv('REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    # Extract text and emails from the document
    result, emails = ocr_document(temp_file_path)
    if result['error']:
        return {'error': result['error']}

    # Calculate the checksum of the file
    metadata = get_file_metadata(temp_file_path)

    # Upload to S3 using the unique key name
    if s3_service.upload_to_s3(temp_file_path, bucket_name, unique_key):
        # Save document information
        document_url = s3_service.get_document_url(s3_file=unique_key, s3_bucket=bucket_name)
        doc = Document.objects.create(file_url=document_url,
                                      s3_file_name=unique_key,
                                      project=project,
                                      file_name=file_name)

        # Save document metadata
        DocumentMeta.objects.create(
            document=doc,
            hash_value=unique_key,
            name=file_name,
            size_bytes=metadata['Size (bytes)'],
            file_type=metadata['Type'],
            is_directory=metadata['Is Directory'],
            last_modified_time=metadata['Last Modified Time'],
            last_accessed_time=metadata['Last Accessed Time']
        )

        # Save OCR text and emails
        OCRText.objects.create(
            document=doc,
            text=result['text'],
            emails=emails
        )
        try:
            pdf_document = fitz.open(temp_file_path)
            for page_number in range(len(pdf_document)):
                page = pdf_document.load_page(page_number)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image_bytes = pixmap.tobytes()
                s3_image_key = f"{unique_key}_page_{page_number + 1}.jpg"
                if s3_service.upload_image_to_s3(image_bytes, bucket_name, s3_image_key):
                    image_url = s3_service.get_document_url(s3_file=s3_image_key, s3_bucket=bucket_name)
                    PageImage.objects.create(document=doc, page_number=page_number + 1, image_url=image_url)
                pixmap = None  # Clean up the pixmap object
            pdf_document.close()
        except Exception as e:
            status['error'] = str(e)
            print(f"Error processing PDF pages: {e}")

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return {'document_id': doc.id, 'status':status}
    else:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return {'error': f'Failed to upload {file_name} to S3'}
