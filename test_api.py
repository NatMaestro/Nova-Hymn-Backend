#!/usr/bin/env python
"""Test API endpoint to verify hymn is returned correctly"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from hymns.views import HymnViewSet
from hymns.models import Denomination

print("=" * 70)
print("TESTING API ENDPOINT")
print("=" * 70)

factory = RequestFactory()
viewset = HymnViewSet()

# Test 1: With denomination and period
print("\n1. Testing with denomination=1, hymn_period=new:")
print("-" * 70)
request = factory.get('/api/v1/hymns/?denomination=1&hymn_period=new')
# Manually set query_params for test
class MockQueryParams:
    def get(self, key, default=None):
        if key == 'denomination':
            return '1'
        elif key == 'hymn_period':
            return 'new'
        return default
request.query_params = MockQueryParams()
viewset.request = request
viewset.format_kwarg = None
queryset = viewset.get_queryset()
print(f"Queryset count: {queryset.count()}")
for hymn in queryset:
    print(f"  - Hymn ID: {hymn.id}, Title: {hymn.title[:60]}...")
    # Check denomination_hymn
    dh = hymn.denomination_hymns.filter(denomination_id=1, hymn_period='new').first()
    if dh:
        print(f"    DenominationHymn: #{dh.number}, Verses: {dh.verses.count()}")

# Test 2: With denomination only
print("\n2. Testing with denomination=1 only:")
print("-" * 70)
request = factory.get('/api/v1/hymns/?denomination=1')
class MockQueryParams2:
    def get(self, key, default=None):
        if key == 'denomination':
            return '1'
        return default
request.query_params = MockQueryParams2()
viewset.request = request
queryset = viewset.get_queryset()
print(f"Queryset count: {queryset.count()}")
for hymn in queryset:
    print(f"  - Hymn ID: {hymn.id}, Title: {hymn.title[:60]}...")

# Test 3: Without filters
print("\n3. Testing without filters (all hymns):")
print("-" * 70)
request = factory.get('/api/v1/hymns/')
class MockQueryParams3:
    def get(self, key, default=None):
        return default
request.query_params = MockQueryParams3()
viewset.request = request
queryset = viewset.get_queryset()
print(f"Queryset count: {queryset.count()}")
for hymn in queryset:
    print(f"  - Hymn ID: {hymn.id}, Title: {hymn.title[:60]}...")

# Test 4: Test serializer
print("\n4. Testing serializer output:")
print("-" * 70)
from hymns.serializers import HymnListSerializer
from hymns.models import Hymn

hymn = Hymn.objects.get(id=7)
request = factory.get('/api/v1/hymns/?denomination=1&hymn_period=new')
class MockQueryParams4:
    def get(self, key, default=None):
        if key == 'denomination':
            return '1'
        elif key == 'hymn_period':
            return 'new'
        return default
request.query_params = MockQueryParams4()
serializer = HymnListSerializer(hymn, context={'request': request})
print(f"Serialized data:")
print(f"  ID: {serializer.data.get('id')}")
print(f"  Number: {serializer.data.get('number')}")
print(f"  Title: {serializer.data.get('title')[:60]}...")
print(f"  Denomination info: {serializer.data.get('denomination_info')}")

print("\n" + "=" * 70)
print("[OK] All tests completed!")

