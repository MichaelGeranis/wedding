"""Email translations for multi-language support."""

EMAIL_TRANSLATIONS = {
    "en": {
        "rsvp_confirmed": "RSVP Confirmed!",
        "rsvp_received": "RSVP Received",
        "dear": "Dear",
        "thank_you_rsvp": "Thank you for your RSVP!",
        "excited_celebrate": "We're so excited to celebrate with you!",
        "will_miss_you": "We'll miss you!",
        "confirmation_number": "Confirmation Number",
        "status": "Status",
        "attending": "Attending",
        "not_attending": "Not Attending",
        "plus_one": "Plus One",
        "yes": "Yes",
        "dietary_restrictions": "Dietary Restrictions",
        "your_message": "Your Message",
        "changes_contact": "If you need to make any changes to your RSVP, please contact us directly.",
        "with_love": "With love",
        "wedding_team": "The happy couple",
        "automated_email": "This is an automated confirmation email. Please do not reply to this email.",
        "rsvp_details": "RSVP DETAILS",
    },
    "el": {
        "rsvp_confirmed": "Η Απάντησή σας Επιβεβαιώθηκε!",
        "rsvp_received": "Λάβαμε την Απάντησή σας",
        "dear": "Αγαπητέ/ή",
        "thank_you_rsvp": "Σας ευχαριστούμε για την απάντησή σας!",
        "excited_celebrate": "Ανυπομονούμε να γιορτάσουμε μαζί σας!",
        "will_miss_you": "Θα μας λείψετε!",
        "confirmation_number": "Αριθμός Επιβεβαίωσης",
        "status": "Κατάσταση",
        "attending": "Θα Παρευρεθώ",
        "not_attending": "Δεν θα Παρευρεθώ",
        "plus_one": "Συνοδός",
        "yes": "Ναι",
        "dietary_restrictions": "Διατροφικοί Περιορισμοί",
        "your_message": "Το Μήνυμά σας",
        "changes_contact": "Εάν χρειάζεται να κάνετε αλλαγές στην απάντησή σας, παρακαλούμε επικοινωνήστε μαζί μας απευθείας.",
        "with_love": "Με αγάπη",
        "wedding_team": "Το ζευγάρι",
        "automated_email": "Αυτό είναι ένα αυτοματοποιημένο email επιβεβαίωσης. Παρακαλώ μην απαντήσετε.",
        "rsvp_details": "ΛΕΠΤΟΜΕΡΕΙΕΣ ΑΠΑΝΤΗΣΗΣ",
    },
}


def get_translation(key: str, language: str = "en") -> str:
    """Get translated text for a given key and language."""
    lang = language if language in EMAIL_TRANSLATIONS else "en"
    return EMAIL_TRANSLATIONS[lang].get(key, EMAIL_TRANSLATIONS["en"].get(key, key))
