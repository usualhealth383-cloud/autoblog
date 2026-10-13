package app.yakjido;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.core.content.ContextCompat;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebChromeClient;

public class MainActivity extends BridgeActivity {

    // 홈 날씨 「내 위치」 — 대략 위치(ACCESS_COARSE_LOCATION)만 묻는다.
    // Capacitor 기본 처리기는 대략·정밀 위치를 함께 묻고, 정밀 위치를 선언하지 않은 앱은
    // 안드로이드 11 이하에서 허용을 눌러도 늘 거절로 끝난다(2026-10-13 점검 1-12).
    private GeolocationPermissions.Callback geoCallback;
    private String geoOrigin;

    private final ActivityResultLauncher<String> coarseLauncher = registerForActivityResult(
        new ActivityResultContracts.RequestPermission(),
        granted -> {
            GeolocationPermissions.Callback cb = geoCallback;
            String origin = geoOrigin;
            geoCallback = null;
            geoOrigin = null;
            if (cb != null) cb.invoke(origin, Boolean.TRUE.equals(granted), false);
        }
    );

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (bridge == null || bridge.getWebView() == null) return;
        // 나머지(파일 고르기·카메라·알림창 등)는 Capacitor 처리기를 그대로 쓴다.
        bridge.getWebView().setWebChromeClient(new BridgeWebChromeClient(bridge) {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.ACCESS_COARSE_LOCATION)
                    == PackageManager.PERMISSION_GRANTED) {
                    callback.invoke(origin, true, false);
                    return;
                }
                if (geoCallback != null) geoCallback.invoke(geoOrigin, false, false);
                geoCallback = callback;
                geoOrigin = origin;
                coarseLauncher.launch(Manifest.permission.ACCESS_COARSE_LOCATION);
            }
        });
    }
}
