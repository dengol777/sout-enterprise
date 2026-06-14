import base64
import json
import time
import uuid
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

router = APIRouter(prefix="/auth/esia", tags=["ЕСИА Авторизация"])

# Конфигурация (хранить в Vault/env!)
ESIA_CONFIG = {
    "client_id": "YOUR_SYSTEM_ID",
    "redirect_uri": "https://sout.company.local/auth/esia/callback",
    "scope": "openid fullname id_doc snils",  # Минимальный набор для КЭДО
    "auth_url": "https://login.esia.gosuslugi.ru/aas/oauth2/ac",
    "token_url": "https://login.esia.gosuslugi.ru/aas/oauth2/te",
    "info_url": "https://login.esia.gosuslugi.ru/rs/prns",
}


def _generate_state() -> str:
    """Генерация уникального state для защиты от CSRF"""
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip("=")


@router.get("/login")
async def esia_login(response: Response):
    """Перенаправляет пользователя на страницу входа Госуслуг"""
    state = _generate_state()
    
    # Сохраняем state в cookie для проверки при callback
    response.set_cookie(
        key="esia_oauth_state", 
        value=state, 
        httponly=True, 
        secure=True,
        max_age=300
    )
    
    params = {
        "client_id": ESIA_CONFIG["client_id"],
        "redirect_uri": ESIA_CONFIG["redirect_uri"],
        "scope": ESIA_CONFIG["scope"],
        "response_type": "code",
        "state": state,
        "access_type": "offline",  # Обязательно для получения refresh_token!
    }
    
    return {"redirect_url": f"{ESIA_CONFIG['auth_url']}?{urlencode(params)}"}


@router.get("/callback")
async def esia_callback(
    code: str,
    state: str,
    esia_oauth_state: str = Depends(lambda r: r.cookies.get("esia_oauth_state")),
    session: Session = Depends(get_session)
):
    """Обрабатывает возврат из ЕСИА, обменивает code на токены"""
    # 1. Проверка state (защита от CSRF)
    if state != esia_oauth_state:
        raise HTTPException(status_code=403, detail="Invalid OAuth state")
    
    # 2. Обмен кода на токены
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            ESIA_CONFIG["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": ESIA_CONFIG["client_id"],
                "redirect_uri": ESIA_CONFIG["redirect_uri"],
                "scope": ESIA_CONFIG["scope"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_resp.text}")
        
        tokens = token_resp.json()
    
    # 3. Получение профиля пользователя (SNIILS, ФИО)
    access_token = tokens["access_token"]
    oid = _extract_oid_from_token(access_token)
    
    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(
            f"{ESIA_CONFIG['info_url']}/{oid}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile = profile_resp.json()
    
    # 4. Связывание с сотрудником в БД по SNIILS
    employee = session.exec(
        select(Employee).where(Employee.snils == profile.get("snils"))
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=404, 
            detail="Сотрудник с таким СНИЛС не найден в системе. Обратитесь к специалисту по ОТ."
        )
    
    # 5. Сохраняем refresh_token для автоматического продления
    employee.esia_refresh_token = tokens.get("refresh_token")
    employee.esia_oid = oid
    session.add(employee)
    session.commit()
    
    return {
        "message": "Авторизация успешна",
        "employee_id": employee.id,
        "full_name": profile.get("fullName"),
    }


def _extract_oid_from_token(access_token: str) -> str:
    """Извлекает OID (идентификатор физлица) из JWT access_token ЕСИА"""
    try:
        payload_part = access_token.split(".")[1]
        # Добавляем padding если нужно
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += "=" * padding
        
        decoded = base64.urlsafe_b64decode(payload_part)
        payload = json.loads(decoded)
        return payload["urn:esia:sbj_id"]
    except Exception:
        raise HTTPException(status_code=400, detail="Не удалось извлечь OID из токена ЕСИА")
