from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from fpdf import FPDF
from docx import Document
from io import BytesIO
import os
import docx2txt
from PyPDF2 import PdfReader
import re
import nltk
import heapq

# Define the path where NLTK data is stored
nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
nltk.data.path.append(nltk_data_path)

# Ensure NLTK data is available at the start
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', download_dir=nltk_data_path)
    nltk.download('stopwords', download_dir=nltk_data_path)
#rebders the main page
def main(request):
    return render(request, 'base.html')

def upload_document(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES['document']

            # Save the uploaded file to a temporary location
            temporary_file_path = 'media/temporary_file'
            with open(temporary_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Determine file format and extract text accordingly
            if uploaded_file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                # DOCX file
                text = docx2txt.process(temporary_file_path)
            elif uploaded_file.content_type == 'application/pdf':
                # PDF file using PyPDF2
                reader = PdfReader(temporary_file_path)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
            elif uploaded_file.content_type == 'text/plain':
                # TXT file
                with open(temporary_file_path, 'r') as f:
                    text = f.read()
            else:
                messages.error(request, 'Unsupported file format!')
                return render(request, 'showText.html')

            # Remove the temporary file
            os.remove(temporary_file_path)

            messages.success(request, 'Text extracted successfully!')
            return render(request, 'showText.html', {'extracted_text': text})

    except Exception as e:
        # Handle exceptions (e.g., file not found, extraction error)
        messages.error(request, f'Error: {str(e)}')
    return render(request, 'showText.html')

def summarization(request):
    if request.method == 'POST':
        # Get the article text from the form data
        article_text = request.POST.get('extracted_text', '')

        if not article_text:
            messages.error(request, 'No text provided for summarization!')
            return render(request, 'showText.html')

        # Preprocessing steps
        try:
            # Removing Square Brackets and Extra Spaces
            article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
            article_text = re.sub(r'\s+', ' ', article_text)
            # Removing special characters and digits
            formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text)
            formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)

            sentence_list = nltk.sent_tokenize(article_text)
            stopwords = nltk.corpus.stopwords.words('english')

            word_frequencies = {}
            for word in nltk.word_tokenize(formatted_article_text):
                if word not in stopwords:
                    if word not in word_frequencies:
                        word_frequencies[word] = 1
                    else:
                        word_frequencies[word] += 1

            maximum_frequency = max(word_frequencies.values())
            for word in word_frequencies.keys():
                word_frequencies[word] = word_frequencies[word] / maximum_frequency

            sentence_scores = {}
            for sent in sentence_list:
                for word in nltk.word_tokenize(sent.lower()):
                    if word in word_frequencies:
                        if len(sent.split(' ')) < 30:
                            if sent not in sentence_scores:
                                sentence_scores[sent] = word_frequencies[word]
                            else:
                                sentence_scores[sent] += word_frequencies[word]

            summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)
            summary = ' '.join(summary_sentences)

            messages.success(request, 'Summary generated successfully!')
            return render(request, 'showSumText.html', {'sum_text': summary})

        except Exception as e:
            messages.error(request, f'Error during summarization: {str(e)}')
            return render(request, 'showText.html')

def export_summary(request, format):
    if request.method == 'POST':
        summary_text = request.POST.get('sum_text', '')

        if not summary_text:
            messages.error(request, 'No summary text available for export!')
            return render(request, 'showSumText.html')

        if format == 'pdf':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="summary.pdf"'

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            # Encode summary_text as utf-8
            pdf.multi_cell(0, 10, summary_text.encode('utf-8').decode('latin-1'))
            response.write(pdf.output(dest='S').encode('latin1'))
            return response

        elif format == 'docx':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = 'attachment; filename="summary.docx"'

            doc = Document()
            doc.add_paragraph(summary_text)
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            response.write(buffer.read())
            return response

    messages.error(request, 'Invalid request method!')
    return render(request, 'showSumText.html')
