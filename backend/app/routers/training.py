from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TrainingContent

router = APIRouter(tags=["training"])

TRANSLATED = {
    "ta": ("இயந்திர பாதுகாப்பு பயிற்சி", "இயந்திர வெப்பநிலை, அழுத்தம் மற்றும் சுற்றுப்புற பாதுகாப்பு நிலைகளை கண்காணிக்கவும். பாதுகாப்பு வரம்புகள் மீறப்பட்டால் இயந்திரத்தை நிறுத்தவும்."),
    "hi": ("मशीन सुरक्षा प्रशिक्षण", "मशीन के तापमान, दबाव और आसपास की सुरक्षा स्थितियों की निगरानी करें। सुरक्षित सीमा पार होने पर मशीन रोक दें।"),
    "te": ("యంత్ర భద్రత శిక్షణ", "యంత్ర ఉష్ణోగ్రత, పీడనం మరియు పరిసర భద్రతను పర్యవేక్షించండి. సురక్షిత పరిమితులు దాటితే యంత్రాన్ని ఆపండి."),
    "kn": ("ಯಂತ್ರ ಸುರಕ್ಷತಾ ತರಬೇತಿ", "ಯಂತ್ರದ ತಾಪಮಾನ, ಒತ್ತಡ ಮತ್ತು ಸುತ್ತಮುತ್ತಲಿನ ಸುರಕ್ಷತಾ ಪರಿಸ್ಥಿತಿಗಳನ್ನು ಗಮನಿಸಿ. ಸುರಕ್ಷಿತ ಮಿತಿಗಳನ್ನು ಮೀರಿದರೆ ಯಂತ್ರವನ್ನು ನಿಲ್ಲಿಸಿ."),
}

@router.get("/training-content")
def training(alert_type: str | None = None, lang: str = "en", limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(TrainingContent)
    if alert_type: q = q.filter(TrainingContent.related_alert_type == alert_type)
    rows = q.order_by(TrainingContent.id).offset(offset).limit(limit).all()
    if not rows:
        rows = [TrainingContent(id=0, title="Machine Safety", body_text="Monitor machine temperature and pressure. Stop when safe operating thresholds are exceeded.", related_alert_type=alert_type)]
    result=[]
    for r in rows:
        title, body = r.title, r.body_text
        if lang in TRANSLATED: title, body = TRANSLATED[lang]
        result.append({"id": r.id, "title": title, "body_text": body, "related_alert_type": r.related_alert_type, "language": lang})
    return {"content": result}
