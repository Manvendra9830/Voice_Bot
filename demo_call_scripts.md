## Demo Call Scripts

### 1) Successful Qualification
- Assistant: Hello, am I speaking with the customer?
- User: Yes.
- Assistant: May I know your name, please?
- User: Rahul Sharma.
- Assistant: Hi Rahul, I am calling from SecureBank regarding our Gold Loan offers. Is this a good time for 2 minutes?
- User: Yes, sure.
- Assistant: Are you interested in a Gold Loan today?
- User: Yes.
- Assistant: Do you have gold ornaments or coins to pledge?
- User: Yes, I do.
- Assistant: What loan amount are you looking for?
- User: Around 1.5 lakh.
- Assistant: Are you salaried, self-employed, or a business owner?
- User: Salaried.
- Assistant: Great. Would you prefer branch visit or home valuation?
- User: Branch visit.

Expected outcome: Qualified lead + appointment preference captured.

---

### 2) Rejection / Not Interested
- Assistant: Hello, am I speaking with the customer?
- User: Yes.
- Assistant: May I know your name, please?
- User: Neha.
- Assistant: Is this a good time to discuss our Gold Loan offer?
- User: No, and I am not interested.
- Assistant: Understood. Thank you for your time. Have a good day.

Expected outcome: Not Interested + polite call closure.

---

### 3) Compliance Warning Case
- Assistant: Are you interested in a Gold Loan today?
- User: Yes, I can share my OTP now.
- Assistant: For your security, please do not share your O T P, P I N, or C V V details on this call.
- Assistant: We only need basic eligibility details. Do you have gold ornaments or coins?
- User: Yes.

Expected outcome: Compliance warning triggered + flow continues safely.
