import re
import pdfplumber
import networkx as nx
import spacy
import sys
from collections import defaultdict
from typing import List

nlp = spacy.load("en_core_web_sm")

def add_borrower_to_graph(G, text: str):
    doc = nlp(text)
    borrower = None
    for ent in doc.ents:
        if ent.label_ == "ORG":
            borrower = ent.text
            break

    if borrower:
        G.add_node(borrower, type="borrower")
        G.add_edge("document", borrower)

def add_credit_agreement_date_to_graph(G, text: str):
    doc = nlp(text)
    date = None
    for ent in doc.ents:
        if ent.label_ == "DATE":
            date = ent.text
            break

    if date:
        G.add_node(date, type="date")
        G.add_edge("document", date)

def add_rate_type_to_graph(G, text: str):
    rate_types = ["LIBOR", "SOFR", "EURIBOR", "TIBOR", "SHIBOR"]
    rate_type_occurrences = defaultdict(int)

    for rate_type in rate_types:
        rate_type_occurrences[rate_type] = len(re.findall(rate_type, text, re.IGNORECASE))

    for rate_type, count in rate_type_occurrences.items():
        if count > 0:
            G.add_node(rate_type, type="rate_type")
            G.add_edge("document", rate_type, weight=count)

def add_currency_to_graph(G, text: str):
    currencies = ["USD", "EUR", "JPY", "GBP", "AUD"]
    currency_occurrences = defaultdict(int)

    for currency in currencies:
        currency_occurrences[currency] = len(re.findall(currency, text, re.IGNORECASE))

    for currency, count in currency_occurrences.items():
        if count > 0:
            G.add_node(currency, type="currency")
            G.add_edge("document", currency, weight=count)

def add_facility_type_to_graph(G, text: str):
    facility_types = ["initial term loan", "Term Loan B", "Term Loan A", "Term Loan C"]
    facility_type_occurrences = defaultdict(int)

    for facility_type in facility_types:
        facility_type_occurrences[facility_type] = len(re.findall(facility_type, text, re.IGNORECASE))

    for facility_type, count in facility_type_occurrences.items():
        if count > 0:
            G.add_node(facility_type, type="facility_type")
            G.add_edge("document", facility_type, weight=count)

def add_aggregate_principal_amount_to_graph(G, text: str):
    amounts = re.findall(r"(\$[\d,]+(\.\d{2})?)", text)
    amount_occurrences = defaultdict(int)

    for amount, _ in amounts:
        amount_occurrences[amount] += 1

    for amount, count in amount_occurrences.items():
        if count > 0:
            G.add_node(amount, type="amount")
            G.add_edge("document", amount, weight=count)

def add_applicable_rate_to_graph(G, text: str, rate_type: str):
    rate_occurrences = defaultdict(int)
    rate_regex = r"(\d+(\.\d{1,2})?%?)"

    for match in re.finditer(rate_regex, text):
        rate_occurrences[match.group()] += 1

    for rate, count in rate_occurrences.items():
        if count > 0:
            G.add_node(rate, type="applicable_rate")
            G.add_edge("document", rate, weight=count)

def answer_question_using_graph(G, question: str):
    question_lower = question.lower()

    if "type of rate loan" in question_lower or "is it LIBOR, SOFR" in question_lower:
        rate_types = ["LIBOR", "SOFR", "EURIBOR", "TIBOR", "SHIBOR"]
        best_rate_type = max(rate_types, key=lambda x: G.number_of_edges("document", x) if G.has_edge("document", x) else 0)
        return best_rate_type

    if "type of currency used" in question_lower:
        currencies = ["USD", "EUR", "JPY", "GBP", "AUD"]
        best_currency = max(currencies, key=lambda x: G.number_of_edges("document", x) if G.has_edge("document", x) else 0)
        return best_currency

    if "kind of term loan" in question_lower:
        facility_types = ["initial term loan", "Term Loan B", "Term Loan A", "Term Loan C"]
        best_facility_type = max(facility_types, key=lambda x: G.number_of_edges("document", x) if G.has_edge("document", x) else 0)
        return best_facility_type

    if "aggregate principal amount" in question_lower:
        amounts = [node for node, data in G.nodes(data=True) if data.get("type") == "amount"]
        if amounts:
            best_amount = max(amounts, key=lambda x: G.number_of_edges("document", x))
            return best_amount
        else:
            return "The aggregate principal amount could not be identified."

    if "applicable rate" in question_lower:
        rates = [node for node, data in G.nodes(data=True) if data.get("type") == "applicable_rate"]
        if rates:
            best_rate = max(rates, key=lambda x: G.number_of_edges("document", x))
            return best_rate
        else:
            return "The applicable rate could not be identified."

    if "who is listed as the 'borrower'" in question_lower:
        borrowers = [node for node, data in G.nodes(data=True) if data.get("type") == "borrower"]
        if borrowers:
            return borrowers[0]
        else:
            return "The borrower could not be identified."

    if "credit agreement is dated as of when" in question_lower:
        dates = [node for node, data in G.nodes(data=True) if data.get("type") == "date"]
        if dates:
            return dates[0]
        else:
            return "The credit agreement date could not be identified."

    return "Question not recognized."

def process_pdf(file_content: str):
    G = nx.DiGraph()
    G.add_node("document", type="document")
    text = file_content
    add_borrower_to_graph(G, text)
    add_credit_agreement_date_to_graph(G, text)
    add_rate_type_to_graph(G, text)
    add_currency_to_graph(G, text)
    add_facility_type_to_graph(G, text)
    add_aggregate_principal_amount_to_graph(G, text)
    rate_type = "your rate type here"
    add_applicable_rate_to_graph(G, text, rate_type)

    questions = [
        "What is the type of rate loan that the applicable rate is in (i.e., is it LIBOR, SOFR, or anything else)?",
        "What is the type of currency used?",
        "What is the kind of term loan that the credit agreement is?",
        "What is the aggregate principal amount?",
        "What is the applicable rate?",
        "Who is listed as the 'borrower'?",
        "Credit agreement is dated as of when?",
    ]

    answers = []
    for question in questions:
        answer = answer_question_using_graph(G, question)
        answers.append(answer)

    return answers

# # Create the graph
# G = nx.DiGraph()
# G.add_node("document", type="document")
# text = sys.argv[1]
# add_borrower_to_graph(G, text)
# add_credit_agreement_date_to_graph(G, text)
# add_rate_type_to_graph(G, text)
# add_currency_to_graph(G, text)
# add_facility_type_to_graph(G, text)
# add_aggregate_principal_amount_to_graph(G, text)
# rate_type = "your rate type here"
# add_applicable_rate_to_graph(G, text, rate_type)

# List of questions
# questions = [
#     "What is the type of rate loan that the applicable rate is in (i.e., is it LIBOR, SOFR, or anything else)?",
#     "What is the type of currency used?",
#     "What is the kind of term loan that the credit agreement is?",
#     "What is the aggregate principal amount?",
#     "What is the applicable rate?",
#     "Who is listed as the 'borrower'?",
#     "Credit agreement is dated as of when?",
# ]

# Answer the questions using the graph
# answers = []
# for question in questions:
#     answer = answer_question_using_graph(G, question)
#     answers.append(answer)

# print(answers)