package com.plaguedmods.mediastudio;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;

import com.arthenica.ffmpegkit.FFmpegKit;
import com.arthenica.ffmpegkit.ReturnCode;
import com.arthenica.ffmpegkit.FFmpegSession;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Phone-friendly local media conversion with the same branding as desktop. */
public class MainActivity extends Activity {
    private static final int NAVY = Color.rgb(10, 18, 29);
    private static final int PANEL = Color.rgb(20, 37, 51);
    private static final int PANEL_BORDER = Color.rgb(57, 86, 103);
    private static final int AQUA = Color.rgb(72, 223, 199);
    private static final int WHITE = Color.rgb(237, 246, 250);
    private static final int MUTED = Color.rgb(169, 192, 205);
    private static final String[] FORMATS = {
        "mp3", "wav", "flac", "ogg", "m4a", "mp4", "mkv", "webm", "avi", "mov"
    };
    private static final String[] FORMAT_LABELS = {
        "MP3  ·  Audio", "WAV  ·  Audio", "FLAC  ·  Audio", "OGG  ·  Audio",
        "M4A  ·  Audio", "MP4  ·  Video", "MKV  ·  Video", "WebM  ·  Video",
        "AVI  ·  Video", "MOV  ·  Video"
    };
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private Uri sourceUri;
    private Spinner formatSpinner;
    private TextView sourceName;
    private TextView statusText;
    private Button convertButton;
    private ProgressBar progress;
    private String pendingFormat;

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private GradientDrawable rounded(int color, int radius, int borderColor) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(color);
        shape.setCornerRadius(dp(radius));
        if (borderColor != 0) shape.setStroke(dp(1), borderColor);
        return shape;
    }

    private TextView text(String content, float sp, int color, boolean bold) {
        TextView text = new TextView(this);
        text.setText(content);
        text.setTextSize(sp);
        text.setTextColor(color);
        if (bold) text.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return text;
    }

    private Button button(String title, boolean primary) {
        Button button = new Button(this);
        button.setText(title);
        button.setAllCaps(false);
        button.setTextSize(15);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setTextColor(primary ? NAVY : WHITE);
        button.setBackground(rounded(primary ? AQUA : Color.rgb(31, 55, 73), 11,
                primary ? AQUA : PANEL_BORDER));
        button.setMinHeight(dp(52));
        button.setPadding(dp(16), dp(12), dp(16), dp(12));
        return button;
    }

    private LinearLayout vertical() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        return layout;
    }

    private LinearLayout card() {
        LinearLayout layout = vertical();
        layout.setPadding(dp(19), dp(19), dp(19), dp(19));
        layout.setBackground(rounded(PANEL, 17, PANEL_BORDER));
        return layout;
    }

    private void gap(LinearLayout parent, int heightDp) {
        View spacer = new View(this);
        parent.addView(spacer, new LinearLayout.LayoutParams(1, dp(heightDp)));
    }

    private void sectionHeading(LinearLayout parent, String label) {
        TextView heading = text(label, 12, AQUA, true);
        heading.setLetterSpacing(0.1f);
        parent.addView(heading);
        gap(parent, 11);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(NAVY);
        getWindow().setNavigationBarColor(NAVY);
        ScrollView scrolling = new ScrollView(this);
        scrolling.setFillViewport(true);
        scrolling.setBackgroundColor(NAVY);
        LinearLayout root = vertical();
        root.setPadding(dp(20), dp(26), dp(20), dp(26));
        scrolling.addView(root);

        // Brand header: scalable source asset, generous text sizes, and high contrast.
        LinearLayout brand = new LinearLayout(this);
        brand.setOrientation(LinearLayout.HORIZONTAL);
        brand.setGravity(Gravity.CENTER_VERTICAL);
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pms_brand);
        logo.setContentDescription("Plague's Media Studio logo");
        brand.addView(logo, new LinearLayout.LayoutParams(dp(74), dp(74)));
        LinearLayout labels = vertical();
        labels.setPadding(dp(13), 0, 0, 0);
        labels.addView(text("PLAGUED MODS / CREATIVE TOOLS", 10, AQUA, true));
        gap(labels, 4);
        TextView name = text("Plague's Media\nStudio", 23, WHITE, true);
        name.setLineSpacing(0, 0.95f);
        labels.addView(name);
        brand.addView(labels);
        root.addView(brand);
        gap(root, 9);
        root.addView(text("Your media. Your device. Your workflow.", 13, MUTED, false));
        gap(root, 25);

        LinearLayout importCard = card();
        sectionHeading(importCard, "01  /  SOURCE MEDIA");
        sourceName = text("No file selected", 16, WHITE, true);
        sourceName.setMaxLines(2);
        sourceName.setEllipsize(android.text.TextUtils.TruncateAt.END);
        importCard.addView(sourceName);
        gap(importCard, 6);
        importCard.addView(text("Choose audio or video from your phone or storage.", 13, MUTED, false));
        gap(importCard, 15);
        Button selectButton = button("＋  Choose media file", false);
        selectButton.setOnClickListener(v -> chooseSource());
        importCard.addView(selectButton);
        root.addView(importCard);
        gap(root, 17);

        LinearLayout settingsCard = card();
        sectionHeading(settingsCard, "02  /  CONVERSION SETTINGS");
        settingsCard.addView(text("OUTPUT FORMAT", 12, MUTED, true));
        gap(settingsCard, 10);
        formatSpinner = new Spinner(this);
        ArrayAdapter<String> formats = new ArrayAdapter<String>(this,
                android.R.layout.simple_spinner_item, FORMAT_LABELS) {
            @Override public View getView(int position, View convertView, ViewGroup parent) {
                return spinnerText(position);
            }
            @Override public View getDropDownView(int position, View convertView, ViewGroup parent) {
                return spinnerText(position);
            }
            private View spinnerText(int index) {
                TextView item = text(FORMAT_LABELS[index], 16, WHITE, true);
                item.setGravity(Gravity.CENTER_VERTICAL);
                item.setPadding(dp(14), dp(14), dp(10), dp(14));
                item.setBackgroundColor(Color.rgb(24, 43, 59));
                return item;
            }
        };
        formatSpinner.setAdapter(formats);
        formatSpinner.setBackground(rounded(Color.rgb(24, 43, 59), 11, PANEL_BORDER));
        settingsCard.addView(formatSpinner);
        gap(settingsCard, 11);
        settingsCard.addView(text("Audio can be extracted from supported video files.", 12, MUTED, false));
        root.addView(settingsCard);
        gap(root, 17);

        LinearLayout activityCard = card();
        sectionHeading(activityCard, "03  /  ACTIVITY");
        LinearLayout activityRow = new LinearLayout(this);
        activityRow.setOrientation(LinearLayout.HORIZONTAL);
        activityRow.setGravity(Gravity.CENTER_VERTICAL);
        statusText = text("Ready for a media file", 14, WHITE, true);
        statusText.setMaxLines(3);
        activityRow.addView(statusText, new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        progress = new ProgressBar(this);
        progress.setIndeterminate(true);
        progress.setVisibility(View.GONE);
        activityRow.addView(progress, new LinearLayout.LayoutParams(dp(30), dp(30)));
        activityCard.addView(activityRow);
        root.addView(activityCard);
        gap(root, 21);

        convertButton = button("▶  Convert and save", true);
        convertButton.setEnabled(false);
        convertButton.setOnClickListener(v -> chooseDestination());
        root.addView(convertButton);
        gap(root, 10);
        TextView local = text("Conversion happens on your device. Files are never uploaded.",
                12, MUTED, false);
        local.setGravity(Gravity.CENTER);
        root.addView(local);
        gap(root, 20);
        Button about = button("About Plague's Media Studio", false);
        about.setOnClickListener(v -> showAbout());
        root.addView(about);
        setContentView(scrolling);
    }

    private void chooseSource() {
        Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        pick.setType("*/*");
        pick.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(pick, 11);
    }

    private void chooseDestination() {
        pendingFormat = FORMATS[formatSpinner.getSelectedItemPosition()];
        String name = sourceUri == null ? "converted" : displayName(sourceUri);
        int dot = name.lastIndexOf('.');
        if (dot > 0) name = name.substring(0, dot);
        Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        save.setType("application/octet-stream");
        save.addCategory(Intent.CATEGORY_OPENABLE);
        save.putExtra(Intent.EXTRA_TITLE, name + "." + pendingFormat);
        startActivityForResult(save, 12);
    }

    private String displayName(Uri uri) {
        try (Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int column = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (column >= 0) return cursor.getString(column);
            }
        } catch (Exception ignored) {
            // A file name is optional; the content URI can still be opened.
        }
        return "media";
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (result != RESULT_OK || data == null || data.getData() == null) return;
        if (request == 11) {
            sourceUri = data.getData();
            sourceName.setText(displayName(sourceUri));
            statusText.setText("File selected. Choose a format to continue.");
            convertButton.setEnabled(true);
        } else if (request == 12 && sourceUri != null) {
            Uri target = data.getData();
            Uri source = sourceUri;
            String fmt = pendingFormat;
            progress.setVisibility(View.VISIBLE);
            statusText.setText("Converting media…");
            convertButton.setEnabled(false);
            executor.execute(() -> transcode(source, target, fmt));
        }
    }

    private void transcode(Uri source, Uri target, String fmt) {
        File sourceFile = null;
        File outputFile = null;
        String resultText;
        try {
            sourceFile = File.createTempFile("pms-source-", ".media", getCacheDir());
            outputFile = File.createTempFile("pms-output-", "." + fmt, getCacheDir());
            try (InputStream input = getContentResolver().openInputStream(source);
                 OutputStream output = new FileOutputStream(sourceFile)) {
                if (input == null) throw new IOException("Cannot read selected media");
                copy(input, output);
            }
            String argument = "-hide_banner -nostdin -y -i " + quote(sourceFile.getAbsolutePath())
                    + (isAudio(fmt) ? " -vn " : " ") + quote(outputFile.getAbsolutePath());
            FFmpegSession session = FFmpegKit.execute(argument);
            if (!ReturnCode.isSuccess(session.getReturnCode())) {
                throw new IOException("FFmpeg could not convert this file or format");
            }
            try (InputStream input = new FileInputStream(outputFile);
                 OutputStream output = getContentResolver().openOutputStream(target, "w")) {
                if (output == null) throw new IOException("Cannot save destination");
                copy(input, output);
            }
            resultText = "✓  Conversion complete. File saved.";
        } catch (Exception e) {
            resultText = "Conversion failed: " + e.getMessage();
        } finally {
            if (sourceFile != null) sourceFile.delete();
            if (outputFile != null) outputFile.delete();
        }
        final String completed = resultText;
        runOnUiThread(() -> {
            progress.setVisibility(View.GONE);
            statusText.setText(completed);
            convertButton.setEnabled(true);
        });
    }

    private static boolean isAudio(String format) {
        return format.equals("mp3") || format.equals("wav") || format.equals("flac")
                || format.equals("ogg") || format.equals("m4a");
    }

    private static String quote(String path) {
        return "'" + path.replace("'", "'\\''") + "'";
    }

    private static void copy(InputStream input, OutputStream output) throws IOException {
        byte[] data = new byte[65536];
        int count;
        while ((count = input.read(data)) != -1) output.write(data, 0, count);
    }

    private void showAbout() {
        LinearLayout body = vertical();
        body.setPadding(dp(20), dp(24), dp(20), dp(14));
        body.setBackgroundColor(PANEL);
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.pms_brand);
        LinearLayout.LayoutParams logoLayout = new LinearLayout.LayoutParams(dp(100), dp(100));
        logoLayout.gravity = Gravity.CENTER_HORIZONTAL;
        body.addView(logo, logoLayout);
        gap(body, 13);
        TextView heading = text("Plague's Media Studio", 21, WHITE, true);
        heading.setGravity(Gravity.CENTER);
        body.addView(heading);
        gap(body, 10);
        TextView info = text("Version 0.1.0\n\nLocal audio and video conversion powered by FFmpeg.\n\nCreated by Kaotick Jay · Plagued Mods", 14, MUTED, false);
        info.setGravity(Gravity.CENTER);
        body.addView(info);
        new AlertDialog.Builder(this)
                .setView(body)
                .setPositiveButton("Close", (dialog, which) -> dialog.dismiss())
                .show();
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        executor.shutdown();
    }
}