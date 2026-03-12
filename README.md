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

## 환경 변수 (로컬 .env / Vercel Environment Variables)

로컬: 프로젝트 루트에 `.env` 파일 생성 (`.env.example` 참고).  
**Vercel 배포 시**: 프로젝트 → Settings → Environment Variables 에서 아래 변수 추가.

| 변수 | 설명 |
|------|------|
| `TEAM_PASSWORD` | 팀 프로젝트 비밀번호. 설정 시 사이트 접속 시 로그인 필수 (비우면 비밀번호 없이 접속) |
| `SMTP_USER` | 이메일 발송용 Gmail 주소 |
| `SMTP_PASSWORD` | Gmail 앱 비밀번호 (2단계 인증 후 생성) |
| `SECRET_KEY` | Flask 세션 암호화용 (운영 시 랜덤 문자열 권장) |

## 이메일 발송 설정

이메일을 실제로 보내려면 **SMTP** 설정이 필요합니다. (로컬은 `.env`, Vercel은 환경 변수에 설정)

1. **SMTP_USER**: 본인 Gmail 주소  
2. **SMTP_PASSWORD**: [Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호] 로 생성한 비밀번호  

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 엑셀 형식

- **Inventory** 시트: 품목코드, 재료명, 규격, 단위, 현재재고, 안전재고, MOQ, 거래처, 거래처이메일, 리드타임(일) 등
- **Suppliers** 시트: 거래처명, 담당자, 이메일, 리드타임(일), 품목군

`domino_inventory_training.xlsx` 를 참고하면 됩니다.
