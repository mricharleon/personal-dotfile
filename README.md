# Personal dotfile
Una pequeña personalización de algunos archivos con
funcionalidades geniales ;)

- **Tmux** (.tmux.conf)

    ![Tmux](https://cloud.githubusercontent.com/assets/2581366/26532575/8fbac784-43c9-11e7-8950-00ce5360c5fc.png)

- **Vim** (.vimrc)

    - Instalar xclip (Compatibilidad con el ratón para copiar y pegar al
      clipboard es mucho mas eficiente. -Para mi)
    - Instalar ctags (Dependencia para plugin tagbar)
    - Instalar cmake (Dependecia para poder compilar el plugin autocomplete)

  ![Tmux](https://cloud.githubusercontent.com/assets/2581366/26562304/b91ab834-448a-11e7-964c-40d9f422e681.png)

- **Opencode** (`opencode/`)

## Sincronización de configuración Opencode

Para mantener el repositorio sincronizado con la configuración local de opencode:

```bash
# 1. Copiar archivos locales al repositorio
cp ~/.config/opencode/opencode.json opencode/opencode.json
cp ~/.config/opencode/AGENTS.md opencode/AGENTS.md
cp ~/.config/opencode/*.jsonc opencode/
cp ~/.config/opencode/*.json opencode/

# 2. Copiar plugins locales
cp ~/.config/opencode/plugins/*.js opencode/plugins/

# 3. Eliminar archivos del repositorio que no existen en local
# (revisar con git status)

# 4. Commit y push
git add -A
git commit -m "sync: actualizar opencode con configuración local"
git push
```

**Archivos a revisar manualmente:**
- `opencode/opencode.json` - configuración principal
- `opencode/AGENTS.md` - instrucciones del agente
- `opencode/plugins/` - plugins instalados localmente
- `opencode/skills/` - skills instaladas localmente
