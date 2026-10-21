package com.plaguedmods.mediastudio;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import com.arthenica.ffmpegkit.FFmpegKit;
import com.arthenica.ffmpegkit.ReturnCode;
import java.io.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private Uri input;
    private Spinner format;
    private TextView status;
    private Button convert;
    private String extension;
    private static final String[] FORMATS = {"mp3","wav","flac","ogg","m4a","mp4","mkv","webm","avi","mov"};
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout root = new LinearLayout(this);
        root.setPadding(32, 45, 32, 24);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xff121a25);
        TextView title = new TextView(this);
        title.setText("Plague's Media Studio");
        title.setTextColor(0xffe6edf4);
        title.setTextSize(26);
        root.addView(title);
        Button select = new Button(this);
        select.setText("Choose media file");
        select.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.setType("*/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(intent, 11);
        });
        root.addView(select);
        format = new Spinner(this);
        format.setAdapter(new ArrayAdapter<String>(this, android.R.layout.simple_spinner_dropdown_item, FORMATS));
        root.addView(format);
        convert = new Button(this);
        convert.setText("Convert and save");
        convert.setEnabled(false);
        convert.setOnClickListener(v -> {
            extension = FORMATS[format.getSelectedItemPosition()];
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.setType("application/octet-stream");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.putExtra(Intent.EXTRA_TITLE, "converted." + extension);
            startActivityForResult(intent, 12);
        });
        root.addView(convert);
        status = new TextView(this);
        status.setTextColor(0xffb4c9d9);
        status.setText("Choose a file to begin. Conversion happens on your device.");
        root.addView(status);
        setContentView(root);
    }
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (result != RESULT_OK || data == null || data.getData() == null) return;
        if (request == 11) {
            input = data.getData();
            convert.setEnabled(true);
            status.setText("File selected. Choose the output format.");
        } else if (request == 12 && input != null) {
            Uri output = data.getData();
            convert.setEnabled(false);
            status.setText("Converting…");
            worker.execute(() -> transcode(input, output, extension));
        }
    }
    private static String quote(String value) {
        return "'" + value.replace("'", "'\\''") + "'";
    }
    private void transcode(Uri source, Uri dest, String fmt) {
        File in = null, out = null;
        try {
            in = File.createTempFile("studio-in-", ".media", getCacheDir());
            out = File.createTempFile("studio-out-", "." + fmt, getCacheDir());
            try (InputStream stream = getContentResolver().openInputStream(source);
                 OutputStream target = new FileOutputStream(in)) {
                if (stream == null) throw new IOException("Cannot read selected file");
                byte[] buf = new byte[65536];
                int n;
                while ((n = stream.read(buf)) != -1) target.write(buf, 0, n);
            }
            String args = "-hide_banner -nostdin -y -i " + quote(in.getAbsolutePath())
                + (fmt.matches("mp3|wav|flac|ogg|m4a") ? " -vn " : " ")
                + quote(out.getAbsolutePath());
            var session = FFmpegKit.execute(args);
            if (!ReturnCode.isSuccess(session.getReturnCode())) {
                throw new IOException("FFmpeg failed: " + session.getFailStackTrace());
            }
            try (InputStream stream = new FileInputStream(out);
                 OutputStream target = getContentResolver().openOutputStream(dest, "w")) {
                if (target == null) throw new IOException("Cannot save destination");
                byte[] buf = new byte[65536];
                int n;
                while ((n = stream.read(buf)) != -1) target.write(buf, 0, n);
            }
            runOnUiThread(() -> status.setText("Saved converted file."));
        } catch (Exception ex) {
            String message = ex.getMessage();
            runOnUiThread(() -> status.setText("Conversion error: " + message));
        } finally {
            if (in != null) in.delete();
            if (out != null) out.delete();
            runOnUiThread(() -> convert.setEnabled(true));
        }
    }
}
