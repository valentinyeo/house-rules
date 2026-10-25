#!/usr/bin/env python3
from pathlib import Path

home = Path.home()
links = {home / '.local/share/house-rules': Path('/var/lib/house-rules-inne/current')}
for name in ['.claude/skills', '.agents/skills', '.codex/skills', '.config/hax/skills']:
    directory = home / name
    if directory.is_dir():
        links[directory / 'house-rules'] = Path('/var/lib/house-rules-inne/current/skills/house-rules')
for link, target in links.items():
    if link.is_symlink() and link.readlink() == target:
        continue
    if link.exists() or link.is_symlink():
        raise SystemExit(f'Refusing to replace existing path: {link}')
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target, target_is_directory=True)
print('INNE_LINKS_OK')
