"""
Management command to seed media files (sheet music and audio).
Usage: python manage.py seed_media --hymn-id <hymn_id> --type <sheet_music|audio>
"""
from django.core.management.base import BaseCommand
from hymns.models import Hymn, SheetMusic, AudioFile
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Seed media files for hymns (sheet music and audio)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hymn-id',
            type=int,
            help='Hymn ID to add media for',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['sheet_music', 'audio'],
            help='Type of media to add',
        )
        parser.add_argument(
            '--audio-type',
            type=str,
            choices=['piano', 'soprano', 'alto', 'tenor', 'bass', 'full'],
            help='Audio type (required if type is audio)',
        )
        parser.add_argument(
            '--file-path',
            type=str,
            required=True,
            help='Path to the media file',
        )
        parser.add_argument(
            '--thumbnail-path',
            type=str,
            help='Path to thumbnail (for sheet music)',
        )

    def handle(self, *args, **options):
        hymn_id = options.get('hymn_id')
        media_type = options.get('type')
        file_path = options.get('file_path')
        thumbnail_path = options.get('thumbnail_path')
        audio_type = options.get('audio_type')

        if not hymn_id:
            self.stdout.write(self.style.ERROR('--hymn-id is required'))
            return

        try:
            hymn = Hymn.objects.get(id=hymn_id)
        except Hymn.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Hymn with ID {hymn_id} does not exist'))
            return

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        if media_type == 'sheet_music':
            self._add_sheet_music(hymn, file_path, thumbnail_path)
        elif media_type == 'audio':
            if not audio_type:
                self.stdout.write(self.style.ERROR('--audio-type is required for audio files'))
                return
            self._add_audio(hymn, file_path, audio_type)
        else:
            self.stdout.write(self.style.ERROR('Invalid media type. Use --type sheet_music or --type audio'))

    def _add_sheet_music(self, hymn, file_path, thumbnail_path=None):
        """Add sheet music for a hymn"""
        from django.core.files import File
        
        sheet_music, created = SheetMusic.objects.get_or_create(
            hymn=hymn,
            defaults={'is_premium': True}
        )

        with open(file_path, 'rb') as f:
            sheet_music.file.save(
                os.path.basename(file_path),
                File(f),
                save=True
            )

        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'rb') as f:
                sheet_music.thumbnail.save(
                    os.path.basename(thumbnail_path),
                    File(f),
                    save=True
                )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created sheet music for hymn {hymn.number}: {hymn.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated sheet music for hymn {hymn.number}: {hymn.title}'))

    def _add_audio(self, hymn, file_path, audio_type):
        """Add audio file for a hymn"""
        from django.core.files import File
        
        audio_file, created = AudioFile.objects.get_or_create(
            hymn=hymn,
            audio_type=audio_type,
            defaults={'is_premium': True}
        )

        with open(file_path, 'rb') as f:
            audio_file.file.save(
                os.path.basename(file_path),
                File(f),
                save=True
            )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Created {audio_type} audio for hymn {hymn.number}: {hymn.title}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Updated {audio_type} audio for hymn {hymn.number}: {hymn.title}'
            ))

