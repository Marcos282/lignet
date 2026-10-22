from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def editor(request):
    return render(request, 'ftth_designer/editor.html', {
        'title': 'Lignet FTTH Designer — projetista de redes ópticas',
        'description': 'Editor visual de redes FTTH balanceadas e desbalanceadas. MVP de desenho com portas individuais e projetos temporários no navegador.',
    })
