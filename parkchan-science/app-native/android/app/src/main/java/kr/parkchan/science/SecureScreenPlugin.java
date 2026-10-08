package kr.parkchan.science;

import android.view.WindowManager;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * 교재 화면 캡처 막기 (docs/03-기획-결정사항.md '캡처 방지').
 * FLAG_SECURE 를 켜면 스크린샷·화면 녹화·최근 앱 미리보기에 화면이 찍히지 않는다.
 * 앱이 화면마다 켜고 끈다 — 교재·문제 화면은 켜고, 공부 노트·일정·이야기·내 정보는 끈다(학생이 자기 기록은 캡처할 수 있게).
 */
@CapacitorPlugin(name = "SecureScreen")
public class SecureScreenPlugin extends Plugin {
    @PluginMethod
    public void set(PluginCall call) {
        final boolean on = Boolean.TRUE.equals(call.getBoolean("on", Boolean.TRUE));
        getActivity().runOnUiThread(() -> {
            if (on) getActivity().getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
            else getActivity().getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE);
            call.resolve();
        });
    }
}
