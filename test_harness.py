import json
from pathlib import Path

from main import normalize_bool, normalize_loan_amount


def run_tests():
    test_file = Path("test_cases.json")
    if not test_file.exists():
        print("test_cases.json not found")
        return 1

    data = json.loads(test_file.read_text(encoding="utf-8"))
    cases = data.get("test_cases", [])
    passed = 0
    results = []

    for case in cases:
        case_id = case.get("id", "UNKNOWN")
        expected = case.get("expected", {})
        ok = True
        notes = []

        # Basic checks on extraction normalization behavior.
        if "loan_amount" in expected:
            actual_amount = normalize_loan_amount(case.get("user_inputs", [""])[0])
            if int(actual_amount) != int(expected["loan_amount"]):
                ok = False
                notes.append(f"loan_amount expected {expected['loan_amount']}, got {actual_amount}")

        if "is_interested" in expected:
            input_text = " ".join(case.get("user_inputs", []))
            actual_interest = normalize_bool(input_text)
            if bool(actual_interest) != bool(expected["is_interested"]):
                ok = False
                notes.append(f"is_interested expected {expected['is_interested']}, got {actual_interest}")

        if ok:
            passed += 1
            results.append({"id": case_id, "status": "PASS", "notes": ""})
        else:
            results.append({"id": case_id, "status": "FAIL", "notes": "; ".join(notes)})

    print("=== Test Harness Result ===")
    for item in results:
        print(f"{item['id']}: {item['status']} {item['notes']}".strip())

    print(f"\nPass Rate: {passed}/{len(cases)}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(run_tests())
