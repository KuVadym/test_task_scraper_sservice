from database import db_session
from database.form_models import Form
from datetime import datetime

def add_form_data_to_db(json_data):
    result = {
        "processed": 0,
        "success": 0,    
        "errors": []     
    }
    
    current_date = datetime.now()
    
    for key, value in json_data.items():
        result["processed"] += 1
        
        try:
            first_activity = None
            if value.get('first_activity'):
                first_activity = datetime.strptime(value.get('first_activity'), '%Y-%m-%d %H:%M:%S')
                
            last_activity = None
            if value.get('last_activity'):
                last_activity = datetime.strptime(value.get('last_activity'), '%Y-%m-%d %H:%M:%S')
            
            form_id = value.get('id')
            username = value.get('username')
            
            form_entry = Form(
                date=current_date,
                form_id=form_id,
                username=username,
                first_activity=first_activity,
                last_activity=last_activity,
                time_online=value.get('time_online', 0)
            )
            
            db_session.add(form_entry)
            db_session.commit()
            
            result["success"] += 1
            
        except Exception as e:
            db_session.rollback()
            result["errors"].append({
                "username": username if 'username' in locals() else "unknown",
                "error": f"Error: {str(e)}"
            })
    
    return result