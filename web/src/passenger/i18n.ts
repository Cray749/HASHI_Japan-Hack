import type { PaxLang } from '../shared/types';

/** Every word the passenger app shows outside the request catalogue. Short and warm. */
const S = {
  pick: { en: 'Choose your language', hi: 'अपनी भाषा चुनिए', pa: 'ਆਪਣੀ ਬੋਲੀ ਚੁਣੋ' },
  seatAsk: { en: 'Your seat number', hi: 'आपकी सीट नंबर', pa: 'ਤੁਹਾਡੀ ਸੀਟ ਨੰਬਰ' },
  seatHint: { en: 'For example 24C', hi: 'जैसे 24C', pa: 'ਜਿਵੇਂ 24C' },
  next: { en: 'Next', hi: 'आगे', pa: 'ਅੱਗੇ' },
  back: { en: 'Back', hi: 'पीछे', pa: 'ਪਿੱਛੇ' },
  consentTitle: { en: 'Before we start', hi: 'शुरू करने से पहले', pa: 'ਸ਼ੁਰੂ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ' },
  consent1: {
    en: 'The crew can see your seat, your language and what you ask for.',
    hi: 'क्रू आपकी सीट, आपकी भाषा और आपकी माँग देख सकता है।',
    pa: 'ਕਰੂ ਤੁਹਾਡੀ ਸੀਟ, ਤੁਹਾਡੀ ਬੋਲੀ ਅਤੇ ਤੁਹਾਡੀ ਮੰਗ ਦੇਖ ਸਕਦਾ ਹੈ।',
  },
  consent2: {
    en: 'We do not keep your name. Everything is deleted after landing.',
    hi: 'हम आपका नाम नहीं रखते। उतरने के बाद सब कुछ मिटा दिया जाता है।',
    pa: 'ਅਸੀਂ ਤੁਹਾਡਾ ਨਾਮ ਨਹੀਂ ਰੱਖਦੇ। ਉੱਤਰਨ ਤੋਂ ਬਾਅਦ ਸਭ ਕੁਝ ਮਿਟਾ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ।',
  },
  consent3: {
    en: 'If you speak, your voice is used only to understand the request. It is not saved.',
    hi: 'आप बोलेंगे तो आवाज़ सिर्फ़ माँग समझने के लिए इस्तेमाल होगी। उसे सहेजा नहीं जाता।',
    pa: 'ਤੁਸੀਂ ਬੋਲੋਗੇ ਤਾਂ ਆਵਾਜ਼ ਸਿਰਫ਼ ਮੰਗ ਸਮਝਣ ਲਈ ਵਰਤੀ ਜਾਵੇਗੀ। ਇਹ ਸਾਂਭੀ ਨਹੀਂ ਜਾਂਦੀ।',
  },
  agreeVoice: { en: 'OK, I can speak', hi: 'ठीक है, आवाज़ चलेगी', pa: 'ਠੀਕ ਹੈ, ਆਵਾਜ਼ ਚੱਲੇਗੀ' },
  agreeTap: { en: 'Pictures only', hi: 'सिर्फ़ तस्वीरें', pa: 'ਸਿਰਫ਼ ਤਸਵੀਰਾਂ' },
  profileTitle: { en: 'Make it easy for you', hi: 'आपके लिए आसान बनाएँ', pa: 'ਤੁਹਾਡੇ ਲਈ ਸੌਖਾ ਬਣਾਈਏ' },
  senior: { en: 'Bigger text and pictures', hi: 'बड़े अक्षर और तस्वीरें', pa: 'ਵੱਡੇ ਅੱਖਰ ਅਤੇ ਤਸਵੀਰਾਂ' },
  firstTime: { en: 'First time flying', hi: 'पहली बार हवाई यात्रा', pa: 'ਪਹਿਲੀ ਵਾਰ ਹਵਾਈ ਸਫ਼ਰ' },
  veg: { en: 'Vegetarian', hi: 'शाकाहारी', pa: 'ਸ਼ਾਕਾਹਾਰੀ' },
  hearing: { en: 'I hear less well', hi: 'मुझे कम सुनाई देता है', pa: 'ਮੈਨੂੰ ਘੱਟ ਸੁਣਾਈ ਦਿੰਦਾ ਹੈ' },
  mobility: { en: 'I need help walking', hi: 'चलने में मदद चाहिए', pa: 'ਤੁਰਨ ਵਿੱਚ ਮਦਦ ਚਾਹੀਦੀ ਹੈ' },
  pictures: { en: 'Pictures first', hi: 'पहले तस्वीरें', pa: 'ਪਹਿਲਾਂ ਤਸਵੀਰਾਂ' },
  start: { en: 'Start', hi: 'शुरू करें', pa: 'ਸ਼ੁਰੂ ਕਰੋ' },
  skip: { en: 'Skip', hi: 'छोड़िए', pa: 'ਛੱਡੋ' },
  askWhat: { en: 'What do you need?', hi: 'आपको क्या चाहिए?', pa: 'ਤੁਹਾਨੂੰ ਕੀ ਚਾਹੀਦਾ ਹੈ?' },
  hello: { en: 'Hello', hi: 'नमस्ते', pa: 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ' },
  more: { en: 'More', hi: 'और', pa: 'ਹੋਰ' },
  holdSpeak: { en: 'Hold and speak', hi: 'दबाकर बोलिए', pa: 'ਦੱਬ ਕੇ ਬੋਲੋ' },
  listening: { en: 'Listening… release when done', hi: 'सुन रहे हैं… बोलकर छोड़िए', pa: 'ਸੁਣ ਰਹੇ ਹਾਂ… ਬੋਲ ਕੇ ਛੱਡੋ' },
  thinking: { en: 'Understanding…', hi: 'समझ रहे हैं…', pa: 'ਸਮਝ ਰਹੇ ਹਾਂ…' },
  didYouMean: { en: 'Did you mean this?', hi: 'क्या आपका मतलब यह है?', pa: 'ਕੀ ਤੁਹਾਡਾ ਮਤਲਬ ਇਹ ਹੈ?' },
  tapPicture: { en: 'Please tap a picture', hi: 'कृपया तस्वीर दबाइए', pa: 'ਕਿਰਪਾ ਕਰਕੇ ਤਸਵੀਰ ਦਬਾਓ' },
  yes: { en: 'Yes', hi: 'हाँ', pa: 'ਹਾਂ' },
  no: { en: 'No', hi: 'नहीं', pa: 'ਨਹੀਂ' },
  sent: { en: 'Sent to the crew', hi: 'क्रू को भेज दिया', pa: 'ਕਰੂ ਨੂੰ ਭੇਜ ਦਿੱਤਾ' },
  seen: { en: 'Crew is coming', hi: 'क्रू आ रहा है', pa: 'ਕਰੂ ਆ ਰਿਹਾ ਹੈ' },
  replied: { en: 'Crew replied', hi: 'क्रू ने जवाब दिया', pa: 'ਕਰੂ ਨੇ ਜਵਾਬ ਦਿੱਤਾ' },
  understood: { en: 'I understood', hi: 'समझ आ गया', pa: 'ਸਮਝ ਆ ਗਿਆ' },
  understoodDone: { en: 'Thank you, the crew knows', hi: 'धन्यवाद, क्रू को पता चल गया', pa: 'ਧੰਨਵਾਦ, ਕਰੂ ਨੂੰ ਪਤਾ ਲੱਗ ਗਿਆ' },
  cancel: { en: 'Cancel request', hi: 'माँग रद्द करें', pa: 'ਮੰਗ ਰੱਦ ਕਰੋ' },
  play: { en: 'Listen again', hi: 'फिर से सुनिए', pa: 'ਦੁਬਾਰਾ ਸੁਣੋ' },
  noReply: { en: 'No reply yet. Press help if urgent.', hi: 'अभी जवाब नहीं आया। ज़रूरी हो तो मदद दबाइए।', pa: 'ਹਾਲੇ ਜਵਾਬ ਨਹੀਂ ਆਇਆ। ਲੋੜ ਹੋਵੇ ਤਾਂ ਮਦਦ ਦਬਾਓ।' },
  helpBig: { en: 'I NEED HELP', hi: 'मदद चाहिए', pa: 'ਮਦਦ ਚਾਹੀਦੀ ਹੈ' },
  helpSure: { en: 'Call the crew now?', hi: 'क्रू को अभी बुलाएँ?', pa: 'ਕਰੂ ਨੂੰ ਹੁਣੇ ਬੁਲਾਈਏ?' },
  announcement: { en: 'Message from the crew', hi: 'क्रू का संदेश', pa: 'ਕਰੂ ਦਾ ਸੁਨੇਹਾ' },
  exitTitle: { en: 'Exit row check', hi: 'निकास पंक्ति की जाँच', pa: 'ਨਿਕਾਸ ਕਤਾਰ ਦੀ ਜਾਂਚ' },
  exitIntro: {
    en: 'You are sitting next to an emergency exit. The crew need to be sure you are ready to help.',
    hi: 'आप आपातकालीन निकास के पास बैठे हैं। क्रू को पक्का करना है कि आप मदद के लिए तैयार हैं।',
    pa: 'ਤੁਸੀਂ ਐਮਰਜੈਂਸੀ ਨਿਕਾਸ ਕੋਲ ਬੈਠੇ ਹੋ। ਕਰੂ ਨੂੰ ਪੱਕਾ ਕਰਨਾ ਹੈ ਕਿ ਤੁਸੀਂ ਮਦਦ ਲਈ ਤਿਆਰ ਹੋ।',
  },
  exitQ1: { en: 'Are you willing and able to help open the exit?', hi: 'क्या आप निकास खोलने में मदद करने को तैयार और सक्षम हैं?', pa: 'ਕੀ ਤੁਸੀਂ ਨਿਕਾਸ ਖੋਲ੍ਹਣ ਵਿੱਚ ਮਦਦ ਲਈ ਤਿਆਰ ਅਤੇ ਯੋਗ ਹੋ?' },
  exitQ2: { en: 'When do you open the exit door?', hi: 'आप निकास का दरवाज़ा कब खोलेंगे?', pa: 'ਤੁਸੀਂ ਨਿਕਾਸ ਦਾ ਦਰਵਾਜ਼ਾ ਕਦੋਂ ਖੋਲ੍ਹੋਗੇ?' },
  exitA1: { en: 'Only when the crew tell me to', hi: 'सिर्फ़ जब क्रू कहे', pa: 'ਸਿਰਫ਼ ਜਦੋਂ ਕਰੂ ਕਹੇ' },
  exitA2: { en: 'As soon as the plane stops', hi: 'विमान रुकते ही', pa: 'ਜਹਾਜ਼ ਰੁਕਦੇ ਹੀ' },
  exitA3: { en: 'I do not know', hi: 'मुझे नहीं पता', pa: 'ਮੈਨੂੰ ਨਹੀਂ ਪਤਾ' },
  exitThanks: { en: 'Thank you. The crew will confirm with you.', hi: 'धन्यवाद। क्रू आपसे पुष्टि करेगा।', pa: 'ਧੰਨਵਾਦ। ਕਰੂ ਤੁਹਾਡੇ ਨਾਲ ਪੁਸ਼ਟੀ ਕਰੇਗਾ।' },
  offline: { en: 'Connection lost. Trying again… your request will go when it returns.', hi: 'कनेक्शन टूट गया। फिर कोशिश हो रही है… वापस आते ही आपकी माँग भेज दी जाएगी।', pa: 'ਕਨੈਕਸ਼ਨ ਟੁੱਟ ਗਿਆ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਹੋ ਰਹੀ ਹੈ… ਮੁੜਦੇ ਹੀ ਤੁਹਾਡੀ ਮੰਗ ਭੇਜ ਦਿੱਤੀ ਜਾਵੇਗੀ।' },
  offlineHelp: { en: 'If it is urgent, press the call button on your seat.', hi: 'ज़रूरी हो तो अपनी सीट का कॉल बटन दबाइए।', pa: 'ਲੋੜੀਂਦਾ ਹੋਵੇ ਤਾਂ ਆਪਣੀ ਸੀਟ ਦਾ ਕਾਲ ਬਟਨ ਦਬਾਓ।' },
  landed: { en: 'Thank you for flying. Your data has been deleted.', hi: 'यात्रा के लिए धन्यवाद। आपका डेटा मिटा दिया गया है।', pa: 'ਸਫ਼ਰ ਲਈ ਧੰਨਵਾਦ। ਤੁਹਾਡਾ ਡਾਟਾ ਮਿਟਾ ਦਿੱਤਾ ਗਿਆ ਹੈ।' },
  micBlocked: { en: 'Microphone not available. Please use the pictures.', hi: 'माइक्रोफ़ोन उपलब्ध नहीं है। कृपया तस्वीरें इस्तेमाल करें।', pa: 'ਮਾਈਕ੍ਰੋਫ਼ੋਨ ਉਪਲਬਧ ਨਹੀਂ। ਕਿਰਪਾ ਕਰਕੇ ਤਸਵੀਰਾਂ ਵਰਤੋ।' },
  tooShort: { en: 'Too short. Hold the button while you speak.', hi: 'बहुत छोटा। बोलते समय बटन दबाए रखिए।', pa: 'ਬਹੁਤ ਛੋਟਾ। ਬੋਲਦੇ ਸਮੇਂ ਬਟਨ ਦੱਬੀ ਰੱਖੋ।' },
} as const;

export type Key = keyof typeof S;

/** Interface strings of the extra language packs, filled in when the catalogue loads. */
let PACK_UI: Record<string, Record<string, string>> = {};

export function setPackUi(ui: Record<string, Record<string, string>>): void {
  PACK_UI = ui ?? {};
}

export function t(lang: PaxLang, key: Key): string {
  const entry = S[key] as Record<string, string>;
  return entry[lang] ?? PACK_UI[lang]?.[key] ?? entry.en;
}

/** Categories on the "More" screen. */
export const CATEGORIES: { id: string; icon: string; label: Record<string, string> }[] = [
  { id: 'drink', icon: 'GlassWater', label: { en: 'Drinks', hi: 'पेय', pa: 'ਪੀਣ ਵਾਲਾ' } },
  { id: 'food', icon: 'Utensils', label: { en: 'Food', hi: 'खाना', pa: 'ਖਾਣਾ' } },
  { id: 'comfort', icon: 'BedDouble', label: { en: 'Comfort', hi: 'आराम', pa: 'ਆਰਾਮ' } },
  { id: 'seat', icon: 'Armchair', label: { en: 'Seat & screen', hi: 'सीट और स्क्रीन', pa: 'ਸੀਟ ਅਤੇ ਸਕਰੀਨ' } },
  { id: 'assist', icon: 'HandHelping', label: { en: 'Help', hi: 'सहायता', pa: 'ਸਹਾਇਤਾ' } },
  { id: 'info', icon: 'Info', label: { en: 'Information', hi: 'जानकारी', pa: 'ਜਾਣਕਾਰੀ' } },
];

export const LANG_NAMES: Record<string, string> = { pa: 'ਪੰਜਾਬੀ', hi: 'हिन्दी', en: 'English' };

export function setLanguages(list: { code: string; name: string }[]): void {
  for (const l of list) LANG_NAMES[l.code] = l.name;
}

/** The crew check-in card: "Is everything OK?", "I'm fine", "Please come to me". */
export const CHECKIN: Record<string, [string, string, string]> = {
  en: ["Is everything OK?", "I'm fine", "Please come to me"],
  hi: ["सब ठीक है?", "मैं ठीक हूँ", "कृपया मेरे पास आइए"],
  pa: ["ਸਭ ਠੀਕ ਹੈ?", "ਮੈਂ ਠੀਕ ਹਾਂ", "ਕਿਰਪਾ ਕਰਕੇ ਮੇਰੇ ਕੋਲ ਆਓ"],
  ta: ["எல்லாம் சரியா?", "நான் நலம்", "தயவுசெய்து என்னிடம் வாருங்கள்"],
  te: ["అంతా బాగుందా?", "నేను బాగున్నాను", "దయచేసి నా దగ్గరకు రండి"],
  bn: ["সব ঠিক আছে?", "আমি ঠিক আছি", "অনুগ্রহ করে আমার কাছে আসুন"],
  gu: ["બધું બરાબર છે?", "હું ઠીક છું", "કૃપા કરીને મારી પાસે આવો"],
  mr: ["सर्व ठीक आहे ना?", "मी ठीक आहे", "कृपया माझ्याकडे या"],
  kn: ["ಎಲ್ಲವೂ ಸರಿಯಾಗಿದೆಯೇ?", "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ", "ದಯವಿಟ್ಟು ನನ್ನ ಬಳಿ ಬನ್ನಿ"],
  ml: ["എല്ലാം ശരിയാണോ?", "എനിക്ക് കുഴപ്പമില്ല", "ദയവായി എന്റെ അടുത്ത് വരൂ"],
  th: ["ทุกอย่างเรียบร้อยดีไหม?", "ฉันสบายดี", "กรุณามาหาฉัน"],
  vi: ["Mọi thứ ổn chứ?", "Tôi ổn", "Xin hãy đến chỗ tôi"],
  id: ["Apakah semuanya baik-baik saja?", "Saya baik-baik saja", "Tolong datang ke tempat saya"],
  fil: ["Maayos ba ang lahat?", "Ayos lang ako", "Pakilapitan po ako"],
  ms: ["Adakah semuanya baik-baik sahaja?", "Saya baik-baik sahaja", "Sila datang kepada saya"],
  km: ["តើអ្វីៗទាំងអស់ល្អទេ?", "ខ្ញុំសុខសប្បាយ", "សូមមកជួបខ្ញុំ"],
  my: ["အားလုံး အဆင်ပြေပါသလား?", "ကျွန်ုပ် အဆင်ပြေပါသည်", "ကျေးဇူးပြု၍ ကျွန်ုပ်ဆီ လာပါ"],
};
