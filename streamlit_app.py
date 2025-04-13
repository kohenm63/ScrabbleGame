import streamlit as st
import random
import unicodedata

# --- Configuration ---
st.set_page_config(page_title="Hebrew Word Wizard", layout="centered")

# --- Hebrew Letter Pool (weighted for frequency) ---
LETTER_POOL = {
    'א': 8, 'ב': 6, 'ג': 4, 'ד': 5, 'ה': 9, 'ו': 8, 'ז': 3, 'ח': 4,
    'ט': 3, 'י': 9, 'כ': 6, 'ל': 7, 'מ': 7, 'נ': 7, 'ס': 4, 'ע': 5,
    'פ': 6, 'צ': 4, 'ק': 3, 'ר': 8, 'ש': 7, 'ת': 6,
    'ך': 1, 'ם': 1, 'ן': 1, 'ף': 1, 'ץ': 1
}

# --- Hebrew Letter Values (like Scrabble) ---
LETTER_VALUES = {
    'א': 1, 'ב': 3, 'ג': 3, 'ד': 2, 'ה': 1, 'ו': 1, 'ז': 4, 'ח': 4,
    'ט': 5, 'י': 1, 'כ': 2, 'ל': 1, 'מ': 3, 'נ': 1, 'ס': 1, 'ע': 3,
    'פ': 4, 'צ': 5, 'ק': 5, 'ר': 1, 'ש': 1, 'ת': 1,
    'ך': 2, 'ם': 3, 'ן': 1, 'ף': 4, 'ץ': 5
}

# --- Sample Hebrew word list (replace with full dictionary later) ---
VALID_WORDS = {
    

    "אבא", "אמא", "מים", "אור", "אוזן", "אוכל", "בית", "בלון", "ברווז", "בקבוק",
    "גזר", "גלגל", "גן", "גינה", "גמל", "דבש", "דגל", "דוב", "דוד", "דלת",
    "הרים", "הר", "הפסקה", "הפתעה", "הכנה", "וילון", "ויסקי", "וו", "ורד", "זבוב",
    "זית", "זנב", "זהב", "זר", "חבר", "חברה", "חתול", "חמור", "חולצה", "חנוכיה",
    "טוב", "טלוויזיה", "טלפון", "טיפה", "טנא", "ילד", "ילדה", "יונה", "ים", "יצירה",
    "כדור", "כיתה", "כיסא", "כפית", "כרית", "לב", "לחם", "לילה", "ליצן", "לקק",
    "מים", "מטריה", "מיטה", "מכנסיים", "מלפפון", "מנורה", "משפחה", "מתנה", "מתוק", "מקרר",
    "נוצה", "נעל", "נחל", "נמר", "נסיכה", "סבון", "סבתא", "ספר", "סוס", "סוכריה",
    "עגבניה", "עין", "עכבר", "עץ", "עגלה", "פח", "פרח", "פנס", "פעוט", "פרפר",
    "צבע", "צב", "ציפור", "צלחת", "צמה", "קיר", "קוף", "קיץ", "קלמר", "קרח",
    "ראש", "רגל", "רופא", "רעש", "ריח", "שולחן", "שמש", "שמלה", "שוקולד", "שן",
    "תינוק", "תפוח", "תמונה", "תיק", "תות", "תרנגול",'שלום', 'אבא', 'אמא', 'בית', 'מים', 'חתול', 'כלב', 'ילד', 'ילדה', 'שמש', 'לילה'}

# --- Generate a random set of 10 Hebrew letters ---
def get_random_letters():
    all_letters = []
    for letter, weight in LETTER_POOL.items():
        all_letters.extend([letter] * weight)
    return random.sample(all_letters, 10)

# --- Score calculation with letter values ---
def calculate_score(word):
    return sum(LETTER_VALUES.get(letter, 0) for letter in word)

# --- Main App ---
st.title("🔤 Hebrew Word Wizard 🧙‍♀️")
st.write("Compose a real Hebrew word using the 10 letters below!")

if 'letters' not in st.session_state:
    st.session_state.letters = get_random_letters()

st.markdown("### 🎴 Your Letters:")
st.markdown(" ".join([f"**{letter}**" for letter in st.session_state.letters]))

if st.button("🔄 New Letters"):
    st.session_state.letters = get_random_letters()
    st.experimental_rerun()

user_word = st.text_input("✍️ Enter a Hebrew word:")

if user_word:
    # Normalize and validate
    word_letters = list(user_word)
    original_letters = st.session_state.letters.copy()

    valid_use = True
    try:
        for letter in word_letters:
            original_letters.remove(letter)
    except ValueError:
        valid_use = False

    if user_word in VALID_WORDS and valid_use:
        score = calculate_score(user_word)
        st.success(f"✅ Valid word! You scored {score} points!")
    elif not valid_use:
        st.error("🚫 You used letters that weren't in your set!")
    else:
        st.error("🚫 Not a valid Hebrew word!")

st.markdown("---")
st.caption("🧠 Tip: Add more words to the dictionary to grow your game!")
