"""
Management command to seed the database with sample hymn data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from hymns.models import Category, Author, Hymn, Verse, SheetMusic, AudioFile
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Seed the database with sample hymn data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Hymn.objects.all().delete()
            Category.objects.all().delete()
            Author.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        self.stdout.write(self.style.SUCCESS('Starting to seed data...'))

        # Create Categories
        categories_data = [
            {'name': 'Worship', 'description': 'Hymns of worship and adoration'},
            {'name': 'Praise', 'description': 'Hymns of praise and celebration'},
            {'name': 'Thanksgiving', 'description': 'Hymns of gratitude and thanksgiving'},
            {'name': 'Grace', 'description': 'Hymns about God\'s grace'},
            {'name': 'Peace', 'description': 'Hymns of peace and comfort'},
            {'name': 'Easter', 'description': 'Easter hymns'},
            {'name': 'Christmas', 'description': 'Christmas hymns'},
            {'name': 'Lent', 'description': 'Lenten hymns'},
            {'name': 'Advent', 'description': 'Advent hymns'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))

        # Create Authors
        authors_data = [
            {'name': 'John Newton', 'biography': 'English Anglican clergyman and hymn writer', 'birth_year': 1725, 'death_year': 1807},
            {'name': 'Carl Boberg', 'biography': 'Swedish pastor and hymn writer', 'birth_year': 1859, 'death_year': 1940},
            {'name': 'Fanny J. Crosby', 'biography': 'American mission worker and hymn writer', 'birth_year': 1820, 'death_year': 1915},
            {'name': 'Thomas Chisholm', 'biography': 'American Methodist minister and hymn writer', 'birth_year': 1866, 'death_year': 1960},
            {'name': 'Horatio Spafford', 'biography': 'American lawyer and hymn writer', 'birth_year': 1828, 'death_year': 1888},
        ]

        authors = {}
        for author_data in authors_data:
            author, created = Author.objects.get_or_create(
                name=author_data['name'],
                defaults={
                    'biography': author_data['biography'],
                    'birth_year': author_data['birth_year'],
                    'death_year': author_data['death_year']
                }
            )
            authors[author_data['name']] = author
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created author: {author.name}'))

        # Sample Hymns Data
        hymns_data = [
            {
                'number': 101,
                'title': 'Amazing Grace',
                'author': 'John Newton',
                'category': 'Grace',
                'language': 'English',
                'scripture_references': ['Ephesians 2:8-9', '2 Corinthians 12:9'],
                'history': 'Written by John Newton in 1779. Newton was a former slave trader who experienced a spiritual conversion and became an abolitionist.',
                'meter': '8.6.8.6',
                'key_signature': 'G Major',
                'time_signature': '3/4',
                'is_premium': False,
                'verses': [
                    {'verse_number': 1, 'is_chorus': False, 'text': 'Amazing grace! How sweet the sound, that saved a wretch like me. I once was lost but now I\'m found, was blind but now I see.', 'order': 1},
                    {'verse_number': 2, 'is_chorus': False, 'text': 'T\'was grace that taught my heart to fear, and grace my fears relieved. How precious did that grace appear the hour I first believed.', 'order': 2},
                    {'verse_number': 3, 'is_chorus': False, 'text': 'Through many dangers, toils and snares, I have already come. \'Tis grace hath brought me safe thus far, and grace will lead me home.', 'order': 3},
                    {'verse_number': 4, 'is_chorus': False, 'text': 'When we\'ve been there ten thousand years, bright shining as the sun. We\'ve no less days to sing God\'s praise than when we\'ve first begun.', 'order': 4},
                ]
            },
            {
                'number': 102,
                'title': 'How Great Thou Art',
                'author': 'Carl Boberg',
                'category': 'Praise',
                'language': 'English',
                'scripture_references': ['Psalm 145:3', 'Romans 8:18'],
                'history': 'Originally a Swedish poem written by Carl Boberg in 1885. It was translated to English by Stuart Hine in 1949.',
                'meter': '11.10.11.10',
                'key_signature': 'Bb Major',
                'time_signature': '4/4',
                'is_premium': False,
                'verses': [
                    {'verse_number': 1, 'is_chorus': False, 'text': 'O Lord my God! When I in awesome wonder consider all the works Thy hands have made. I see the stars, I hear the rolling thunder, Thy power throughout the universe displayed.', 'order': 1},
                    {'verse_number': 2, 'is_chorus': True, 'text': 'Then sings my soul, my Savior God to Thee: How great Thou art! How great Thou art! Then sings my soul, my Savior God to Thee: How great Thou art! How great Thou art!', 'order': 2},
                    {'verse_number': 3, 'is_chorus': False, 'text': 'When through the woods and forest glades I wander and hear the birds sing sweetly in the trees. When I look down from lofty mountain grandeur and hear the brook and feel the gentle breeze.', 'order': 3},
                ]
            },
            {
                'number': 103,
                'title': 'Blessed Assurance',
                'author': 'Fanny J. Crosby',
                'category': 'Thanksgiving',
                'language': 'English',
                'scripture_references': ['Hebrews 10:22', '1 John 5:13'],
                'history': 'Written by Fanny Crosby in 1873. Crosby wrote over 8,000 hymns despite being blind from infancy.',
                'meter': '9.10.9.9',
                'key_signature': 'F Major',
                'time_signature': '4/4',
                'is_premium': False,
                'verses': [
                    {'verse_number': 1, 'is_chorus': False, 'text': 'Blessed assurance, Jesus is mine! Oh, what a foretaste of glory divine! Heir of salvation, purchase of God, born of His Spirit, washed in His blood.', 'order': 1},
                    {'verse_number': 2, 'is_chorus': True, 'text': 'This is my story, this is my song, praising my Savior all the day long. This is my story, this is my song, praising my Savior all the day long.', 'order': 2},
                    {'verse_number': 3, 'is_chorus': False, 'text': 'Perfect submission, perfect delight, visions of rapture now burst on my sight. Angels descending bring from above echoes of mercy, whispers of love.', 'order': 3},
                ]
            },
            {
                'number': 104,
                'title': 'Great Is Thy Faithfulness',
                'author': 'Thomas Chisholm',
                'category': 'Worship',
                'language': 'English',
                'scripture_references': ['Lamentations 3:22-23', 'James 1:17'],
                'history': 'Written by Thomas Chisholm in 1923. The hymn is based on Lamentations 3:22-23 and emphasizes God\'s unchanging faithfulness.',
                'meter': '11.10.11.10',
                'key_signature': 'Eb Major',
                'time_signature': '3/4',
                'is_premium': False,
                'verses': [
                    {'verse_number': 1, 'is_chorus': False, 'text': 'Great is Thy faithfulness, O God my Father. There is no shadow of turning with Thee. Thou changest not, Thy compassions they fail not. As Thou hast been, Thou forever wilt be.', 'order': 1},
                    {'verse_number': 2, 'is_chorus': True, 'text': 'Great is Thy faithfulness! Great is Thy faithfulness! Morning by morning new mercies I see. All I have needed Thy hand hath provided. Great is Thy faithfulness, Lord, unto me!', 'order': 2},
                    {'verse_number': 3, 'is_chorus': False, 'text': 'Summer and winter and springtime and harvest, sun, moon, and stars in their courses above join with all nature in manifold witness to Thy great faithfulness, mercy, and love.', 'order': 3},
                ]
            },
            {
                'number': 105,
                'title': 'It Is Well With My Soul',
                'author': 'Horatio Spafford',
                'category': 'Peace',
                'language': 'English',
                'scripture_references': ['2 Kings 4:26', 'Philippians 4:7'],
                'history': 'Written by Horatio Spafford in 1873 after he lost his four daughters in a shipwreck. Despite this tragedy, he wrote this hymn expressing his faith and trust in God.',
                'meter': '11.8.11.9',
                'key_signature': 'Eb Major',
                'time_signature': '4/4',
                'is_premium': False,
                'verses': [
                    {'verse_number': 1, 'is_chorus': False, 'text': 'When peace like a river, attendeth my way, when sorrows like sea billows roll. Whatever my lot, Thou hast taught me to say: It is well, it is well with my soul.', 'order': 1},
                    {'verse_number': 2, 'is_chorus': True, 'text': 'It is well with my soul, it is well, it is well with my soul.', 'order': 2},
                    {'verse_number': 3, 'is_chorus': False, 'text': 'Though Satan should buffet, though trials should come, let this blest assurance control: that Christ has regarded my helpless estate and hath shed His own blood for my soul.', 'order': 3},
                ]
            },
        ]

        # Create Hymns
        for hymn_data in hymns_data:
            verses_data = hymn_data.pop('verses')
            author_name = hymn_data.pop('author')
            category_name = hymn_data.pop('category')
            
            hymn, created = Hymn.objects.get_or_create(
                number=hymn_data['number'],
                defaults={
                    **hymn_data,
                    'author': authors.get(author_name),
                    'category': categories.get(category_name),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created hymn: {hymn.number}. {hymn.title}'))
                
                # Create Verses
                for verse_data in verses_data:
                    Verse.objects.create(hymn=hymn, **verse_data)
                    self.stdout.write(self.style.SUCCESS(f'  - Created verse {verse_data["verse_number"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Hymn {hymn.number} already exists, skipping...'))

        self.stdout.write(self.style.SUCCESS('\nData seeding completed!'))
        self.stdout.write(self.style.SUCCESS(f'Created {Category.objects.count()} categories'))
        self.stdout.write(self.style.SUCCESS(f'Created {Author.objects.count()} authors'))
        self.stdout.write(self.style.SUCCESS(f'Created {Hymn.objects.count()} hymns'))
        self.stdout.write(self.style.SUCCESS(f'Created {Verse.objects.count()} verses'))

