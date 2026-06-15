# 오라클 클라우드 평생무료 배포 가이드

PC와 무관하게 24시간 매일 06:00(KST) 글 생성 + 텔레그램 알림이 돌아가게 한다.

## A. 오라클 클라우드 계정 + 서버(VM) 만들기
1. https://www.oracle.com/kr/cloud/free/ → "무료로 시작하기" → 가입
   - 신원 확인용 카드 등록 필요(평생무료 자원은 과금되지 않음). 가입 승인에 시간이 걸릴 수 있음.
2. 콘솔 로그인 → **Compute > Instances > Create Instance**
   - 이름: autoblog
   - 이미지: **Canonical Ubuntu 22.04**
   - Shape: **Ampere(ARM) VM.Standard.A1.Flex** (Always Free 대상) — OCPU 1, 메모리 6GB 정도면 충분
   - **SSH 키**: "Generate a key pair for me" → **개인 키(.key) 다운로드 후 잘 보관**
   - Create
3. 인스턴스의 **Public IP** 확인(예: 140.x.x.x)
4. 방화벽: 별도 포트 개방 불필요(텔레그램은 아웃바운드만 사용).

## B. 코드 + 비밀파일 서버로 올리기 (PC에서)
서버 접속:
```
ssh -i <다운받은키.key> ubuntu@<서버IP>
```
PC의 auto_blog 폴더를 서버로 복사(PowerShell scp 또는 WinSCP). 특히 아래 비밀파일 필수:
- `.env`  (OpenAI 키, 텔레그램 토큰, BLOGGER_BLOG_ID 등)
- `config/client_secret.json`, `config/token.json` (Blogger 인증 — 재로그인 불필요)
- `config/telegram_chats.json` (chat_id)

예시(PowerShell, 폴더 통째로):
```
scp -i <키.key> -r C:\Users\parkh\OneDrive\capcut\auto_blog\* ubuntu@<서버IP>:/home/ubuntu/auto_blog/
```
(.venv, data 폴더는 빼고 올려도 됨)

## C. 서버에서 설치 1줄
```
cd ~/auto_blog && bash deploy/setup.sh
```
끝나면 부팅 시 자동 시작되는 서비스로 등록된다.

## 확인/운영
- 실시간 로그: `journalctl -u autoblog -f`
- 재시작: `sudo systemctl restart autoblog`
- 매일 06:00(KST) 자동 생성 → 텔레그램 알림 → 폰에서 승인.

> PC의 서비스(시작프로그램)는 더 이상 필요 없으니, 중복 방지를 위해 PC쪽 서비스는 꺼두세요
> (시작프로그램에서 AutoBlogService 제거). 텔레그램 봇은 한 곳에서만 돌려야 합니다.
