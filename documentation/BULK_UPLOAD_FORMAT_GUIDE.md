# Bulk Upload Document Format Guide

## 📋 Overview

The system **automatically extracts and arranges** the data from your documents, but you need to follow a **specific format** for best results.

---

## ✅ **Recommended Format**

### **Format 1: With Hymn Number (Recommended)**

```
101. Amazing Grace

1. Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost, but now am found
Was blind, but now I see

2. 'Twas grace that taught my heart to fear
And grace my fears relieved
How precious did that grace appear
The hour I first believed

Chorus: Amazing grace, how sweet the sound
That saved a wretch like me

3. Through many dangers, toils and snares
I have already come
'Tis grace hath brought me safe thus far
And grace will lead me home
```

### **Format 2: Without Hymn Number**

```
Amazing Grace

1. Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost, but now am found
Was blind, but now I see

2. 'Twas grace that taught my heart to fear
And grace my fears relieved
How precious did that grace appear
The hour I first believed
```

---

## 📝 **Format Rules**

### **1. Title (First Line/Paragraph)**
- **With number**: `101. Amazing Grace` or `1. Amazing Grace`
- **Without number**: `Amazing Grace` (number will be auto-assigned)
- Must be the **first non-empty line/paragraph**

### **2. Verses**
- **Must be numbered**: `1.`, `2.`, `3.`, etc.
- **Multi-line verses**: Lines after the verse number are part of that verse
- **Empty lines**: Separate verses (optional, but helpful)

**Example:**
```
1. First line of verse one
Second line of verse one
Third line of verse one

2. First line of verse two
Second line of verse two
```

### **3. Choruses/Refrains**
- **Mark with**: `Chorus:` or `Refrain:` (case-insensitive)
- Can have `:` or not: `Chorus:` or `Chorus` both work
- **Multi-line choruses**: Lines after "Chorus:" are part of the chorus

**Examples:**
```
Chorus: Amazing grace, how sweet the sound
That saved a wretch like me

Refrain: Hallelujah, praise the Lord
```

### **4. Verse Order**
- Verses are ordered by their verse number
- Choruses are placed after all verses (order = verse_number + 100)
- If you want a chorus between verses, number it appropriately

---

## 🔍 **How the System Extracts Data**

### **Step 1: Title Extraction**
- Looks for pattern: `NUMBER. TITLE` (e.g., "101. Amazing Grace")
- If found: extracts number and title
- If not found: uses first line as title only

### **Step 2: Verse Detection**
- Detects lines starting with numbers: `1.`, `2.`, `3.`, etc.
- Removes the number prefix and extracts the text
- Continues reading lines until next verse number or chorus

### **Step 3: Chorus Detection**
- Detects lines starting with: `Chorus:` or `Refrain:`
- Marks as chorus (not regular verse)
- Extracts text after "Chorus:" or "Refrain:"

### **Step 4: Multi-line Handling**
- Lines after a verse number are appended to that verse
- Empty lines separate verses (but not required)
- Continues until next verse number or chorus marker

---

## 📄 **File Format Examples**

### **Word Document (.docx, .doc)**

**Structure:**
```
101. Amazing Grace

1. Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost, but now am found
Was blind, but now I see

2. 'Twas grace that taught my heart to fear
And grace my fears relieved
How precious did that grace appear
The hour I first believed

Chorus: Amazing grace, how sweet the sound
That saved a wretch like me

3. Through many dangers, toils and snares
I have already come
'Tis grace hath brought me safe thus far
And grace will lead me home
```

**Notes:**
- Each paragraph becomes a line
- Empty paragraphs are ignored
- Formatting (bold, italic) is ignored (only text is extracted)

### **Text File (.txt)**

**Structure:**
```
101. Amazing Grace

1. Amazing grace, how sweet the sound
That saved a wretch like me
I once was lost, but now am found
Was blind, but now I see

2. 'Twas grace that taught my heart to fear
And grace my fears relieved
How precious did that grace appear
The hour I first believed

Chorus: Amazing grace, how sweet the sound
That saved a wretch like me

3. Through many dangers, toils and snares
I have already come
'Tis grace hath brought me safe thus far
And grace will lead me home
```

**Notes:**
- Each line is processed separately
- Empty lines are ignored
- Line breaks within verses are preserved

---

## ⚠️ **Important Notes**

### **1. Hymn Number in File**
- The hymn number in the file is **extracted but not used**
- The system uses the "Starting Hymn Number" from the upload form
- Or auto-increments from the last number for that denomination/period

### **2. Verse Numbering**
- Verses **must** be numbered: `1.`, `2.`, `3.`, etc.
- If verses aren't numbered, they'll be auto-numbered sequentially
- But it's better to number them explicitly

### **3. Multi-line Verses**
- Lines after a verse number are part of that verse
- Empty lines help separate verses (but not required)
- The system continues reading until the next verse number

### **4. Chorus Placement**
- Choruses are automatically placed after all verses
- If you want a chorus between verses, you'll need to edit manually after upload

### **5. Special Characters**
- Unicode characters are supported (e.g., é, ñ, ü)
- Make sure your file is saved as UTF-8 (for .txt files)

---

## ✅ **Best Practices**

1. **Always number verses**: `1.`, `2.`, `3.`, etc.
2. **Use clear titles**: First line should be the hymn title
3. **Separate verses**: Use empty lines between verses (optional but helpful)
4. **Mark choruses clearly**: Use `Chorus:` or `Refrain:`
5. **One hymn per file**: Each file should contain one hymn
6. **Test with one file first**: Upload one file to verify the format works

---

## 🧪 **Testing Your Format**

1. Create a test file with one hymn
2. Upload it via bulk upload
3. Check the result in admin
4. Verify:
   - Title is correct
   - Verses are in the right order
   - Chorus is marked correctly
   - Multi-line verses are preserved

---

## 📋 **Example Files**

### **Example 1: Simple Hymn**

```
Amazing Grace

1. Amazing grace, how sweet the sound
That saved a wretch like me

2. 'Twas grace that taught my heart to fear
And grace my fears relieved
```

### **Example 2: Hymn with Chorus**

```
How Great Thou Art

1. O Lord my God, when I in awesome wonder
Consider all the worlds Thy hands have made

Chorus: Then sings my soul, my Savior God, to Thee
How great Thou art, how great Thou art

2. When through the woods and forest glades I wander
And hear the birds sing sweetly in the trees
```

### **Example 3: Complex Hymn**

```
101. Blessed Assurance

1. Blessed assurance, Jesus is mine
O what a foretaste of glory divine
Heir of salvation, purchase of God
Born of His Spirit, washed in His blood

Refrain: This is my story, this is my song
Praising my Savior all the day long

2. Perfect submission, perfect delight
Visions of rapture now burst on my sight
Angels descending bring from above
Echoes of mercy, whispers of love
```

---

## 🚨 **Common Mistakes to Avoid**

1. ❌ **No verse numbers**: `Amazing grace, how sweet...` (should be `1. Amazing grace...`)
2. ❌ **Inconsistent numbering**: `1.`, `3.`, `5.` (should be `1.`, `2.`, `3.`)
3. ❌ **Title in wrong place**: Title should be first line
4. ❌ **Chorus not marked**: Just text without "Chorus:" prefix
5. ❌ **Multiple hymns in one file**: One file = one hymn

---

## 💡 **Summary**

**The system WILL extract and arrange the data automatically**, but you need to:
- ✅ Number your verses (`1.`, `2.`, `3.`)
- ✅ Put title first
- ✅ Mark choruses (`Chorus:` or `Refrain:`)
- ✅ One hymn per file

The system handles:
- ✅ Multi-line verses
- ✅ Empty lines
- ✅ Auto-numbering (if verses aren't numbered)
- ✅ Chorus placement

**Bottom line**: Follow the format rules above, and the system will extract everything correctly!



