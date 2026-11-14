package dz.ouin.app;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView web;
    private SharedPreferences prefs;
    private GeolocationPermissions.Callback geoCb;
    private String geoOrigin;

    /** عنوان الخادم بلا شرطة أخيرة ولا /app */
    private static String clean(String u) {
        if (u == null) return "";
        u = u.trim().replaceAll("[\"'<>\\s]", "");
        if (u.isEmpty()) return "";
        if (!u.startsWith("http")) u = "https://" + u;
        u = u.replaceAll("/+$", "");
        if (u.endsWith("/app")) u = u.substring(0, u.length() - 4);
        return u;
    }

    private String base() {
        String saved = prefs.getString("url", null);
        return clean(saved != null ? saved : getString(R.string.app_url));
    }

    /** صفحة البداية: عنوان ينتهي بـ .html يُستعمل كما هو، وإلا نضيف /app (خادم Flask) */
    private static String start(String b) {
        return b.endsWith(".html") ? b : b + "/app";
    }

    private boolean placeholder(String b) {
        return b.isEmpty() || b.contains("example.com");
    }

    private String host() {
        String h = Uri.parse(base()).getHost();
        return h == null ? "" : h;
    }

    private void open() {
        String b = base();
        if (placeholder(b)) showSettings("أدخل عنوان المنصة لبدء الاستخدام");
        else web.loadUrl(start(b));
    }

    /** صفحة محلية لإدخال عنوان الخادم (مفيدة عند تغيّر الرابط المؤقت). */
    private void showSettings(String msg) {
        String cur = base();
        if (placeholder(cur)) cur = "";
        String html = "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                + "<body dir='rtl' style='font-family:sans-serif;padding:28px;text-align:center'>"
                + "<h2>وين؟ DZ</h2><p>" + msg + "</p>"
                + "<input id='u' placeholder='https://...' value='" + cur
                + "' style='width:100%;padding:12px;font-size:16px;direction:ltr;box-sizing:border-box'>"
                + "<p><button onclick=\"ouinApp.setUrl(document.getElementById('u').value)\""
                + " style='padding:12px 28px;font-size:16px'>اتصال</button></p></body>";
        web.loadDataWithBaseURL("https://localhost/", html, "text/html", "utf-8", null);
    }

    private class Bridge {
        @JavascriptInterface
        public void setUrl(String u) {
            final String n = clean(u);
            if (n.isEmpty()) return;
            prefs.edit().putString("url", n).apply();
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    web.loadUrl(start(n));
                }
            });
        }
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("ouin", MODE_PRIVATE);
        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setGeolocationEnabled(true);
        web.addJavascriptInterface(new Bridge(), "ouinApp");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                if (host().equals(u.getHost())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) { }
                return true;
            }

            @Override
            public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                if (r.isForMainFrame()) showSettings("تعذّر الوصول إلى الخادم. تحقق من الإنترنت أو أدخل العنوان الحالي.");
            }

            @Override
            public void onReceivedHttpError(WebView v, WebResourceRequest r, WebResourceResponse e) {
                if (r.isForMainFrame() && e.getStatusCode() >= 400 && host().equals(r.getUrl().getHost())) {
                    showSettings("الخادم لا يستجيب (" + e.getStatusCode() + "). أدخل العنوان الحالي للمنصة.");
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                    cb.invoke(origin, true, false);
                } else {
                    geoCb = cb;
                    geoOrigin = origin;
                    requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
                }
            }
        });

        if (state != null) web.restoreState(state); else open();
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] res) {
        super.onRequestPermissionsResult(code, perms, res);
        if (geoCb != null) {
            boolean ok = res.length > 0 && res[0] == PackageManager.PERMISSION_GRANTED;
            geoCb.invoke(geoOrigin, ok, false);
            geoCb = null;
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
