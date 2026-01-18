#!/usr/bin/env python
"""Script to check hymns in database"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hymns.models import Hymn, DenominationHymn, Denomination, Verse

print("=" * 70)
print("DATABASE CHECK")
print("=" * 70)

print("\n1. HYMNS TABLE (hymns_hymn):")
print("-" * 70)
hymns = Hymn.objects.all()
print(f"Total Hymns: {hymns.count()}")
for h in hymns:
    print(f"  ID: {h.id}")
    print(f"  Title: {h.title}")
    print(f"  Category: {h.category.name if h.category else 'None'}")
    print(f"  Author: {h.author.name if h.author else 'None'}")
    print(f"  Language: {h.language}")
    print(f"  Is Premium: {h.is_premium}")
    print()

print("\n2. DENOMINATIONS TABLE (hymns_denomination):")
print("-" * 70)
denominations = Denomination.objects.all()
print(f"Total Denominations: {denominations.count()}")
for d in denominations:
    print(f"  ID: {d.id}, Name: {d.name}, Slug: {d.slug}, Active: {d.is_active}")
print()

print("\n3. DENOMINATION HYMNS TABLE (hymns_denominationhymn):")
print("-" * 70)
dhs = DenominationHymn.objects.all()
print(f"Total DenominationHymns: {dhs.count()}")
for dh in dhs:
    print(f"  ID: {dh.id}")
    print(f"  Hymn ID: {dh.hymn.id}, Title: {dh.hymn.title[:60]}...")
    print(f"  Denomination: {dh.denomination.name} (ID: {dh.denomination.id})")
    print(f"  Number: {dh.number}")
    print(f"  Period: {dh.hymn_period}")
    print(f"  Verses Count: {dh.verses.count()}")
    print()

print("\n4. CHECKING 'BEHOLD' HYMN:")
print("-" * 70)
behold_hymn = Hymn.objects.filter(title__icontains='Behold').first()
if behold_hymn:
    print(f"[OK] Found hymn: {behold_hymn.title}")
    print(f"   ID: {behold_hymn.id}")
    behold_dh = DenominationHymn.objects.filter(hymn=behold_hymn).first()
    if behold_dh:
        print(f"   DenominationHymn:")
        print(f"     Denomination: {behold_dh.denomination.name} (ID: {behold_dh.denomination.id})")
        print(f"     Number: {behold_dh.number}")
        print(f"     Period: {behold_dh.hymn_period}")
        print(f"     Verses: {behold_dh.verses.count()}")
        print()
        print("   Verses:")
        for v in behold_dh.verses.all().order_by('order', 'verse_number'):
            print(f"     {v.verse_number}. {v.text[:50]}...")
    else:
        print("   [ERROR] No DenominationHymn found for this hymn!")
else:
    print("[ERROR] No hymn with 'Behold' in title found")

print("\n5. TESTING API FILTER:")
print("-" * 70)
# Test if the hymn would be returned with the filter
catholic = Denomination.objects.filter(slug='catholic').first()
if catholic:
    print(f"Testing filter: denomination={catholic.id}, hymn_period=new")
    filtered = DenominationHymn.objects.filter(
        denomination=catholic,
        hymn_period='new'
    )
    print(f"Found {filtered.count()} DenominationHymns")
    for dh in filtered:
        print(f"  - Hymn #{dh.number}: {dh.hymn.title[:50]}...")

print("\n" + "=" * 70)

