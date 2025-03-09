import csv
from io import StringIO
import secrets
from app.models.guest import Guest

def process_guest_csv(file_content):
    """Process CSV file and return list of guest objects"""
    try:
        content = file_content.decode('utf-8-sig')
        stream = StringIO(content)
        
        reader = csv.DictReader(stream)
        required_headers = ['name', 'phone', 'has_plus_one', 'is_family', 'language']
        
        if not all(header in reader.fieldnames for header in required_headers):
            missing = [h for h in required_headers if h not in reader.fieldnames]
            raise ValueError(f"Missing required headers: {', '.join(missing)}")
        
        guests = []
        for row in reader:
            if not row['name'] or not row['phone']:
                raise ValueError(f"Name and phone are required. Row data: {row}")
            
            guest = Guest(
                name=row['name'].strip(),
                phone=row['phone'].strip(),
                email=row.get('email', '').strip() or None,  # Make email optional
                token=secrets.token_urlsafe(32),
                has_plus_one=str(row.get('has_plus_one', '')).lower() == 'true',
                is_family=str(row.get('is_family', '')).lower() == 'true',
                language_preference=row.get('language', 'en').strip()
            )
            guests.append(guest)
        
        return guests
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise ValueError(f"Error processing CSV: {str(e)}")

def validate_guest_data(row):
    """Validate guest data from CSV"""
    errors = []
    if not row.get('name'):
        errors.append('Name is required')
    if not row.get('email'):
        errors.append('Email is required')
    return errors