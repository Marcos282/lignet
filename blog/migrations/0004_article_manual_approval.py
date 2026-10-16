from django.db import migrations, models


def separate_editorial_flows(apps, schema_editor):
    Article = apps.get_model("blog", "Article")
    Article.objects.using(schema_editor.connection.alias).filter(generated=True).update(manual_approval=False)


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0003_article_image_job_article_image_model_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="manual_approval",
            field=models.BooleanField(
                default=True, verbose_name="Exigir minha aprovação manual",
                help_text="Marcado: o Cron não aprova este artigo. Artigos novos do painel usam esta opção por padrão."),
        ),
        migrations.RunPython(separate_editorial_flows, migrations.RunPython.noop),
    ]
