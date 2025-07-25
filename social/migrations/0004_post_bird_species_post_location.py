# Generated by Django 5.2.3 on 2025-07-23 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0003_post_postcomment_friendrequest_postlike'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='bird_species',
            field=models.CharField(choices=[('Wood Pigeon', 'Wood Pigeon'), ('House Sparrow', 'House Sparrow'), ('Starling', 'Starling'), ('Blue Tit', 'Blue Tit'), ('Blackbird', 'Blackbird'), ('Robin', 'Robin'), ('Goldfinch', 'Goldfinch'), ('Magpie', 'Magpie')], default='Wood Pigeon', max_length=25),
        ),
        migrations.AddField(
            model_name='post',
            name='location',
            field=models.CharField(choices=[('Asia', 'Asia'), ('Erean', 'Erean'), ('Brunad', 'Brunad'), ('Bylyn', 'Bylyn'), ('Docia', 'Docia'), ('Marend', 'Marend'), ('Pryn', 'Pryn'), ('Zord', 'Zord'), ('Yaean', 'Yaean'), ('Frestin', 'Frestin'), ('Stonyam', 'Stonyam'), ('Ryall', 'Ryall'), ('Ruril', 'Ruril'), ('Keivia', 'Keivia'), ('Tallan', 'Tallan'), ('Adohad', 'Adohad'), ('Obelyn', 'Obelyn'), ('Holmer', 'Holmer'), ('Vertwall', 'Vertwall')], default='Asia', max_length=25),
        ),
    ]
