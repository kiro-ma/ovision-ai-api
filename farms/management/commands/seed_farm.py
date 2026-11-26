from django.core.management.base import BaseCommand

from farms.models import Farm


class Command(BaseCommand):
    help = "Cria ou atualiza uma fazenda/usuário padrão para testes locais da API Ovision."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@ovision.local", help="E-mail de login da fazenda")
        parser.add_argument("--password", default="ovision123", help="Senha de acesso")
        parser.add_argument("--name", default="Fazenda Ovision Demo", help="Nome da fazenda/criação")
        parser.add_argument("--owner-name", default="Produtor Demo", help="Nome do responsável")
        parser.add_argument("--species-focus", default="caprinos", help="Espécie principal")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]

        farm, created = Farm.objects.get_or_create(
            email=email,
            defaults={
                "name": options["name"],
                "owner_name": options["owner_name"],
                "species_focus": options["species_focus"],
            },
        )
        farm.name = options["name"]
        farm.owner_name = options["owner_name"]
        farm.species_focus = options["species_focus"]
        farm.set_password(password)
        farm.save()

        acao = "criada" if created else "atualizada"
        self.stdout.write(
            self.style.SUCCESS(
                f"Fazenda {acao} com sucesso: id={farm.id} | email={farm.email} | senha={password}"
            )
        )
