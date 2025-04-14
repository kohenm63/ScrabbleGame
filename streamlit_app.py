import streamlit as st
import random
import google.generativeai as genai
import os
import time

# --- Configuration & Constants ---
st.set_page_config(page_title="🌀 מילים מבולבלות לפי רמות 🌀", layout="wide", initial_sidebar_state="collapsed")

# --- Emojis ---
EMOJI_THINKING = "🤔"; EMOJI_CORRECT = "✅"; EMOJI_WRONG = "❌"; EMOJI_HINT = "💡"
EMOJI_NEW = "🔄"; EMOJI_REVEAL = "👀"; EMOJI_PARTY = "🎉"; EMOJI_NICE_TRY = "💪"
EMOJI_BRAIN = "🧠"; EMOJI_STAR = "⭐"; EMOJI_WAIT = "⏳"; EMOJI_EASY = "😊"
EMOJI_MEDIUM = "🙂"; EMOJI_HARD = "😎"; EMOJI_API_ERROR = "📡"

# --- Word List & Level Definition ---
HEBREW_WORDS_ALL = [
    # Easy (3-4 letters)
    "בית", "ספר", "ילד", "שמש", "ירח", "כדור", "פרח", "עץ", "מים", "אור", "יום",
    "אבא", "אמא", "צבע", "גינה", "ים", "חול", "דלת", "אוכל", "כלב",
    # Medium (5 letters)
    "שלום", "ילדה", "חתול", "לילה", "משחק", "בלון", "עוגה", "מתנה", "כיסא", "שבוע",
    "חודש", "חלון", "אהבה", "עבודה", "חופש", "טיול",
    # Hard (6+ letters)
    "שולחן", "מחשב", "ישראל", "כתיבה", "קריאה", "משפחה", "מדינה", "חבר"
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
    "קשה": {"min": 6, "max": 10, "emoji": EMOJI_HARD}
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

# --- Gemini Model Setup (Sidebar) ---
st.sidebar.header(f"{EMOJI_BRAIN} הגדרות עוזר ה-AI")
api_key_input = st.sidebar.text_input(
    "מפתח API של גוגל (אם יש):",
    type="password",
    help="אפשר להשיג מפתח בחינם מ-Google AI Studio כדי לקבל רמזים ובדיקת מילים.",
)
api_key = api_key_input or os.getenv("GOOGLE_API_KEY")
model = None
gemini_enabled = False
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Using a capable model, adjust if needed
        model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_enabled = True
        st.sidebar.success(f"{EMOJI_CORRECT} עוזר ה-AI מוכן!")
    except Exception as e:
        st.sidebar.error(f"⚠️ שגיאה בהגדרת עוזר ה-AI: {e}")
        st.sidebar.caption("ייתכן שהמפתח שגוי או שיש בעיית רשת.")
elif not api_key:
    st.sidebar.info("ℹ️ אפשר לשחק גם בלי מפתח API, אבל לא יהיו רמזים או בדיקת מילים מיוחדת מה-AI.")

# --- Helper Functions ---

def scramble_word(word):
    """Scrambles the letters of a given word, ensuring it's different."""
    if not word: return ""
    char_list = list(word)
    # Shuffle at least once
    random.shuffle(char_list)
    scrambled = "".join(char_list)
    # Re-shuffle if identical (for words > 1 letter) up to a limit
    attempts = 0
    max_attempts = 5
    while scrambled == word and len(word) > 1 and attempts < max_attempts:
        random.shuffle(char_list)
        scrambled = "".join(char_list)
        attempts += 1
    return scrambled

def get_new_word():
    """Selects a new word based on the current level and resets game state."""
    current_level = st.session_state.current_level
    word_list = WORDS_BY_LEVEL.get(current_level, [])

    if not word_list:
        st.error(f"אוי לא! אין מילים ברמה '{current_level}'. נסו לבחור רמה אחרת.")
        st.stop() # Stop execution if no words available for the level
        return

    original_word = random.choice(word_list)
    # Ensure the new word isn't the same as the last one if possible
    max_tries = 3
    tries = 0
    while original_word == st.session_state.get('original_word') and len(word_list) > 1 and tries < max_tries:
        original_word = random.choice(word_list)
        tries += 1

    st.session_state.original_word = original_word
    st.session_state.scrambled_word = scramble_word(original_word)

    # Clear only relevant game state - NOT user_guess or level or score/streak
    if 'message' in st.session_state: del st.session_state.message
    if 'message_type' in st.session_state: del st.session_state.message_type
    if 'hint' in st.session_state: del st.session_state.hint
    if 'hint_for_word' in st.session_state: del st.session_state.hint_for_word

# --- Gemini Helper Functions ---

def check_word_validity_gemini(word_to_check):
    """Uses Gemini to check if a word is a valid Hebrew word. Returns True, False, or None."""
    if not model or not gemini_enabled:
        return None # Cannot perform check

    # Simple prompt focused on getting a clear yes/no
    prompt = f"האם '{word_to_check}' היא מילה תקינה ונפוצה בשפה העברית המודרנית? ענה רק 'כן' או 'לא'."
    try:
        # Configure for deterministic answer, shorter timeout might be useful
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.0 # Minimal temperature
            ),
            request_options={'timeout': 10} # 10 second timeout
            # Consider stricter safety if needed, but often causes issues with simple word checks
            # safety_settings={'HARASSMENT':'block_none', ...}
        )
        if response.parts:
            answer = response.text.strip().lower()
            # Check explicitly for 'כן' or 'לא' at the start for robustness
            if answer.startswith("כן"): return True
            if answer.startswith("לא"): return False
            st.sidebar.warning(f"Gemini (validity): תשובה לא ברורה '{answer}'")
            return None # Unclear answer
        else:
            reason = getattr(response.prompt_feedback, 'block_reason', 'Unknown')
            st.sidebar.warning(f"Gemini (validity): הבקשה נחסמה ({reason})")
            return None # Blocked or empty response
    except Exception as e:
        st.sidebar.error(f"Gemini (validity) Error: {e}")
        return None # Error during API call

def get_hint_gemini(word_to_hint):
    """Uses Gemini to generate a hint for the word. Returns hint text or error string."""
    if not model or not gemini_enabled:
        return f"{EMOJI_API_ERROR} עוזר ה-AI לא זמין כרגע."

    current_level = st.session_state.get('current_level', 'לא ידועה')
    # Prompt tailored for kids and level awareness
    prompt = f"""
אני ילד/ה שמשחק/ת במשחק ניחוש מילים בעברית ברמה '{current_level}'.
המילה שאני צריך/ה לנחש היא '{word_to_hint}'.
תן/י לי בבקשה רמז קצר, פשוט וקל להבנה בעברית למילה הזו, שמתאים לילדים ולרמת הקושי '{current_level}'.
אל תשתמש/י במילה '{word_to_hint}' עצמה או בשורש שלה ברמז.
הרמז צריך להיות משפט אחד קצר וברור.
לדוגמה, למילה 'חתול' ברמה קלה, רמז טוב יהיה: 'חיה שעושה מיאו'.
למילה 'מחשב' ברמה קשה, רמז טוב יהיה: 'מכשיר עם מסך ומקלדת שעוזר לנו ללמוד ולשחק'.
"""
    try:
        response = model.generate_content(
             prompt,
             generation_config=genai.types.GenerationConfig(
                 temperature=0.7 # Allow some creativity for hints
             ),
             request_options={'timeout': 15}, # Slightly longer timeout for generation
             # Safety settings might be needed depending on words/hints generated
             # safety_settings={'HARASSMENT':'block_none', ...}
        )
        if response.parts:
             hint_text = response.text.strip().replace("*","") # Remove markdown emphasis sometimes added
             # Basic validation: Check if hint is not too short or empty
             if hint_text and len(hint_text) > 3:
                 st.session_state.hint = hint_text
                 st.session_state.hint_for_word = word_to_hint # Track which word the hint is for
                 return hint_text
             else:
                 st.sidebar.warning(f"Gemini (hint): Received short/empty hint: '{hint_text}'")
                 return f"{EMOJI_THINKING} הממ... לא הצלחתי לחשוב על רמז טוב הפעם."
        else:
            reason = getattr(response.prompt_feedback, 'block_reason', 'Unknown')
            st.sidebar.warning(f"Gemini (hint): הבקשה נחסמה ({reason})")
            return f"{EMOJI_BRAIN} לא ניתן היה ליצור רמז (אולי נחסם)."

    except Exception as e:
        st.sidebar.error(f"Gemini (hint) Error: {e}")
        return f"{EMOJI_API_ERROR} שגיאה ביצירת רמז מהעוזר."

# --- Initialize Session State ---
if 'current_level' not in st.session_state:
    st.session_state.current_level = LEVEL_NAMES[0]
if 'original_word' not in st.session_state:
    # Must call get_new_word *after* current_level is set
    get_new_word()
if 'last_btn_press' not in st.session_state:
    st.session_state.last_btn_press = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'streak' not in st.session_state:
    st.session_state.streak = 0
if 'level_selector' not in st.session_state:
     st.session_state.level_selector = st.session_state.current_level

# --- Callback for Level Change ---
def handle_level_change():
    """Called when the level selection radio button changes."""
    new_level = st.session_state.level_selector # Get value from the widget's key
    if new_level != st.session_state.current_level: # Check if level actually changed
        st.session_state.current_level = new_level
        st.session_state.streak = 0 # Reset streak
        st.toast(f"עוברים לרמה {new_level}! {LEVEL_DEFINITIONS[new_level]['emoji']}", icon="🚀")
        get_new_word() # Fetch a word for the new level
        # Clear user input and other game state messages/hints
        if "user_guess" in st.session_state: del st.session_state.user_guess
        if 'message' in st.session_state: del st.session_state.message
        if 'message_type' in st.session_state: del st.session_state.message_type
        if 'hint' in st.session_state: del st.session_state.hint
        if 'hint_for_word' in st.session_state: del st.session_state.hint_for_word
    # No st.rerun() needed here, Streamlit handles rerun after callback completes

# --- Main App Layout ---
st.title(f"🌀 מילים מבולבלות - בחרו רמה! 🌀")
st.divider()

col_game, col_info = st.columns([2.5, 1]) # Game area wider

with col_game:
    st.subheader(f"סידור אותיות - רמה: {st.session_state.current_level} {LEVEL_DEFINITIONS[st.session_state.current_level]['emoji']}")
    # Scrambled Word Display - Big and Colorful
    scrambled_html = f"<h1 style='text-align: center; color: #0068C9; font-weight: bold; letter-spacing: 5px; margin-bottom: 15px;'>{st.session_state.scrambled_word}</h1>"
    st.markdown(scrambled_html, unsafe_allow_html=True)

    # User Input
    guess = st.text_input(
        "כתבו כאן את הניחוש שלכם:",
        key="user_guess", # Crucial for linking widget state
        value=st.session_state.get("user_guess", ""), # Maintain value across reruns
        placeholder="מה המילה?...",
        label_visibility="collapsed"
    )

    # Hint Area - Placeholder for dynamic content
    hint_area = st.empty()
    # Display hint ONLY if it exists in state AND is for the CURRENT word
    if 'hint' in st.session_state and st.session_state.get('hint_for_word') == st.session_state.get('original_word'):
         hint_area.info(f"{EMOJI_HINT} רמז: {st.session_state.hint}")

    # Feedback Area - Placeholder for dynamic content
    feedback_area = st.empty()

with col_info:
    # Level Selection Widget
    st.subheader("בחירת רמה")
    st.radio(
        "בחרו רמת קושי:",
        options=LEVEL_NAMES,
        key="level_selector", # Links to session state key
        on_change=handle_level_change, # Function to call on change
        horizontal=True, # Display side-by-side
        label_visibility="collapsed" # Hide the default label
    )
    st.caption(f"קל: {LEVEL_DEFINITIONS['קל']['min']}-{LEVEL_DEFINITIONS['קל']['max']} | "
               f"בינוני: {LEVEL_DEFINITIONS['בינוני']['min']} | "
               f"קשה: {LEVEL_DEFINITIONS['קשה']['min']}+ אותיות")
    st.divider()

    # Score Display
    st.subheader("הניקוד שלי")
    st.metric(label=f"{EMOJI_STAR} סך הכל נקודות", value=st.session_state.score)
    st.metric(label="🔥 רצף הצלחות", value=st.session_state.streak)
    st.divider()

    # Action Buttons
    st.subheader("פעולות")
    MIN_CLICK_INTERVAL = 1.0 # Debounce interval in seconds
    # Check if enough time has passed since the last button press
    can_process_click = time.time() - st.session_state.last_btn_press > MIN_CLICK_INTERVAL

    # Button definitions with disabling logic
    check_button = st.button(f"{EMOJI_CORRECT} בדוק!", use_container_width=True, type="primary", disabled=not can_process_click or not st.session_state.get("user_guess"))
    hint_button = st.button(f"{EMOJI_HINT} אפשר רמז?", use_container_width=True, disabled=not gemini_enabled or not can_process_click)
    reveal_button = st.button(f"{EMOJI_REVEAL} גיליתי...", use_container_width=True, disabled=not can_process_click)
    new_word_button = st.button(f"{EMOJI_NEW} מילה אחרת (באותה רמה)", use_container_width=True, disabled=not can_process_click)

    # Show wait message if buttons are temporarily disabled
    if not can_process_click:
        st.caption(f"{EMOJI_WAIT} רק שניה...")

# --- Game Logic --- Executes based on button presses if debounce allows ---

current_time = time.time() # Get current time once for efficiency

# Process button clicks only if debounce interval has passed
if can_process_click:

    # --- Check Answer Logic ---
    if check_button and guess: # Ensure guess has content
        st.session_state.last_btn_press = current_time # Record press time
        cleaned_guess = guess.strip()

        # Correct Guess Branch
        if cleaned_guess == st.session_state.original_word:
            st.session_state.score += 1
            st.session_state.streak += 1
            st.balloons() # Fun celebration!
            st.session_state.message = f"{EMOJI_PARTY} יש! כל הכבוד! המילה היא '{st.session_state.original_word}'. קבלו מילה חדשה!"
            st.session_state.message_type = "success"
            feedback_area.success(st.session_state.message) # Show immediate feedback
            hint_area.empty() # Clear any old hint
            st.toast(f"מעולה! +1 נקודה {EMOJI_STAR}", icon=EMOJI_PARTY)
            time.sleep(2) # Pause to show message/balloons

            get_new_word() # Prepare next word state

            # CRITICAL: Clear input widget state *before* rerun
            if "user_guess" in st.session_state:
                del st.session_state.user_guess

            st.rerun() # Trigger rerun to display new word and clear input

        # Incorrect Guess Branch
        else:
            st.session_state.streak = 0 # Reset streak
            st.session_state.user_guess = cleaned_guess # Keep wrong guess in box for editing
            validity_check_result = None
            validity_message = ""
            if gemini_enabled:
                with st.spinner(f"{EMOJI_THINKING} המממ... בודק אם המילה קיימת..."):
                    validity_check_result = check_word_validity_gemini(cleaned_guess)

            # Tailor feedback based on validity check
            if validity_check_result is True:
                validity_message = f"'{cleaned_guess}' זו מילה, אבל לא זו שחיפשנו."
                st.session_state.message = f"אופס... {validity_message} נסו שוב! {EMOJI_NICE_TRY}"
                st.session_state.message_type = "warning"
            elif validity_check_result is False:
                 validity_message = f"לא בטוח ש-' {cleaned_guess}' זו מילה קיימת..."
                 st.session_state.message = f"הו לא... {validity_message} בואו ננסה שוב! {EMOJI_NICE_TRY}"
                 st.session_state.message_type = "error"
            else: # Gemini disabled or check failed
                 st.session_state.message = f"לא נכון... {EMOJI_THINKING} נסו שוב, אתם יכולים!"
                 st.session_state.message_type = "error"
            # No rerun here, just update feedback message state for display later

    # --- Get Hint Logic ---
    elif hint_button and gemini_enabled:
        st.session_state.last_btn_press = current_time
        current_word = st.session_state.original_word

        # Only fetch hint if we don't have one for the *current* word
        if st.session_state.get('hint_for_word') != current_word:
            with st.spinner(f"{EMOJI_BRAIN} חושב על רמז טוב..."):
                hint_text = get_hint_gemini(current_word) # This updates state on success

            # Check if hint generation was successful (updates state) or returned an error message
            if 'hint' in st.session_state and st.session_state.hint_for_word == current_word:
                 # Successfully got and stored hint - clear other messages
                 if 'message' in st.session_state: del st.session_state.message
                 if 'message_type' in st.session_state: del st.session_state.message_type
                 feedback_area.empty() # Clear previous feedback
                 st.toast("קיבלת רמז!", icon=EMOJI_HINT)
                 # No rerun needed, display logic will pick up the new hint
            else:
                # Hint generation failed or returned error message
                st.session_state.message = hint_text # Display the error message
                st.session_state.message_type = "warning"
        else:
             # Hint already exists for this word
             if 'message' in st.session_state: del st.session_state.message
             if 'message_type' in st.session_state: del st.session_state.message_type
             feedback_area.empty() # Clear other messages
             st.toast("הרמז כבר מוצג!", icon="👇")
             # No rerun needed

    # --- Reveal Answer Logic ---
    elif reveal_button:
        st.session_state.last_btn_press = current_time
        st.session_state.streak = 0 # Reset streak
        st.session_state.message = f"{EMOJI_REVEAL} המילה היתה: **{st.session_state.original_word}**. לא נורא, נסו את הבאה!"
        st.session_state.message_type = "info"
        hint_area.empty() # Clear any hint display
        # No rerun needed, feedback will update

    # --- Get New Word (Manual Button Request) ---
    elif new_word_button:
        st.session_state.last_btn_press = current_time
        st.session_state.streak = 0 # Reset streak for skipping
        st.toast(f"טוען מילה חדשה ברמה '{st.session_state.current_level}'... {EMOJI_NEW}", icon=EMOJI_WAIT)

        get_new_word() # Prepare next word state for the current level

        hint_area.empty() # Clear hint display
        feedback_area.empty() # Clear previous feedback

        # CRITICAL: Clear input widget state *before* rerun
        if "user_guess" in st.session_state:
             del st.session_state.user_guess

        st.rerun() # Trigger rerun to display new word and clear input

# --- Display Feedback (Always evaluated after potential state changes) ---
# Handles messages set by incorrect guesses, reveals, hint errors etc.
if 'message' in st.session_state and 'message_type' in st.session_state:
    msg_type = st.session_state.message_type
    message = st.session_state.message
    # Avoid re-displaying success message right after rerun trigger
    is_success_loading = (msg_type == "success" and "קבלו מילה חדשה" in message)

    if not is_success_loading:
        if msg_type == "success": feedback_area.success(message, icon=EMOJI_PARTY)
        elif msg_type == "error": feedback_area.error(message, icon=EMOJI_WRONG)
        elif msg_type == "info": feedback_area.info(message, icon=EMOJI_REVEAL)
        elif msg_type == "warning": feedback_area.warning(message, icon=EMOJI_THINKING)

# --- Footer ---
st.divider()
st.caption(f"משחק 'מילים מבולבלות לפי רמות' | {EMOJI_BRAIN} מופעל בעזרת Streamlit ו-Google Gemini")