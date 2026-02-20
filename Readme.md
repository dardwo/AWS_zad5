# Zadanie 5.2 — Invoice OCR (SaaS AI)

## Opis zadania

Projekt przedstawia wykorzystanie usług SaaS z zakresu sztucznej inteligencji i przetwarzania dokumentów w chmurze AWS.

Celem systemu jest automatyczne odczytywanie danych z zeskanowanych polskich faktur VAT i zwracanie:

- numeru NIP sprzedawcy (`vat_id`)
- adresu sprzedawcy (`address`)
- łącznej kwoty brutto (`total`)

System działa jako webserwis z jednym endpointem HTTP:

Rozwiązanie zostało zrealizowane w modelu serverless z wykorzystaniem usług AWS:

Klient (curl\skrypt testujący) -> API Gateway -> AWS Lambda -> Amazon Textract -> Parsowanie danych -> JSON


### Wykorzystane usługi SaaS:

- **Amazon Textract (AnalyzeExpense)** – usługa AI do analizy dokumentów i faktur
- **AWS Lambda** – bezserwerowe przetwarzanie logiki aplikacji
- **API Gateway HTTP API** – udostępnienie endpointu HTTP

Textract odpowiada za analizę dokumentu i ekstrakcję pól, a logika Lambda przetwarza odpowiedź i zwraca ustandaryzowany JSON.

---

## Endpoint

Po wdrożeniu aplikacji otrzymujemy adres w postaci:

https://<api-id>.execute-api.us-east-1.amazonaws.com/invoice

### Przykładowe wywołanie:

```bash
curl -X POST https://<endpoint>/invoice \
  -F "file=@dane/Z02/train/AFV 1_05_2021.pdf"
```

### Przykładowe odpowiedzi:

------------------------------------------------------------
Testowanie pliku ./dane/Z02/train/AFV 4_05_2021.pdf
STATUS: 200
OK: 7831702323  246.0   05-122 Wilanów
------------------------------------------------------------
Testowanie pliku ./dane/Z02/train/CFV 3_05_2021.pdf
STATUS: 200
OK: 7831702323  639.59  05-122 Wilanów
------------------------------------------------------------
Testowanie pliku ./dane/Z02/train/AFV 1_05_2021.pdf
STATUS: 200
OK: 7831702323  109.46  05-122 Wilanów
------------------------------------------------------------
Testowanie pliku ./dane/Z02/train/BFV 3_05_2021.pdf
STATUS: 200
OK: 7831702323  639.59  ul. Towarowa 35/37, 61-896 Poznan
------------------------------------------------------------

### KOnfiguracja
1. Uzupełnić dane dostępowe w pliku .env
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
AWS_DEFAULT_REGION=us-east-1

2. python deploy.py
3. python test_checker.py
4. Usuwanie zasobów - python cleanup.py