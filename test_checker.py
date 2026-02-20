import requests
import glob
import sys

WEBSERVICE_URL = "https://fhn7thfefc.execute-api.us-east-1.amazonaws.com"

for file in glob.glob("./dane/Z02/train/*.pdf"):
    print(f"Testowanie pliku {file}")

    with open(file, "rb") as f:
        files = {"file": f}
        response = requests.post(WEBSERVICE_URL + "/invoice", files=files)

    print("STATUS:", response.status_code)

    try:
        data = response.json()

        if {"vat_id", "address", "total"}.issubset(data) \
           and data["vat_id"] \
           and data["address"] \
           and isinstance(data["total"], (int, float)):

            print(f'OK: {data["vat_id"]}\t{data["total"]}\t{data["address"]}')
        else:
            print("NIEPOPRAWNA ODPOWIEDŹ:", data)

    except Exception as exc:
        print("BŁĘDNA ODPOWIEDŹ (nie JSON)")
        print("RAW:", response.text)

    print("-" * 60)