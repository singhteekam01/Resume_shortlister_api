from typing import List
from pypdf import PdfReader
import docx2txt
import regex as re
import os
import spacy


nlp = spacy.load("en_core_web_sm")

def process_document(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        # Read PDF file
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
    elif file_path.lower().endswith('.docx'):
        # Read DOCX file
        full_text = docx2txt.process(file_path)
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX files are supported.")
    return full_text.lower()


def rabin_karp_search(text: str, keywords: List[str]) -> List[str]:
    def hash_string(s: str, base: int, mod: int) -> int:
        h = 0
        for char in s:
            h = (h * base + ord(char)) % mod
        return h
    
    def rabin_karp_search_single(pattern: str, text: str, base: int = 256, mod: int = 101) -> List[int]:
        pattern_length = len(pattern)
        text_length = len(text)
        pattern_hash = hash_string(pattern, base, mod)
        text_hash = hash_string(text[:pattern_length], base, mod)
        base_pow = pow(base, pattern_length - 1, mod)
        
        matches = []
        
        for i in range(text_length - pattern_length + 1):
            if text_hash == pattern_hash and text[i:i + pattern_length] == pattern:
                matches.append(i)
            if i < text_length - pattern_length:
                text_hash = (base * (text_hash - ord(text[i]) * base_pow) + ord(text[i + pattern_length])) % mod
                if text_hash < 0:
                    text_hash += mod
        
        return matches
    
    all_matches = []
    for keyword in keywords:
        matches = rabin_karp_search_single(keyword, text)
        if matches:
            all_matches.append(keyword)
    
    return all_matches


def calculate_keyword_matching_percentage(keywords: List[str], resume_text: str):
    keywords = [keyword.lower().strip("[]' ") for keyword in keywords]
    resume_text = resume_text.lower()
    
    matching_keywords = rabin_karp_search(resume_text, keywords)
    
    mutual_keywords = set(matching_keywords)
    
    if len(keywords) == 0:
        return 0, mutual_keywords, set()
    matching_percentage = (len(mutual_keywords) / len(keywords)) * 100
    non_matching_keywords = set(keywords).difference(mutual_keywords)

    return matching_percentage, mutual_keywords, non_matching_keywords


def calculate_keyword_matching_percentage_old_algo(keywords: List[str], resume_text: str):
    keywords = [keyword.lower().strip("[]' ") for keyword in keywords]
    resume_tokens = set(token.lower().strip() for token in resume_text.split())
    
    mutual_keywords = set()
    for keyword in keywords:
        if all(word in resume_tokens for word in keyword.split()):
            mutual_keywords.add(keyword)
    
    if len(keywords) == 0:
        return 0, mutual_keywords, set()
    matching_percentage = (len(mutual_keywords) / len(keywords)) * 100
    non_matching_keywords = set(keywords).difference(mutual_keywords)

    return matching_percentage, mutual_keywords, non_matching_keywords


def extract_name_old(text: str) -> List[str]:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
    return names

from spacy.matcher import Matcher

def extract_name(resume_text):
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)

    # Define name patterns
    patterns = [
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name and Last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name, Middle name, and Last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  # First name, Middle name, Middle name, and Last name
        # Add more patterns as needed
    ]

    for pattern in patterns:
        matcher.add('NAME', patterns=[pattern])

    doc = nlp(resume_text)
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text

    return None


def extract_contact_number(text):
    contact_number = None

    # Use regex pattern to find a potential contact number
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"

    #for indian numbers
    # pattern = [
    #     {"ORTH": "+"},
    #     {"ORTH": "91"},
    #     {"SHAPE": "dddddddddd"}
    # ]

    match = re.search(pattern, text)
    if match:
        contact_number = match.group()

    return contact_number


def evaluate_resumes(directory: str, skillset: List[str],top_k :int):
    results = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if filename.lower().endswith(('.pdf', '.docx')):
            resume_text = process_document(str((os.path.join(directory, filename))))
            emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", resume_text)
            name  = extract_name(resume_text)
            number = extract_contact_number(resume_text)
            matching_percentage, mutual_keywords, non_matching_keywords = calculate_keyword_matching_percentage(skillset, resume_text)
            results.append({
                'filename': filename,
                'matching_percentage': matching_percentage,
                'matching_keywords': mutual_keywords,
                'non_matching_keywords': non_matching_keywords,
                'emails': emails,
                'name' : name,
                'file_path': file_path,
                'phone' : number if number is not None else "Phone number not found"
            })
    sorted_results = sorted(results, key=lambda x: x['matching_percentage'], reverse=True)
    return sorted_results[:top_k]
