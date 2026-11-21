# Loan Sales & Call Centre CRM

A CRM for a loan-intermediary call centre. The Admin uploads and distributes leads. Staff call them, log outcomes, schedule follow-ups and create loan applications. The Admin tracks each application through approval, disbursement and closure.

## Tech Stack
Python, Django, SQLite, HTML and CSS (Django templates).

## Run locally
```bash
git clone https://github.com/namithajeejan-cmd/loan-salescall-crm.git
cd loan-salescall-crm
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
```
In the shell, set the superuser's role to ADMIN, then create a staff user:
```python
from crm.models import User
User.objects.filter(username='admin').update(role='ADMIN')
User.objects.create_user(username='staff1', password='Staff@123', role='STAFF')
exit()
```
Then run:
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/

Sample leads for testing: `sample_data/leads.csv` (columns: name, phone, loan_type).

## URLs
- Live: not deployed (run locally using the steps above)
- Mobile UI: `/m/` (the Admin Portal in a phone-sized frame)

## Test credentials
- Admin: `admin` / `crmloansales`
- Staff: `staff1` / `Staff@123`

## Features built
- Separate Admin and Staff login with role-based access (role checked on every page)
- Bulk CSV lead upload with phone validation and duplicate detection
- Equal (round-robin) lead distribution among active staff
- Employee management: add staff, set daily target, activate/deactivate
- Staff portal: own leads only, call logging, daily X/100 counter, interested / not interested, follow-up scheduling
- Loan applications: staff create them, admin updates status (Submitted, Under Review, Approved, Disbursed, Closed, Rejected)
- Admin dashboard with counts and staff performance
- Mobile layout for all pages, with a `/m/` phone view

## Not completed (next steps)
- Document upload and verification
- Bank and loan scheme management (the bank is currently typed text)
- Reports and analytics, CSV export
- Admin pages for all leads and all follow-ups
- Editing a staff member's daily target after creation
- Staff personal performance page

## Notes 
- The daily counter counts every call logged today, including repeat calls to the same lead.
- Follow-ups can be set for any lead that is not marked Not Interested.
- Test accounts use simple passwords for demo purposes only.
- I used AI as a coding assistant and learning aid by understanding with my knowledge.