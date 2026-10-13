// 복용 알림 — 매일 반복 알림의 둘째 날부터도 잠든 폰을 깨워 제시간에 울리게 고친다(2026-10-13 점검 1-03).
//
// @capacitor/local-notifications 8.3.1 은 첫 회만 setExactAndAllowWhileIdle(RTC_WAKEUP)로 걸고,
// 울린 뒤 다음 날 것은 TimedNotificationPublisher 가 setExact/set(AlarmManager.RTC, …)로 다시 건다.
// RTC 는 폰을 깨우지 않고 도즈(밤새 둔 폰)에서 미뤄지므로, 앱을 며칠 안 여는 분일수록 아침 약 알림이 늦는다.
// npm install / npm ci 뒤(postinstall) 이 두 줄만 깨우는 꼴로 바꾼다. 플러그인 판이 바뀌어 줄을 못 찾으면
// 빌드를 멈춰 사람이 다시 보게 한다(조용히 옛 동작으로 돌아가지 않게).
'use strict';
const fs = require('fs');
const path = require('path');

const file = path.join(__dirname, '..', 'node_modules', '@capacitor', 'local-notifications', 'android', 'src', 'main',
  'kotlin', 'com', 'capacitorjs', 'plugins', 'localnotifications', 'TimedNotificationPublisher.kt');

const swaps = [
  ['alarmManager.setExact(AlarmManager.RTC, trigger, pendingIntent)',
   'alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pendingIntent)'],
  ['alarmManager.set(AlarmManager.RTC, trigger, pendingIntent)',
   'alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, pendingIntent)'],
];

if (!fs.existsSync(file)) {
  console.error('[patch-local-notifications] 파일이 없습니다: ' + file);
  process.exit(1);
}
let src = fs.readFileSync(file, 'utf8');
let changed = 0;
for (const [from, to] of swaps) {
  if (src.includes(to) && !src.includes(from)) continue;      // 이미 고침
  if (!src.includes(from)) {
    console.error('[patch-local-notifications] 고칠 줄을 못 찾았습니다(플러그인 판이 바뀜?): ' + from);
    console.error('  → TimedNotificationPublisher.kt 의 재예약 코드를 다시 보고 이 스크립트를 맞춰 주세요.');
    process.exit(1);
  }
  src = src.split(from).join(to);
  changed++;
}
if (changed) fs.writeFileSync(file, src);
console.log('[patch-local-notifications] 반복 알림 재예약을 깨우는 꼴로 ' + (changed ? '고쳤습니다' : '이미 고쳐져 있습니다'));
