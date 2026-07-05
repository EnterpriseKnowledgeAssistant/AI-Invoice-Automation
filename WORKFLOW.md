# AI Invoice Automation Workflow

1. User uploads an invoice PDF.
2. The PDF is saved to the uploads folder.
3. PyPDF2 extracts text from the PDF.
4. Extracted text is sent to Google Gemini.
5. Gemini returns structured invoice JSON.
6. User reviews extracted fields.
7. Department is assigned based on the cost center.
8. Approval is determined using the invoice amount.
9. Invoice is stored in SQLite.
10. User can approve or reject the invoice.
11. Dashboard displays invoice statistics.