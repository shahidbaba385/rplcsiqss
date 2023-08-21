import os
import docx2txt
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT
from whoosh.analysis import RegexTokenizer
import nltk

nltk.download('punkt')

# Define schema for indexing
schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))

# Create index directory if not exists
if not os.path.exists("index"):
    os.mkdir("index")

# Create an index
ix = create_in("index", schema)

# Open the index
writer = ix.writer()

# Define a RegexTokenizer for basic tokenization
tokenizer = RegexTokenizer()

# Index your Word documents
word_documents = [
    "data/Actions to be taken if the process is not followed.docx",
    "data/Basecamp.docx",
    "data/Candidate and Client Communication.docx",
    "data/Candidate Notes.docx",
    "data/Consequences of not following the process.docx",
    "data/Job postings.docx",
    "data/monthly report.docx",
    "data/Process Adherence Full Document.docx",
    "data/PROCESS ADHERENCE IN PSD.docx",
    "data/resume parsing.docx",
    "data/weekly notes.docx",
   
    # Add other document paths here
]

for doc_path in word_documents:
    content = docx2txt.process(doc_path)
    tokenized_content = " ".join([token.text for token in tokenizer(content)])
    writer.add_document(title=os.path.basename(doc_path), content=tokenized_content)

# Index text files
text_files = [
    "data/Text/Importance of Process Adherence.txt",
    # Add other text file paths here
]

for txt_path in text_files:
    with open(txt_path, 'r', encoding='utf-8') as txt_file:
        content = txt_file.read()
        tokenized_content = " ".join([token.text for token in tokenizer(content)])
        writer.add_document(title=os.path.basename(txt_path), content=tokenized_content)

# Commit changes and close the index
writer.commit()
