import streamlit as st
import random
import google.generativeai as genai
import os
import time

# --- Configuration & Constants ---
st.set_page_config(page_title="🌀 מילים מבולבלות לפי רמות 🌀", layout="wide", initial_sidebar_state="collapsed")

# --- Emojis (Keep from previous version) ---
EMOJI_THINKING = "🤔"; EMOJI_CORRECT = "✅"; EMOJI_WRONG = "❌"; EMOJI_HINT = "💡"
EMOJI_NEW = "🔄"; EMOJI_REVEAL = "👀"; EMOJI_PARTY = "🎉"; EMOJI_NICE_TRY = "💪"
EMOJI_BRAIN = "🧠"; EMOJI_STAR = "⭐"; EMOJI_WAIT = "⏳"; EMOJI_EASY = "😊"
EMOJI_MEDIUM = "🙂"; EMOJI_HARD = "😎"

# --- Word List & Level Definition ---
HEBREW_WORDS_ALL = [
    "שלום", "בית", "ספר", "ילד", "ילדה", "שמש", "ירח", "כדור", "פרח",
    "עץ", "מים", "אוכל", "חתול", "כלב", "אור", "יום", "לילה", "אבא", "אמא",
    "משחק", "צבע", "בלון", "גינה", "ים", "חול", "מתנה", "עוגה", "מחשב",
    "כתיבה", "קריאה", "אהבה", "ישראל", "שולחן", "כיסא", "עבודה", "חופש",
    "טיול", "משפחה", "מדינה", "חבר", "דלת", "חלון", "שבוע", "חודש", "שנה"
]

# --- Process words into levels by length ---
WORDS_BY_LEVEL = {
    "קל": [],
    "בינוני": [],
    "קשה": []
}
LEVEL_DEFINITIONS = {
    "קל": {"min": 3, "max": 4, "emoji": EMOJI_EASY},
    "בינוני": {"min": 5, "max": 5, "emoji": EMOJI_MEDIUM},
    "קשה": {"min": 6, "max": 10, "emoji": EMOJI_HARD} # Adjust max as needed
}
LEVEL_NAMES = list(LEVEL_DEFINITIONS.keys())

for word in HEBREW_WORDS_ALL:
    length = len(word)
    if LEVEL_DEFINITIONS["קל"]["min"] <= length <= LEVEL_DEFINITIONS["קל"]["max"]:
        WORDS_BY_LEVEL["קל"].append(word)
    elif LEVEL_DEFINITIONS["בינוני"]["min"] <= length <= LEVEL_DEFINITIONS["בינוני"]["max"]:
        WORDS_BY_LEVEL["בינוני"].append(word)
    elif LEVEL_DEFINITIONS["קשה"]["min"] <= length <= LEVEL_DEFINITIONS["קשה"]["max"]:
        WORDS_BY_LEVEL["קשה"].append(word)

# Check if levels have words
for level, words in WORDS_BY_LEVEL.items():
    if not words:
        st.warning(f"שימו לב: לא נמצאו מילים לרמה '{level}' עם ההגדרות הנוכחיות.")


# --- Gemini Model Setup (Sidebar - Same as before) ---
# ... (Include Gemini setup code here) ...
st.sidebar.header(f"{EMOJI_BRAIN} הגדרות עוזר ה-AI")
api_key_input = st.sidebar.text_input("מפתח API של גוגל (אם יש):", type="password", help="אפשר להשיג מפתח בחינם מ-Google AI Studio כדי לקבל רמזים ובדיקת מילים.")
api_key = api_key_input or os.getenv("GOOGLE_API_KEY")
model = None
gemini_enabled = False
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_enabled = True
        st.sidebar.success(f"{EMOJI_CORRECT} עוזר ה-AI מוכן!")
    except Exception as e: st.sidebar.error(f"⚠️ שגיאה בהגדרת עוזר ה-AI: {e}")
elif not api_key: st.sidebar.info("ℹ️ אפשר לשחק גם בלי מפתח API, אבל לא יהיו רמזים או בדיקת מילים מיוחדת.")


# --- Helper Functions ---

def scramble_word(word):
    # (Same as before)
    if not word: return ""
    char_list = list(word)
    random.shuffle(char_list)
    scrambled = "".join(char_list)
    attempts = 0; max_attempts = 5
    while scrambled == word and len(word) > 1 and attempts < max_attempts:
        random.shuffle(char_list); scrambled = "".join(char_list); attempts += 1
    return scrambled

def get_new_word():
    """Selects a new word based on the current level."""
    current_level = st.session_state.current_level
    word_list = WORDS_BY_LEVEL.get(current_level, [])

    if not word_list:
        st.error(f"אוי לא! אין מילים ברמה '{current_level}'. נסו לבחור רמה אחרת.")
        # Optionally, select from any level as fallback
        # all_words = [w for sublist in WORDS_BY_LEVEL.values() for w in sublist]
        # if all_words: original_word = random.choice(all_words) else: st.stop()
        st.stop() # Stop if no words for the level
        return # Added return for clarity after st.stop()

    original_word = random.choice(word_list)
    st.session_state.original_word = original_word
    st.session_state.scrambled_word = scramble_word(original_word)

    # Clear only relevant game state - NOT user_guess or level
    if 'message' in st.session_state: del st.session_state.message
    if 'message_type' in st.session_state: del st.session_state.message_type
    if 'hint' in st.session_state: del st.session_state.hint
    if 'hint_for_word' in st.session_state: del st.session_state.hint_for_word

# --- Gemini Helper Functions (Same as before) ---
# ... (Include check_word_validity_gemini and get_hint_gemini functions here - omitted for brevity) ...
def check_word_validity_gemini(word_to_check):
    if not model or not gemini_enabled: return None
    prompt = f"האם '{word_to_check}' היא מילה תקינה ומוכרת בשפה העברית המודרנית? ענה 'כן' או 'לא' בלבד, ללא שום תוספת."
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(candidate_count=1, temperature=0.1), safety_settings={'HARASSMENT':'block_none','HATE_SPEECH':'block_none','SEXUALLY_EXPLICIT':'block_none','DANGEROUS_CONTENT':'block_none'})
        if response.parts:
            answer = response.text.strip().lower()
            if "כן" in answer and "לא" not in answer: return True
            elif "לא" in answer: return False
            else: return None # Unclear
        else: return None # Blocked/empty
    except Exception: return None

def get_hint_gemini(word_to_hint):
    if not model or not gemini_enabled: return "עוזר ה-AI לא זמין כרגע."
    prompt = f"אני ילד/ה שמשחק/ת במשחק ניחוש מילים בעברית ברמה '{st.session_state.current_level}'. המילה שאני צריך/ה לנחש היא '{word_to_hint}'. תן/י לי בבקשה רמז קצר, פשוט וקל להבנה בעברית למילה הזו, שמתאים לרמת הקושי. אל תשתמש/י במילה עצמה או בשורש שלה. רמז של משפט אחד קצר."
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.7), safety_settings={'HARASSMENT':'block_none','HATE_SPEECH':'block_none','SEXUALLY_EXPLICIT':'block_none','DANGEROUS_CONTENT':'block_none'})
        if response.parts:
             hint_text = response.text.strip()
             st.session_state.hint = hint_text
             st.session_state.hint_for_word = word_to_hint
             return hint_text
        else: return f"לא הצלחתי לחשוב על רמז הפעם... {EMOJI_THINKING}"
    except Exception: return "שגיאה ביצירת רמז מהעוזר."

# --- Initialize Session State ---
if 'current_level' not in st.session_state:
    st.session_state.current_level = LEVEL_NAMES[0] # Default to first level ('קל')
if 'original_word' not in st.session_state:
    # Initial word fetch needs to happen *after* current_level is set
    get_new_word()
if 'last_btn_press' not in st.session_state:
    st.session_state.last_btn_press = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'streak' not in st.session_state:
    st.session_state.streak = 0
# Key for level selector widget state
if 'level_selector' not in st.session_state:
     st.session_state.level_selector = st.session_state.current_level

# --- Callback for Level Change ---
def handle_level_change():
    """Called when the level selection radio button changes."""
    # The new level is already in st.session_state.level_selector due to the key
    new_level = st.session_state.level_selector
    st.session_state.current_level = new_level # Update our main level tracker
    st.session_state.streak = 0 # Reset streak when changing level
    st.toast(f"עוברים לרמה {new_level}! {LEVEL_DEFINITIONS[new_level]['emoji']}", icon="🚀")
    get_new_word() # Fetch a word for the new level
    # Clear user input and other messages
    if "user_guess" in st.session_state: del st.session_state.user_guess
    if 'message' in st.session_state: del st.session_state.message
    if 'message_type' in st.session_state: del st.session_state.message_type
    if 'hint' in st.session_state: del st.session_state.hint
    if 'hint_for_word' in st.session_state: del st.session_state.hint_for_word
    # No st.rerun() needed here, Streamlit handles it after the callback


# --- Main App Layout ---
st.title(f"🌀 מילים מבולבלות - בחרו רמה! 🌀")
st.divider()

col_game, col_info = st.columns([2.5, 1])

with col_game:
    st.subheader(f"סידור אותיות - רמה: {st.session_state.current_level} {LEVEL_DEFINITIONS[st.session_state.current_level]['emoji']}")
    # Scrambled Word Display (same as before)
    scrambled_html = f"<h1 style='text-align: center; color: #0068C9; font-weight: bold; letter-spacing: 5px;'>{st.session_state.scrambled_word}</h1>"
    st.markdown(scrambled_html, unsafe_allow_html=True)
    st.write("")

    # User Input (same as before)
    guess = st.text_input("כתבו כאן את הניחוש שלכם:", key="user_guess", value=st.session_state.get("user_guess", ""), placeholder="מה המילה?...", label_visibility="collapsed")

    # Hint Area (same as before)
    hint_area = st.empty()
    if 'hint' in st.session_state and st.session_state.get('hint_for_word') == st.session_state.original_word:
         hint_area.info(f"{EMOJI_HINT} רמז: {st.session_state.hint}")

    # Feedback Area (same as before)
    feedback_area = st.empty()

with col_info:
    # --- Level Selection ---
    st.subheader("בחירת רמה")
    st.radio(
        "בחרו רמת קושי:",
        options=LEVEL_NAMES,
        key="level_selector", # Link widget state to session state
        on_change=handle_level_change, # Call this function when selection changes
        horizontal=True, # Display options side-by-side
        label_visibility="collapsed"
    )
    st.caption(f"קל: {LEVEL_DEFINITIONS['קל']['min']}-{LEVEL_DEFINITIONS['קל']['max']} אותיות | "
               f"בינוני: {LEVEL_DEFINITIONS['בינוני']['min']} אותיות | "
               f"קשה: {LEVEL_DEFINITIONS['קשה']['min']}+ אותיות")
    st.divider()

    # Score Display (same as before)
    st.subheader("הניקוד שלי")
    st.metric(label=f"{EMOJI_STAR} סך הכל נקודות", value=st.session_state.score)
    st.metric(label="🔥 רצף הצלחות", value=st.session_state.streak)
    st.divider()

    # Action Buttons (same as before)
    st.subheader("פעולות")
    MIN_CLICK_INTERVAL = 1.0
    can_process_click = time.time() - st.session_state.last_btn_press > MIN_CLICK_INTERVAL
    check_button = st.button(f"{EMOJI_CORRECT} בדוק!", use_container_width=True, type="primary", disabled=not can_process_click or not st.session_state.get("user_guess"))
    hint_button = st.button(f"{EMOJI_HINT} אפשר רמז?", use_container_width=True, disabled=not gemini_enabled or not can_process_click)
    reveal_button = st.button(f"{EMOJI_REVEAL} גיליתי...", use_container_width=True, disabled=not can_process_click)
    new_word_button = st.button(f"{EMOJI_NEW} מילה אחרת (באותה רמה)", use_container_width=True, disabled=not can_process_click)
    if not can_process_click: st.caption(f"{EMOJI_WAIT} רק שניה...")


# --- Game Logic (Mostly same as before, check/hint/reveal/new) ---
if can_process_click:
    # Check Answer Logic (Update score/streak, use balloons, get_new_word, clear input state, rerun)
    if check_button and guess:
        st.session_state.last_btn_press = time.time()
        cleaned_guess = guess.strip()
        if cleaned_guess == st.session_state.original_word:
            st.session_state.score += 1
            st.session_state.streak += 1
            st.balloons()
            st.session_state.message = f"{EMOJI_PARTY} יש! כל הכבוד! המילה היא '{st.session_state.original_word}'. קבלו מילה חדשה!"
            st.session_state.message_type = "success"
            feedback_area.success(st.session_state.message)
            hint_area.empty()
            st.toast(f"מעולה! +1 נקודה {EMOJI_STAR}", icon=EMOJI_PARTY)
            time.sleep(2)
            get_new_word() # Gets word for current level
            if "user_guess" in st.session_state: del st.session_state.user_guess
            st.rerun()
        else: # Incorrect guess
            st.session_state.streak = 0
            st.session_state.user_guess = cleaned_guess
            # ... (rest of incorrect guess logic with Gemini check is the same) ...
            validity_check_result = None; validity_message = ""
            if gemini_enabled:
                with st.spinner(f"{EMOJI_THINKING} המממ... בודק את המילה שלך..."): validity_check_result = check_word_validity_gemini(cleaned_guess)
            if validity_check_result is True: validity_message = f"'{cleaned_guess}' זו מילה נכונה, אבל לא מה שחיפשנו פה."; st.session_state.message = f"אופס... {validity_message} נסו שוב! {EMOJI_NICE_TRY}"; st.session_state.message_type = "warning"
            elif validity_check_result is False: validity_message = f"לא נראה לי ש-' {cleaned_guess}' זו מילה..."; st.session_state.message = f"הו לא... {validity_message} בואו ננסה שוב! {EMOJI_NICE_TRY}"; st.session_state.message_type = "error"
            else: st.session_state.message = f"לא נכון... {EMOJI_THINKING} נסו שוב, אתם יכולים!"; st.session_state.message_type = "error"


    # Get Hint Logic (Same as before)
    elif hint_button and gemini_enabled:
        # ... (hint logic remains the same, uses current_word from session state) ...
        st.session_state.last_btn_press = time.time()
        current_word = st.session_state.original_word
        if st.session_state.get('hint_for_word') != current_word:
            with st.spinner(f"{EMOJI_BRAIN} חושב על רמז טוב..."): hint_text = get_hint_gemini(current_word)
            if hint_text and "שגיאה" not in hint_text and "לא הצלחתי" not in hint_text :
                 if 'message' in st.session_state: del st.session_state.message
                 if 'message_type' in st.session_state: del st.session_state.message_type
                 feedback_area.empty(); st.toast("קיבלת רמז!", icon=EMOJI_HINT)
            elif hint_text: st.session_state.message = hint_text; st.session_state.message_type = "warning"
        else:
             if 'message' in st.session_state: del st.session_state.message
             if 'message_type' in st.session_state: del st.session_state.message_type
             feedback_area.empty(); st.toast("הרמז כבר כאן למטה!", icon="👇")


    # Reveal Answer Logic (Reset streak)
    elif reveal_button:
        st.session_state.last_btn_press = time.time()
        st.session_state.streak = 0 # Reset streak
        st.session_state.message = f"{EMOJI_REVEAL} המילה היתה: **{st.session_state.original_word}**. לא נורא, נסו את הבאה!"
        st.session_state.message_type = "info"
        hint_area.empty()

    # Get New Word (Manual Request - Reset streak, get_new_word for current level, clear input, rerun)
    elif new_word_button:
        st.session_state.last_btn_press = time.time()
        st.session_state.streak = 0 # Reset streak
        st.toast(f"טוען מילה חדשה ברמה '{st.session_state.current_level}'... {EMOJI_NEW}", icon=EMOJI_WAIT)
        get_new_word() # Gets new word for the *current* level
        hint_area.empty(); feedback_area.empty()
        if "user_guess" in st.session_state: del st.session_state.user_guess
        st.rerun()

# --- Display Feedback (Same as before) ---
if 'message' in st.session_state and 'message_type' in st.session_state:
    msg_type = st.session_state.message_type
    message = st.session_state.message
    is_success_loading = (msg_type == "success" and "קבלו מילה חדשה" in message)
    if not is_success_loading:
        if msg_type == "success": feedback_area.success(message, icon=EMOJI_PARTY)
        elif msg_type == "error": feedback_area.error(message, icon=EMOJI_WRONG)
        elif msg_type == "info": feedback_area.info(message, icon=EMOJI_REVEAL)
        elif msg_type == "warning": feedback_area.warning(message, icon=EMOJI_THINKING)

# --- Footer (Same as before) ---
st.divider()
st.caption(f"משחק 'מילים מבולבלות לפי רמות' | {EMOJI_BRAIN} מופעל בעזרת Streamlit ו-Google Gemini")