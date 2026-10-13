package app.yakjido;

import android.Manifest;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.ValueCallback;
import android.webkit.WebView;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.PickVisualMediaRequest;
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

    // 「앨범에서 고르기」 — 안드로이드 사진 선택기(Photo Picker)로 연다. 앱이 사진 권한을 묻지 않고(「모두 허용·제한된 액세스」 창 없음)
    // 고른 사진 한 장만 받는다. 구글 권장 방식이며, 오래된 폰은 구글 플레이 서비스가 같은 선택기를 대신 띄운다(2026-10-13 현욱님).
    // 「카메라로 찍기」(capture) 는 Capacitor 처리기 그대로 — 카메라 앱을 띄워 찍은 사진만 받으므로 카메라 권한도 묻지 않는다.
    private ValueCallback<Uri[]> pickCallback;

    private final ActivityResultLauncher<PickVisualMediaRequest> photoPicker = registerForActivityResult(
        new ActivityResultContracts.PickVisualMedia(),
        uri -> {
            ValueCallback<Uri[]> cb = pickCallback;
            pickCallback = null;
            if (cb != null) cb.onReceiveValue(uri == null ? null : new Uri[] { uri });
        }
    );

    private static boolean imagesOnly(String[] types) {
        if (types == null || types.length == 0) return false;
        for (String t : types) if (t == null || !t.startsWith("image/")) return false;
        return true;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (bridge == null || bridge.getWebView() == null) return;
        // 나머지(카메라·다른 파일 고르기·알림창 등)는 Capacitor 처리기를 그대로 쓴다.
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

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (params.isCaptureEnabled() || params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE || !imagesOnly(params.getAcceptTypes())) {
                    return super.onShowFileChooser(webView, callback, params);
                }
                // 웹뷰는 앞선 고르기에 답이 없으면 다음 고르기를 열지 않는다 — 남은 것은 «고르지 않음»으로 닫는다
                if (pickCallback != null) pickCallback.onReceiveValue(null);
                pickCallback = callback;
                try {
                    photoPicker.launch(new PickVisualMediaRequest.Builder()
                        .setMediaType(ActivityResultContracts.PickVisualMedia.ImageOnly.INSTANCE)
                        .build());
                    return true;
                } catch (Exception e) {
                    pickCallback = null;
                    return super.onShowFileChooser(webView, callback, params);
                }
            }
        });
    }
}
