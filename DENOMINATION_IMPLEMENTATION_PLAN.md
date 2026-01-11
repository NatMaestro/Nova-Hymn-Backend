# Denomination System Implementation Plan (UPDATED)

## 🎯 Goal
Support multiple church denominations (Catholic, Methodist, Baptist) with the ability to filter hymns by denomination. For Catholic hymns, support "New Hymns" and "Old Hymns" sub-categories.

**Key Requirements:**
1. ✅ Hymns CAN belong to multiple denominations
2. ✅ Hymn numbers are unique PER denomination (same hymn can be #1 in Catholic and #234 in Methodist)
3. ✅ No existing hymns, so no data migration needed

---

## 📋 Revised Solution

### **1. Database Structure**

#### **New Model: `Denomination`**
```python
class Denomination(models.Model):
    name = CharField(max_length=100, unique=True)  # "Catholic", "Methodist", "Baptist"
    slug = SlugField(max_length=100, unique=True, blank=True)
    description = TextField(blank=True, null=True)
    is_active = BooleanField(default=True)
    display_order = IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'name']
```

#### **New Through Model: `DenominationHymn`**
```python
class DenominationHymn(models.Model):
    """Junction table linking hymns to denominations with denomination-specific data"""
    hymn = ForeignKey(Hymn, on_delete=CASCADE, related_name='denomination_hymns')
    denomination = ForeignKey(Denomination, on_delete=CASCADE, related_name='hymns')
    number = IntegerField(validators=[MinValueValidator(1)])  # Hymn number in THIS denomination/period
    hymn_period = CharField(
        max_length=10, 
        choices=[('new', 'New'), ('old', 'Old')], 
        null=True, 
        blank=True,
        help_text="Required for Catholic hymns. Old and New have separate numbering sequences."
    )
    
    class Meta:
        # For Catholic: (denomination, hymn_period, number) must be unique
        # For others: (denomination, number) must be unique (hymn_period is null)
        unique_together = [('denomination', 'hymn_period', 'number')]
        ordering = ['denomination', 'hymn_period', 'number']
        indexes = [
            models.Index(fields=['denomination', 'hymn_period', 'number']),
        ]
    
    def clean(self):
        """Validate that Catholic hymns must have hymn_period"""
        if self.denomination and self.denomination.slug == 'catholic':
            if not self.hymn_period:
                raise ValidationError("Catholic hymns must specify hymn_period (new or old)")
        elif self.hymn_period:
            raise ValidationError("hymn_period can only be set for Catholic hymns")
```

#### **Hymn Model Changes**
```python
class Hymn(models.Model):
    # REMOVE: number = models.IntegerField(unique=True)  # Remove this!
    # ... existing fields (title, author, category, etc.) ...
    # Note: title, author, category are shared across denominations
    # But lyrics (verses) are denomination-specific!
    
    # NEW FIELD:
    denominations = ManyToManyField(
        Denomination, 
        through='DenominationHymn',
        related_name='hymn_set',
        blank=True
    )
    # Note: hymn_period is stored in DenominationHymn, not Hymn
```

#### **Verse Model Changes - IMPORTANT!**
```python
class Verse(models.Model):
    """Verse model - lyrics are denomination-specific!"""
    # CHANGE: Link to DenominationHymn instead of Hymn directly
    denomination_hymn = models.ForeignKey(
        'DenominationHymn', 
        on_delete=models.CASCADE, 
        related_name='verses'
    )
    verse_number = models.IntegerField(validators=[MinValueValidator(1)])
    is_chorus = models.BooleanField(default=False)
    text = models.TextField()  # Lyrics can vary: "You" vs "Thou", etc.
    order = models.IntegerField(default=0, help_text="Order of verse in hymn")
    
    class Meta:
        ordering = ['order', 'verse_number']
        # Unique per denomination/period combination
        unique_together = ['denomination_hymn', 'verse_number', 'is_chorus']
    
    @property
    def hymn(self):
        """Convenience property to access the hymn"""
        return self.denomination_hymn.hymn
    
    def __str__(self):
        verse_type = "Chorus" if self.is_chorus else f"Verse {self.verse_number}"
        return f"{self.denomination_hymn.hymn.title} ({self.denomination_hymn.denomination.name}) - {verse_type}"
```

**Why this change?**
- ✅ Lyrics can vary by denomination ("You" vs "Thou")
- ✅ Same hymn can have different verses in different denominations
- ✅ Catholic Old and New can have different lyrics
- ✅ Each DenominationHymn has its own set of verses

**Why this approach?**
- ✅ ManyToMany: Hymns can belong to multiple denominations
- ✅ Per-denomination numbering: Number stored in junction table
- ✅ Unique constraint: (denomination, number) ensures uniqueness per denomination
- ✅ Flexible: Same hymn can have different numbers in different denominations
- ✅ Catholic periods: `hymn_period` only applies when denomination is Catholic

---

### **2. Data Structure Example**

**IMPORTANT: Catholic Old and New Hymns have SEPARATE numbering sequences!**

```
Hymn: "Amazing Grace" (id: 1)
├── In Catholic Old (number: 1, hymn_period: "old")
├── In Catholic New (number: 546, hymn_period: "new")  ← Same hymn, different number!
├── In Methodist (number: 234, hymn_period: null)
└── In Baptist (number: 45, hymn_period: null)

Hymn: "How Great Thou Art" (id: 2)
├── In Catholic Old (number: 2, hymn_period: "old")
├── In Catholic New (number: 1, hymn_period: "new")  ← Different number in New
└── In Methodist (number: 1, hymn_period: null)
```

**Database Tables:**
```
hymns_hymn:
  id | title
  1  | Amazing Grace
  2  | How Great Thou Art

hymns_denomination:
  id | name      | slug
  1  | Catholic  | catholic
  2  | Methodist | methodist
  3  | Baptist   | baptist

hymns_denominationhymn:
  id | hymn_id | denomination_id | number | hymn_period
  1  | 1       | 1               | 1      | old        ← Catholic Old #1
  2  | 1       | 1               | 546    | new        ← Catholic New #546 (same hymn!)
  3  | 1       | 2               | 234    | null       ← Methodist #234
  4  | 1       | 3               | 45     | null       ← Baptist #45
  5  | 2       | 1               | 2      | old        ← Catholic Old #2
  6  | 2       | 1               | 1      | new        ← Catholic New #1
  7  | 2       | 2               | 1      | null       ← Methodist #1

hymns_verse:
  id | denomination_hymn_id | verse_number | text                    | is_chorus
  1  | 1 (Catholic Old #1)  | 1           | "You are my God..."     | false
  2  | 1 (Catholic Old #1)  | 2           | "You are my strength..."| false
  3  | 3 (Methodist #234)    | 1           | "Thou art my God..."    | false  ← Different lyrics!
  4  | 3 (Methodist #234)    | 2           | "Thou art my strength..."| false ← Different lyrics!
  5  | 2 (Catholic New #546)| 1           | "You are my God..."     | false  ← May differ from Old
```

**Note:** Verses are linked to `DenominationHymn`, not directly to `Hymn`. This allows:
- Different lyrics per denomination ("You" vs "Thou")
- Different lyrics between Catholic Old and New
- Each denomination/period combination has its own verse set

**Key Points:**
- Catholic Old Hymns: Numbers 1, 2, 3... (separate sequence)
- Catholic New Hymns: Numbers 1, 2, 3... (separate sequence)
- Same hymn can be #1 in Old and #546 in New
- Unique constraint: `(denomination, hymn_period, number)` ensures no duplicates within each period
- **Lyrics are denomination-specific!** Each DenominationHymn has its own verses
- Same hymn can have different lyrics: "You are my God" (Catholic) vs "Thou art my God" (Methodist)

---

### **3. Backend API Changes**

#### **New Endpoints:**
```
GET /api/v1/denominations/                    # List all denominations
GET /api/v1/denominations/{id}/               # Get specific denomination
GET /api/v1/denominations/{id}/hymns/         # Get hymns for a denomination
```

#### **Updated Hymn Endpoints:**
```
GET /api/v1/hymns/?denomination=1                    # Filter by denomination ID (all Catholic hymns)
GET /api/v1/hymns/?denomination=catholic             # Filter by denomination slug (all Catholic hymns)
GET /api/v1/hymns/?denomination=1&hymn_period=new    # Catholic NEW hymns only (numbers 1, 2, 3...)
GET /api/v1/hymns/?denomination=1&hymn_period=old    # Catholic OLD hymns only (numbers 1, 2, 3...)
GET /api/v1/hymns/?denomination=2                    # Methodist hymns (numbers 1, 2, 3...)
GET /api/v1/hymns/?denomination=3                    # Baptist hymns (numbers 1, 2, 3...)
```

**Note:** When filtering Catholic hymns by period, the numbering sequence is separate:
- Catholic Old: #1, #2, #3... (one sequence)
- Catholic New: #1, #2, #3... (different sequence)
- Same hymn can appear in both with different numbers!

#### **Response Structure:**

**When filtering by Catholic Old:**
```json
{
  "id": 1,
  "title": "Amazing Grace",
  "number": 1,  // Catholic Old number
  "denomination_name": "Catholic",
  "hymn_period": "old",
  // ... other fields
}
```

**When filtering by Catholic New:**
```json
{
  "id": 1,
  "title": "Amazing Grace",
  "number": 546,  // Catholic New number (different from Old!)
  "denomination_name": "Catholic",
  "hymn_period": "new",
  // ... other fields
}
```

**When viewing hymn detail (all denominations):**
```json
{
  "id": 1,
  "title": "Amazing Grace",
  "denominations": [
    {
      "id": 1,
      "name": "Catholic",
      "slug": "catholic",
      "number": 1,
      "hymn_period": "old",
      "verses": [
        {"verse_number": 1, "text": "You are my God...", "is_chorus": false},
        {"verse_number": 2, "text": "You are my strength...", "is_chorus": false}
      ]
    },
    {
      "id": 1,
      "name": "Catholic",
      "slug": "catholic",
      "number": 546,
      "hymn_period": "new",  // Same hymn, different number in New!
      "verses": [
        {"verse_number": 1, "text": "You are my God...", "is_chorus": false}  // May differ from Old
      ]
    },
    {
      "id": 2,
      "name": "Methodist",
      "slug": "methodist",
      "number": 234,
      "hymn_period": null,
      "verses": [
        {"verse_number": 1, "text": "Thou art my God...", "is_chorus": false},  // Different lyrics!
        {"verse_number": 2, "text": "Thou art my strength...", "is_chorus": false}
      ]
    }
  ],
  // ... other fields
}
```

**Note:** Each denomination entry includes its own verses with potentially different lyrics!

---

### **4. Frontend Changes**

#### **New UI Components:**
1. **Denomination Selector** (similar to category selector)
   - Tabs or dropdown: "All", "Catholic", "Methodist", "Baptist"
   - For Catholic: Sub-selector "All", "New Hymns", "Old Hymns"

2. **Hymn Display**
   - Show hymn number based on selected denomination
   - Show denomination badge(s) on hymn card
   - Show "New" or "Old" badge for Catholic hymns

#### **Updated Screens:**
- **Home Screen**: Add denomination filter
- **All Hymns Screen**: Add denomination tabs/filter
- **Hymn Detail**: Show all denominations this hymn belongs to, with their numbers

#### **Filter Flow:**
```
User selects "Catholic" 
  → API call: /api/v1/hymns/?denomination=catholic
  → Shows all Catholic hymns with Catholic numbers (1, 2, 3...)

User selects "Catholic" → "New Hymns"
  → API call: /api/v1/hymns/?denomination=catholic&hymn_period=new
  → Shows only Catholic new hymns

User selects "Methodist"
  → API call: /api/v1/hymns/?denomination=methodist
  → Shows all Methodist hymns with Methodist numbers (1, 234, 45...)
```

---

### **5. Admin Interface Changes**

#### **Django Admin:**
- **DenominationAdmin**: Manage denominations
- **DenominationHymnInline**: Inline in HymnAdmin to add/edit denomination associations
- **HymnAdmin Updates**:
  - Remove `number` field from main form
  - Add `DenominationHymnInline` to manage denominations and numbers
  - Show all denominations a hymn belongs to

#### **Bulk Upload Enhancement:**
- Add denomination selection to bulk upload form
- Specify hymn number for the selected denomination
- For Catholic: Specify hymn_period (new/old)

---

### **6. Migration Strategy**

Since there are **no existing hymns**, migration is straightforward:

#### **Step 1: Create Denomination Model**
- New migration creates `hymns_denomination` table
- Seed initial data: Catholic, Methodist, Baptist

#### **Step 2: Create DenominationHymn Model**
- New migration creates `hymns_denominationhymn` table
- Sets up ManyToMany relationship

#### **Step 3: Update Hymn Model**
- Migration removes `number` field (or makes it nullable/legacy)
- Migration adds `denominations` ManyToMany field
- Update indexes and constraints

#### **Step 4: Update Verse Model**
- Migration changes `hymn` ForeignKey to `denomination_hymn` ForeignKey
- This is a breaking change - verses now belong to DenominationHymn, not Hymn directly
- Update unique_together constraint

#### **Step 5: Update Existing Code**
- Update serializers to handle new structure (verses from DenominationHymn)
- Update views to filter by denomination and return correct verses
- Update admin interface (VerseInline now shows per DenominationHymn)

---

### **7. Implementation Steps**

1. ✅ **Create Denomination Model** (models.py)
2. ✅ **Create DenominationHymn Through Model** (models.py)
3. ✅ **Update Hymn Model** (remove number, add ManyToMany)
4. ✅ **Update Verse Model** (link to DenominationHymn instead of Hymn)
5. ✅ **Create Migrations** (makemigrations)
6. ✅ **Seed Initial Denominations** (data migration)
7. ✅ **Update Serializers** (include denomination data, verses from DenominationHymn)
8. ✅ **Update Views** (add filtering by denomination, return correct verses)
9. ✅ **Update Admin** (add inline for DenominationHymn, VerseInline per DenominationHymn)
10. ✅ **Update API Documentation** (Swagger)
11. ✅ **Frontend Integration** (add denomination selector)

---

### **8. Query Examples**

```python
# Get all Catholic hymns (both Old and New)
Hymn.objects.filter(denomination_hymns__denomination__slug='catholic')

# Get Catholic NEW hymns only (separate numbering: 1, 2, 3...)
Hymn.objects.filter(
    denomination_hymns__denomination__slug='catholic',
    denomination_hymns__hymn_period='new'
).order_by('denomination_hymns__number')

# Get Catholic OLD hymns only (separate numbering: 1, 2, 3...)
Hymn.objects.filter(
    denomination_hymns__denomination__slug='catholic',
    denomination_hymns__hymn_period='old'
).order_by('denomination_hymns__number')

# Get a hymn with all its denomination/period numbers
hymn = Hymn.objects.get(id=1)
hymn.denomination_hymns.all()  # All DenominationHymn objects
# Catholic Old number
hymn.denomination_hymns.filter(denomination__slug='catholic', hymn_period='old').first().number
# Catholic New number (may be different!)
hymn.denomination_hymns.filter(denomination__slug='catholic', hymn_period='new').first().number

# Get hymns that belong to multiple denominations
Hymn.objects.filter(denomination_hymns__denomination__slug__in=['catholic', 'methodist'])

# Get hymn with specific number in Catholic Old
Hymn.objects.filter(
    denomination_hymns__denomination__slug='catholic',
    denomination_hymns__hymn_period='old',
    denomination_hymns__number=1
)

# Get hymn with specific number in Catholic New (different from Old!)
Hymn.objects.filter(
    denomination_hymns__denomination__slug='catholic',
    denomination_hymns__hymn_period='new',
    denomination_hymns__number=546
)
```

---

### **9. Benefits of This Approach**

✅ **Multi-denomination**: Hymns can belong to multiple denominations
✅ **Per-denomination numbering**: Same hymn, different numbers per denomination
✅ **Flexible**: Easy to add more denominations
✅ **Clean**: Clear separation of concerns
✅ **Query-friendly**: Efficient database queries
✅ **User-friendly**: Clear filtering in UI
✅ **Scalable**: Can extend with more fields in DenominationHymn if needed

---

### **10. Important Considerations**

#### **Hymn Number Display:**
- When viewing hymns, show the number for the **selected denomination**
- In hymn detail, show all denominations and their numbers
- API should return the relevant number based on filter

#### **Lyrics (Verses) Display:**
- **CRITICAL:** Verses are denomination-specific!
- When viewing a hymn filtered by denomination, show verses for THAT denomination
- Same hymn can have completely different lyrics in different denominations
- Catholic Old and New can have different lyrics
- API must return verses from the correct DenominationHymn

#### **Search & Filtering:**
- Search should work across all denominations
- Filtering by denomination should show correct numbers AND correct lyrics
- Sorting should use the denomination-specific number
- Search results should indicate which denomination version is shown

#### **Bulk Operations:**
- When uploading hymns, specify denomination and number
- **Must specify which denomination's lyrics to upload**
- Can upload same hymn to multiple denominations with different lyrics
- Validate number uniqueness per denomination
- Each denomination upload creates separate verse entries

---

## 🚀 Ready to Implement?

This revised plan addresses:
- ✅ Multi-denomination support (ManyToMany)
- ✅ Per-denomination hymn numbering
- ✅ Catholic new/old hymn periods
- ✅ Clean database structure
- ✅ Simple API filtering
- ✅ Easy frontend integration

**Proceeding with implementation!**
