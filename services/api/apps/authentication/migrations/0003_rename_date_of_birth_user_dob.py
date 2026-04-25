from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_user_address_user_city_user_country_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='date_of_birth',
            new_name='dob',
        ),
    ]