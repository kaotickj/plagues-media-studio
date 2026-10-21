#!/usr/bin/env bash
set -euo pipefail
install -Dm755 dist/PlaguesMediaStudio/PlaguesMediaStudio "$DESTDIR/usr/bin/plagues-media-studio"
cp -a dist/PlaguesMediaStudio/_internal "$DESTDIR/usr/bin/_internal"
mkdir -p "$DESTDIR/usr/share/applications"
cat > "$DESTDIR/usr/share/applications/plagues-media-studio.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Plague's Media Studio
Exec=plagues-media-studio
Terminal=false
Categories=AudioVideo;Video;Audio;
EOF
