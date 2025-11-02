#!/bin/bash

# Configuración
APP_NAME="BackupApp"
APPDIR="${APP_NAME}.AppDir"

echo "🔧 Limpiando builds anteriores..."
rm -rf "$APPDIR" build dist
rm -f "${APP_NAME}-x86_64.AppImage"

echo "📦 Creando ejecutable compatible con Pentium..."
source venv/bin/activate

# FORZAR compatibilidad con CPUs antiguas - CRÍTICO
export CFLAGS="-march=x86-64 -mtune=generic -msse -msse2 -mno-avx -mno-avx2 -mno-avx512f"
export CXXFLAGS="-march=x86-64 -mtune=generic -msse -msse2 -mno-avx -mno-avx2 -mno-avx512f"
export LDFLAGS="-Wl,-O1 -Wl,--as-needed"

# Crear ejecutable con compatibilidad máxima
pyinstaller --onefile --windowed --name="$APP_NAME" \
  --hidden-import='PyQt6.QtCore' \
  --hidden-import='PyQt6.QtGui' \
  --hidden-import='PyQt6.QtWidgets' \
  --add-data "icon.png:." \
  --target-arch x86_64 \
  --workpath build_temp \
  --distpath dist_compat \
  backupapp.py

echo "📁 Creando estructura AppDir..."
mkdir -p "$APPDIR"/usr/bin
mkdir -p "$APPDIR"/usr/share/icons/hicolor/256x256/apps

# Copiar archivos
cp "dist_compat/$APP_NAME" "$APPDIR/usr/bin/"
cp icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/backupapp.png"

# Crear .desktop
cat > "$APPDIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=BackupApp
Comment=Application to create ZIP backups
Exec=AppRun
Icon=backupapp
Type=Application
Categories=Utility;
Terminal=false
StartupWMClass=BackupApp
X-AppImage-Name=$APP_NAME
X-AppImage-Version=1.0
EOF

# Crear AppRun
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="$HERE/usr/bin:$PATH"
export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"
# Forzar compatibilidad adicional en runtime
export QT_QUICK_BACKEND=software
cd "$HERE"
exec "./usr/bin/BackupApp"
EOF

chmod +x "$APPDIR/AppRun"

# Enlace simbólico del icono
cd "$APPDIR"
ln -s usr/share/icons/hicolor/256x256/apps/backupapp.png ./
cd ..

echo "🚀 Generando AppImage..."
appimagetool "$APPDIR" || ./linuxdeploy-x86_64.AppImage --appdir "$APPDIR" --output appimage

echo "✅ ¡AppImage compatible con multiples CPUs creado!"