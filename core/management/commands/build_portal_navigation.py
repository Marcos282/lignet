from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from core.portal_navigation import replace_navigation


class Command(BaseCommand):
    help = 'Atualiza o menu estático da página inicial a partir do componente compartilhado.'

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Verifica sem modificar arquivos.')

    def handle(self, *args, **options):
        path = settings.BASE_DIR / 'index.html'
        original = path.read_text(encoding='utf-8')
        updated = replace_navigation(original, render_to_string('includes/navigation.html'))
        for kind, tag, filename, legacy in (
            ('STYLE', 'style', 'navigation.css', '<link rel="stylesheet" href="/static/lignet/navigation.css">'),
            ('SCRIPT', 'script', 'navigation.js', '<script src="/static/lignet/navigation.js" defer></script>'),
        ):
            start, end = f'<!-- SITE_NAV_{kind}_START -->', f'<!-- SITE_NAV_{kind}_END -->'
            source = (settings.BASE_DIR / 'static' / 'lignet' / filename).read_text(encoding='utf-8').strip()
            content = f'{start}\n<{tag}>\n{source}\n</{tag}>\n{end}'
            if start in updated and end in updated:
                before, remainder = updated.split(start, 1)
                _, after = remainder.split(end, 1)
                updated = before + content + after
            elif legacy in updated:
                updated = updated.replace(legacy, content)
            else:
                raise CommandError(f'Marcador do menu ausente: {kind}.')
            if kind == 'SCRIPT' and updated.index(start) < updated.index('</head>'):
                updated = updated.replace(content + '\n', '', 1)
                updated = updated.replace('</body>', content + '\n</body>', 1)
        if options['check']:
            if updated != original:
                raise CommandError('Menu estático desatualizado. Execute build_portal_navigation.')
            self.stdout.write('Menu estático sincronizado.')
        else:
            if updated != original:
                path.write_text(updated, encoding='utf-8')
            self.stdout.write(self.style.SUCCESS('Menu estático atualizado, com CSS e JavaScript incorporados.'))
