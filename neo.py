import re
import pdfplumber
import spacy
import json
from collections import defaultdict
from neo4j import GraphDatabase

uri = "neo4j+s://c2ef0299.databases.neo4j.io"
user = "neo4j"
password = "1sAspC1Cs8BgZpcO4wv1i2JWsiJ04HR1UW-5F-hgqKg"

driver = GraphDatabase.driver(uri, auth=(user, password))

nlp = spacy.load("en_core_web_sm")

def add_document_text_to_graph(driver, text: str):
    with driver.session() as session:
        session.run("CREATE (doc:Document) SET doc.text = $text", text=text)

def add_borrower_to_graph(driver, text: str):
    borrower_pattern = re.compile(r"among\s*([\w\s,]+),\s*as\s+the\s+Borrower", re.IGNORECASE)
    borrower_match = borrower_pattern.search(text)

    if borrower_match:
        borrower = borrower_match.group(1).strip()
        print(f"Adding borrower: {borrower}")

        with driver.session() as session:
            session.run("MERGE (b:Borrower {name: $borrower}) MERGE (doc:Document) MERGE (doc)-[:HAS_BORROWER]->(b)", borrower=borrower)
    else:
        print("No borrower found in the text.")

def lambda_handler(event, context):
    text = event['text']
    answers = pdf_processor.process_pdf(text)

    response = {
        "statusCode": 200,
        "body": json.dumps(answers)
    }
    return response
    
def add_credit_agreement_date_to_graph(driver, text: str):
    date_pattern = re.compile(r"\b(?:dated as of|dated)\b.*?(?P<date>\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b)", re.IGNORECASE)
    match = date_pattern.search(text)
    date = None
    if match:
        date = match.group("date")
        print(f"Adding date: {date}")  # Add this print statement
    
    if date:
        with driver.session() as session:
            session.run("MERGE (d:Date {value: $date}) MERGE (doc:Document) MERGE (doc)-[:HAS_DATE]->(d)", date=date)

def add_rate_type_to_graph(driver, text: str):
    rate_type_pattern = re.compile(r"\b(?:LIBOR|SOFR|Eurocurrency Rate)\b", re.IGNORECASE)
    rate_type_matches = rate_type_pattern.findall(text)
    rate_type_occurrences = defaultdict(int)

    for rate_type in rate_type_matches:
        if rate_type.lower() == "eurocurrency rate":
            rate_type = "LIBOR"
        rate_type_occurrences[rate_type.upper()] += 1

    with driver.session() as session:
        for rate_type, count in rate_type_occurrences.items():
            if count > 0:
                print(f"Adding rate type: {rate_type}")
                session.run("MERGE (rt:RateType {name: $rate_type}) ON CREATE SET rt.name = $rate_type", rate_type=rate_type)
                session.run("MATCH (doc:Document), (rt:RateType {name: $rate_type}) MERGE (doc)-[:HAS_RATE_TYPE]->(rt)", rate_type=rate_type)

def add_currency_to_graph(driver, text: str):
    currencies = ["USD", "EUR", "JPY", "GBP", "AUD"]
    currency_occurrences = defaultdict(int)

    for currency in currencies:
        currency_occurrences[currency] = len(re.findall(currency, text, re.IGNORECASE))

    with driver.session() as session:
        for currency, count in currency_occurrences.items():
            if count > 0:
                print(f"Adding currency: {currency}")
                session.run("MERGE (c:Currency {name: $currency}) ON CREATE SET c.name = $currency", currency=currency)
                session.run("MATCH (doc:Document), (c:Currency {name: $currency}) MERGE (doc)-[:HAS_CURRENCY]->(c)", currency=currency)

def add_facility_type_to_graph(driver, text: str):
    facility_types = ["initial term loan", "Term Loan B", "Term Loan A", "Term Loan C"]
    facility_type_occurrences = defaultdict(int)

    for facility_type in facility_types:
        facility_type_occurrences[facility_type] = len(re.findall(facility_type, text, re.IGNORECASE))

    with driver.session() as session:
        for facility_type, count in facility_type_occurrences.items():
            if count > 0:
                print(f"Adding facility type: {facility_type}")  # Add this print statement
                session.run("MERGE (ft:FacilityType {value: $facility_type}) MERGE (doc:Document) MERGE (doc)-[:HAS_FACILITY_TYPE {count: $count}]->(ft)", facility_type=facility_type, count=count)

def add_aggregate_principal_amount_to_graph(driver, text: str):
    amount_pattern = re.compile(r"\b(?:aggregate principal amount of )(\$[\d,]+(\.\d{2})?)\b", re.IGNORECASE)
    amount_match = amount_pattern.search(text)

    if amount_match:
        amount = amount_match.group(1)
        with driver.session() as session:
            print(f"Adding amount: {amount}")  # Add this print statement
            session.run("MERGE (a:Amount {value: $amount}) MERGE (doc:Document) MERGE (doc)-[:HAS_AMOUNT]->(a)", amount=amount)

def add_applicable_rate_to_graph(driver, text: str):
    rate_pattern = re.compile(r"Applicable Rate\D+percentage per annum equal to\D+(\d+\.\d{1,2}%|\d{1,2}\.\d{1,2}%)")
    rate_matches = rate_pattern.findall(text)
    rate_occurrences = defaultdict(int)

    for rate in rate_matches:
        rate_occurrences[rate] += 1

    with driver.session() as session:
        for rate, count in rate_occurrences.items():
            if count == max(rate_occurrences.values()):
                print(f"Adding applicable rate: {rate}")
                session.run("MERGE (r:ApplicableRate {value: $rate}) MERGE (doc:Document) MERGE (doc)-[:HAS_RATE {count: $count}]->(r)", rate=rate, count=count)

def answer_question_using_neo4j(driver, question):
    with driver.session() as session:
        question_lower = question.lower()

        if "type of rate loan" in question_lower or "is it LIBOR, SOFR" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_RATE_TYPE]->(rt:RateType) RETURN rt.value as value LIMIT 1")
            single_result = result.single()
            print(f"Query result for question '{question}': {single_result['value']}")
            return single_result['value']

        elif "type of currency" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_CURRENCY]->(c:Currency) RETURN c.value as value LIMIT 1")
            single_result = result.single()
            print(f"Query result for question '{question}': {single_result['value']}")
            return single_result['value']

        elif "kind of term loan" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_FACILITY_TYPE]->(ft:FacilityType) RETURN ft.name as name, count(ft) as cnt ORDER BY cnt DESC LIMIT 1")

        elif "aggregate principal amount" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_AMOUNT]->(amt:Amount) RETURN amt.value as value, count(amt) as cnt ORDER BY cnt DESC LIMIT 1")

        elif "applicable rate" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_APPLICABLE_RATE]->(ar:ApplicableRate) RETURN ar.value as value, count(ar) as cnt ORDER BY cnt DESC LIMIT 1")

        elif "borrower" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_BORROWER]->(b:Borrower) RETURN b.name as name, count(b) as cnt ORDER BY cnt DESC LIMIT 1")

        elif "credit agreement is dated" in question_lower:
            result = session.run("MATCH (doc:Document)-[:HAS_DATE]->(d:Date) RETURN d.value as value, count(d) as cnt ORDER BY cnt DESC LIMIT 1")

        else:
            print(f"Cannot answer the question '{question}'")
            return None

        single_result = result.single()

        if single_result is not None:
            if "name" in single_result.keys():
                print(f"Query result for question '{question}': {single_result['name']}")
                return single_result['name']
            elif "value" in single_result.keys():
                print(f"Query result for question '{question}': {single_result['value']}")
                return single_result['value']
        else:
            print(f"Query result for question '{question}': No results found.")
            return None
        
if __name__ == "__main__":
    # Read the PDF file and store its text in a variable
    pdf_path = "/Users/eddiegarcia/Desktop/Viasat.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        pdf_text = "\n".join([page.extract_text() for page in pdf.pages])

    # Run the text processing functions on the PDF text
    text = pdf_text
    add_borrower_to_graph(driver, pdf_text)
    add_credit_agreement_date_to_graph(driver, pdf_text)
    add_rate_type_to_graph(driver, pdf_text)
    add_currency_to_graph(driver, pdf_text)
    add_facility_type_to_graph(driver, pdf_text)
    add_aggregate_principal_amount_to_graph(driver, pdf_text)
    add_applicable_rate_to_graph(driver, pdf_text)

    # List of questions
    questions = [
        "What is the type of rate loan that the applicable rate is in (i.e., is it LIBOR, SOFR, or anything else)?",
        "What is the type of currency used?",
        "What is the kind of term loan that the credit agreement is?",
        "What is the aggregate principal amount?",
        "What is the applicable rate?",
        "Who is listed as the 'borrower'?",
        "Credit agreement is dated as of when?",
    ]

    # Answer the questions using the graph
    answers = []
    for question in questions:
        answer = answer_question_using_neo4j(driver, question)
        answers.append(answer)

    print(answers)
    driver.close()