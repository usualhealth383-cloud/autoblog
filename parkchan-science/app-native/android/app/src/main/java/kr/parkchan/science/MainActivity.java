package kr.parkchan.science;

import android.os.Bundle;
import android.view.WindowManager;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SecureScreenPlugin.class);
        super.onCreate(savedInstanceState);
        // 앱이 뜨는 순간부터 막아 두고(최근 앱 미리보기 포함), 화면이 정해지면 앱이 SecureScreen.set 으로 조절한다
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
}
