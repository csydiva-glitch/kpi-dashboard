"""Firebase 초기화 · Auth · Firestore 헬퍼"""
import os, json, math
import requests

# ── 설정 로드 순서: st.secrets → 환경변수 ────────────────────────────────────
def _secret(key: str, default: str = '') -> str:
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)

FIREBASE_API_KEY  = _secret('FIREBASE_API_KEY')
FIREBASE_PROJECT  = _secret('FIREBASE_PROJECT_ID', 'board-f7d4b')
_SA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serviceAccountKey.json')

# ── Firebase Admin 초기화 ──────────────────────────────────────────────────────
def _init_app():
    import firebase_admin
    from firebase_admin import credentials
    if firebase_admin._apps:
        return firebase_admin.get_app()

    sa_json = _secret('FIREBASE_SERVICE_ACCOUNT')
    if sa_json:
        cred = credentials.Certificate(json.loads(sa_json))
    elif os.path.exists(_SA_FILE):
        cred = credentials.Certificate(_SA_FILE)
    else:
        return None
    return firebase_admin.initialize_app(cred, {'projectId': FIREBASE_PROJECT})

def is_firebase_available() -> bool:
    """서비스 계정(파일 또는 secrets)이 있으면 True"""
    return bool(_secret('FIREBASE_SERVICE_ACCOUNT')) or os.path.exists(_SA_FILE)

def get_db():
    """Firestore 클라이언트 반환. 미설정이면 None."""
    app = _init_app()
    if app is None:
        return None
    from firebase_admin import firestore
    return firestore.client()

# ── Authentication ─────────────────────────────────────────────────────────────
_ERR_MAP = {
    'EMAIL_NOT_FOUND':           '등록되지 않은 이메일입니다.',
    'INVALID_PASSWORD':          '비밀번호가 올바르지 않습니다.',
    'INVALID_EMAIL':             '이메일 형식이 올바르지 않습니다.',
    'USER_DISABLED':             '비활성화된 계정입니다.',
    'TOO_MANY_ATTEMPTS_TRY_LATER': '로그인 시도가 너무 많습니다. 잠시 후 다시 시도하세요.',
    'INVALID_LOGIN_CREDENTIALS': '이메일 또는 비밀번호가 올바르지 않습니다.',
}

def sign_in(email: str, password: str) -> dict:
    """Firebase Auth REST API 이메일/비밀번호 로그인."""
    if not FIREBASE_API_KEY:
        return {'ok': False, 'error': 'secrets.toml에 FIREBASE_API_KEY가 없습니다.'}
    url = ('https://identitytoolkit.googleapis.com/v1/accounts'
           f':signInWithPassword?key={FIREBASE_API_KEY}')
    try:
        r = requests.post(url, json={
            'email': email, 'password': password, 'returnSecureToken': True
        }, timeout=10)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'네트워크 오류: {e}'}
    if r.status_code == 200:
        d = r.json()
        return {
            'ok': True,
            'id_token':    d['idToken'],
            'email':       d['email'],
            'display_name': d.get('displayName', d['email'].split('@')[0]),
        }
    err_code = r.json().get('error', {}).get('message', '로그인 실패')
    return {'ok': False, 'error': _ERR_MAP.get(err_code, err_code)}

def verify_id_token(id_token: str) -> dict | None:
    app = _init_app()
    if app is None:
        return None
    from firebase_admin import auth
    try:
        return auth.verify_id_token(id_token)
    except Exception:
        return None

# ── Firestore KPI 데이터 ───────────────────────────────────────────────────────
COLLECTION = 'kpi_2025'

def load_kpi_records() -> list[dict]:
    db = get_db()
    if db is None:
        return []
    return [doc.to_dict() for doc in db.collection(COLLECTION).stream()]

def upload_kpi_df(df) -> int:
    """DataFrame → Firestore kpi_2025 컬렉션 (기존 데이터 대체). 저장 건수 반환."""
    db = get_db()
    if db is None:
        raise RuntimeError('Firebase 연결 실패 — serviceAccountKey.json을 확인하세요.')
    col_ref = db.collection(COLLECTION)

    # 기존 문서 삭제
    existing = list(col_ref.stream())
    for i in range(0, len(existing), 499):
        batch = db.batch()
        for doc in existing[i:i+499]:
            batch.delete(doc.reference)
        batch.commit()

    # 신규 업로드 (NaN → None, 계산 컬럼 제외)
    _skip = {'_ach', '_tl', '_delta', '_warn', 'KPI_ID'}
    records = df.to_dict('records')
    for i in range(0, len(records), 499):
        batch = db.batch()
        for rec in records[i:i+499]:
            clean = {
                k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in rec.items() if k not in _skip
            }
            batch.set(col_ref.document(), clean)
        batch.commit()
    return len(records)
