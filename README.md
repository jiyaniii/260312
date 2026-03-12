# 도미노피자 재고·발주 자동화

재고를 파악하고, 부족 시 담당 기업 직원에게 **발주서를 이메일로 보내는** 웹 시스템입니다.

- **데이터 입력**: 엑셀 파일 업로드 또는 샘플 데이터 사용
- **분석**: 현재재고 < 안전재고 → 발주 필요, 발주 권장 수량 = MAX(MOQ, 안전재고−현재재고)
- **발주 이메일 수신 주소**: `songjy0727@gmail.com`

## 실행 방법

```bash
# 가상환경 활성화
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 패키지 설치 (최초 1회)
pip install -r requirements.txt

# 서버 실행
python app.py
```

브라우저에서 **http://127.0.0.1:5050** 접속 후, (포트 변경: `PORT=8080 python app.py`)

1. **엑셀 업로드**: Inventory, Suppliers 시트가 있는 엑셀을 올리거나  
2. **샘플 데이터로 분석**: "샘플 데이터로 분석하기" 클릭  
3. 결과 페이지에서 **발주서 이메일 보내기** 클릭 시 `songjy0727@gmail.com` 으로 발주 요약 메일이 발송됩니다.

## 이메일 발송 설정

이메일을 실제로 보내려면 SMTP 설정이 필요합니다.

1. 프로젝트 루트에 `.env` 파일 생성 (또는 `.env.example` 복사 후 수정)
2. Gmail 예시:
   - `SMTP_USER`: 본인 Gmail 주소
   - `SMTP_PASSWORD`: [Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호] 로 생성한 비밀번호

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

`.env` 로드에는 `python-dotenv` 를 사용할 수 있습니다. (선택 사항)

```bash
pip install python-dotenv
```

그리고 `app.py` 상단에 다음 추가:

```python
from dotenv import load_dotenv
load_dotenv()
```

## 엑셀 형식

- **Inventory** 시트: 품목코드, 재료명, 규격, 단위, 현재재고, 안전재고, MOQ, 거래처, 거래처이메일, 리드타임(일) 등
- **Suppliers** 시트: 거래처명, 담당자, 이메일, 리드타임(일), 품목군

`domino_inventory_training.xlsx` 를 참고하면 됩니다.
