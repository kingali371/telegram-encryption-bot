#!/usr/bin/env python3
"""
Telegram Encryption Bot - بوت التشفير للتليجرام
المميزات: تشفير الملفات + النصوص + Base64 + هاش
"""

import os
import base64
import hashlib
import logging
import tempfile
from typing import Dict, Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات البيئية
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
PORT = int(os.environ.get('PORT', 8080))

# الحد الأقصى لحجم الملف (20 ميجابايت للتليجرام)
MAX_FILE_SIZE = 20 * 1024 * 1024

class EncryptionBot:
    """بوت التشفير الرئيسي مع دعم الملفات"""
    
    def __init__(self):
        self.user_sessions: Dict[int, dict] = {}
    
    def is_authorized(self, user_id: int) -> bool:
        """التحقق من صلاحية المستخدم"""
        return user_id == OWNER_ID
    
    def generate_key(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """توليد مفتاح AES من كلمة مرور"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt_text(self, text: str, password: str) -> str:
        """تشفير نص"""
        key, salt = self.generate_key(password)
        f = Fernet(key)
        encrypted = f.encrypt(text.encode())
        result = base64.b64encode(salt + encrypted).decode()
        return result
    
    def decrypt_text(self, encrypted_data: str, password: str) -> Optional[str]:
        """فك تشفير نص"""
        try:
            data = base64.b64decode(encrypted_data)
            salt = data[:16]
            encrypted = data[16:]
            key, _ = self.generate_key(password, salt)
            f = Fernet(key)
            decrypted = f.decrypt(encrypted).decode()
            return decrypted
        except Exception:
            return None
    
    def encrypt_file(self, file_data: bytes, password: str) -> bytes:
        """تشفير ملف بالكامل"""
        key, salt = self.generate_key(password)
        f = Fernet(key)
        encrypted = f.encrypt(file_data)
        # إضافة الملح في البداية
        return salt + encrypted
    
    def decrypt_file(self, encrypted_data: bytes, password: str) -> Optional[bytes]:
        """فك تشفير ملف"""
        try:
            salt = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            key, _ = self.generate_key(password, salt)
            f = Fernet(key)
            decrypted = f.decrypt(encrypted)
            return decrypted
        except Exception:
            return None
    
    def encode_base64(self, text: str) -> str:
        """Base64 تشفير"""
        return base64.b64encode(text.encode()).decode()
    
    def decode_base64(self, encoded: str) -> Optional[str]:
        """Base64 فك تشفير"""
        try:
            return base64.b64decode(encoded).decode()
        except Exception:
            return None
    
    def hash_text(self, text: str, algo: str = 'sha256') -> str:
        """توليد هاش"""
        if algo == 'sha256':
            return hashlib.sha256(text.encode()).hexdigest()
        elif algo == 'md5':
            return hashlib.md5(text.encode()).hexdigest()
        return None

# إنشاء كائن البوت
encryption_bot = EncryptionBot()

# ============= أوامر البوت ============= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    user_id = update.effective_user.id
    
    if not encryption_bot.is_authorized(user_id):
        await update.message.reply_text("❌ عذراً، هذا البوت مخصص للمالك فقط.")
        return
    
    welcome_text = """
🔐 **بوت التشفير المتقدم - الإصدار 2.0**

مرحباً! يمكنني مساعدتك في تشفير الملفات والنصوص بأمان.

**📁 المميزات الجديدة:**
✅ تشفير الملفات بالكامل (أي نوع ملف)
✅ فك تشفير الملفات واستلامها
✅ تشفير النصوص (AES-256)
✅ تشفير Base64
✅ توليد هاش SHA256/MD5

**📌 كيفية الاستخدام:**
• **لتشفير ملف:** أرسل الملف مباشرة
• **لفك تشفير ملف:** أرسل الملف المشفر (.encrypted)

**📋 الأوامر:**
/encrypt_text - تشفير نص
/decrypt_text - فك تشفير نص
/encode_b64 - تحويل إلى Base64
/decode_b64 - فك Base64
/hash - توليد هاش
/help - عرض المساعدة
/about - معلومات عن البوت

⚠️ **ملاحظة:** أنت المالك الوحيد المسموح باستخدام هذا البوت.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المساعدة"""
    help_text = """
📖 **دليل الاستخدام الكامل:**

🔹 **تشفير ملف:**
1. أرسل الملف الذي تريد تشفيره
2. أدخل كلمة المرور
3. استلم الملف المشفر بصيغة `.encrypted`

🔹 **فك تشفير ملف:**
1. أرسل الملف المشفر (ينتهي بـ .encrypted)
2. أدخل كلمة المرور
3. استلم الملف الأصلي

🔹 **تشفير نص (AES):**
`/encrypt_text` ثم النص، ثم كلمة المرور

🔹 **فك تشفير نص:**
`/decrypt_text` ثم النص المشفر، ثم كلمة المرور

🔹 **Base64:**
`/encode_b64` - تحويل نص إلى Base64
`/decode_b64` - فك تشفير Base64

🔹 **توليد هاش:**
`/hash` - اختيار نوع الهاش

⚠️ **تنبيهات مهمة:**
• الحد الأقصى لحجم الملف: 20 ميجابايت
• احتفظ بكلمة المرور بأمان - بدونها لا يمكن فك التشفير!
• الملفات المفككة تحمل نفس الاسم الأصلي

👤 **ايدي المالك:** `{}
    """.format(OWNER_ID)
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات عن البوت"""
    about_text = """
🤖 **بوت التشفير المتقدم v2.0**

✨ **المميزات:**
• تشفير AES-256 للملفات الكاملة
• تشفير AES-256 للنصوص
• تشفير Base64
• توليد هاش SHA256/MD5
• دعم جميع أنواع الملفات
• واجهة سهلة بالعربية

🛡️ **تقنيات الأمان:**
• PBKDF2 مع 100,000 تكرار
• ملح عشوائي (16 بايت) لكل ملف
• مفاتيح فريدة لكل عملية
• Fernet (تشفير متماثل آمن)

📊 **إحصائيات:**
• حجم الملف الأقصى: 20 ميجابايت
• زمن التشفير: < 5 ثوانٍ للملفات الصغيرة

👨‍💻 **المطور:** Your Name
📅 **الإصدار:** 2.0.0
🔗 **المصدر:** GitHub
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')


async def encrypt_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء تشفير النص"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    context.user_data['action'] = 'encrypt_text_waiting'
    await update.message.reply_text(
        "✏️ أرسل النص الذي تريد تشفيره:\n\n"
        "(يمكنك إلغاء العملية بإرسال /cancel)"
    )


async def decrypt_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء فك تشفير النص"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    context.user_data['action'] = 'decrypt_text_waiting'
    await update.message.reply_text(
        "🔐 أرسل النص المشفر:\n\n"
        "(يمكنك إلغاء العملية بإرسال /cancel)"
    )


async def encode_b64_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشفير Base64"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    context.user_data['action'] = 'encode_b64_waiting'
    await update.message.reply_text("📝 أرسل النص لتحويله إلى Base64:")


async def decode_b64_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فك Base64"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    context.user_data['action'] = 'decode_b64_waiting'
    await update.message.reply_text("🔓 أرسل النص المشفر (Base64) لفك تشفيره:")


async def hash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار نوع الهاش"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    keyboard = [
        [InlineKeyboardButton("🔐 SHA256", callback_data="hash_sha256")],
        [InlineKeyboardButton("📝 MD5", callback_data="hash_md5")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔐 **اختر نوع الهاش:**", 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not encryption_bot.is_authorized(user_id):
        await query.edit_message_text("❌ غير مصرح لك باستخدام هذا البوت.")
        return
    
    if query.data.startswith("hash_"):
        algo = query.data.replace("hash_", "")
        context.user_data['hash_algo'] = algo
        context.user_data['action'] = 'hash_waiting'
        await query.edit_message_text(
            f"✅ تم اختيار {algo.upper()}\n\n"
            f"📝 أرسل النص لتوليد الهاش:"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    text = update.message.text.strip()
    action = context.user_data.get('action')
    
    if action == 'encrypt_text_waiting':
        context.user_data['text_to_encrypt'] = text
        context.user_data['action'] = 'encrypt_text_password'
        await update.message.reply_text("🔑 أدخل كلمة المرور للتشفير:")
    
    elif action == 'encrypt_text_password':
        password = text
        plain_text = context.user_data.get('text_to_encrypt')
        try:
            encrypted = encryption_bot.encrypt_text(plain_text, password)
            await update.message.reply_text(
                f"✅ **تم التشفير بنجاح!**\n\n"
                f"📝 **النص المشفر:**\n`{encrypted}`\n\n"
                f"⚠️ **تنبيه:** احتفظ بكلمة المرور (`{password}`) لفك التشفير!",
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في التشفير: {e}")
        finally:
            context.user_data.clear()
    
    elif action == 'decrypt_text_waiting':
        context.user_data['text_to_decrypt'] = text
        context.user_data['action'] = 'decrypt_text_password'
        await update.message.reply_text("🔑 أدخل كلمة المرور لفك التشفير:")
    
    elif action == 'decrypt_text_password':
        password = text
        encrypted_text = context.user_data.get('text_to_decrypt')
        try:
            decrypted = encryption_bot.decrypt_text(encrypted_text, password)
            if decrypted:
                await update.message.reply_text(
                    f"✅ **تم فك التشفير بنجاح!**\n\n"
                    f"📝 **النص الأصلي:**\n`{decrypted}`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **فشل فك التشفير!**\n\n"
                    "🔍 الأسباب المحتملة:\n"
                    "• كلمة المرور غير صحيحة\n"
                    "• النص المشفر تالف\n"
                    "• النص ليس بصيغة صحيحة"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")
        finally:
            context.user_data.clear()
    
    elif action == 'encode_b64_waiting':
        result = encryption_bot.encode_base64(text)
        await update.message.reply_text(
            f"✅ **Base64:**\n\n`{result}`",
            parse_mode='Markdown'
        )
        context.user_data.clear()
    
    elif action == 'decode_b64_waiting':
        result = encryption_bot.decode_base64(text)
        if result:
            await update.message.reply_text(
                f"✅ **النص الأصلي:**\n\n`{result}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ نص Base64 غير صالح!")
        context.user_data.clear()
    
    elif action == 'hash_waiting':
        algo = context.user_data.get('hash_algo', 'sha256')
        result = encryption_bot.hash_text(text, algo)
        await update.message.reply_text(
            f"✅ **{algo.upper()}:**\n\n`{result}`\n\n"
            f"📊 **طول الهاش:** {len(result)} حرف",
            parse_mode='Markdown'
        )
        context.user_data.clear()
    
    else:
        await update.message.reply_text(
            "❓ أمر غير معروف.\n"
            "📌 استخدم /help لعرض الأوامر المتاحة."
        )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الملفات (تشفير أو فك تشفير)"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        await update.message.reply_text("❌ غير مصرح لك.")
        return
    
    # الحصول على معلومات الملف
    document = update.message.document
    file_name = document.file_name
    file_size = document.file_size
    
    # التحقق من الحجم
    if file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            f"❌ **الملف كبير جداً!**\n\n"
            f"📊 حجم ملفك: {file_size / (1024*1024):.1f} ميجابايت\n"
            f"⚠️ الحد الأقصى: 20 ميجابايت\n\n"
            f"💡 نصيحة: يمكنك ضغط الملف أو تقسيمه.",
            parse_mode='Markdown'
        )
        return
    
    # إرسال رسالة معالجة
    status_msg = await update.message.reply_text(
        f"📥 **جاري تحميل الملف...**\n"
        f"📄 الاسم: `{file_name}`\n"
        f"📦 الحجم: {file_size / 1024:.1f} كيلوبايت",
        parse_mode='Markdown'
    )
    
    try:
        # تحميل الملف
        file = await document.get_file()
        file_data = await file.download_as_bytearray()
        
        # التحقق إذا كان ملف مشفر أم لا
        is_encrypted = file_name.endswith('.encrypted')
        
        if is_encrypted:
            # عملية فك التشفير
            await status_msg.edit_text(
                f"🔐 **ملف مشفر مكتشف!**\n\n"
                f"📄 الاسم الأصلي: `{file_name}`\n\n"
                f"🔑 أرسل كلمة المرور لفك التشفير:",
                parse_mode='Markdown'
            )
            context.user_data['file_action'] = 'decrypt'
            context.user_data['encrypted_data'] = bytes(file_data)
            context.user_data['original_name'] = file_name.replace('.encrypted', '')
        
        else:
            # عملية التشفير
            await status_msg.edit_text(
                f"🔒 **ملف عادي مكتشف!**\n\n"
                f"📄 الاسم: `{file_name}`\n"
                f"📦 الحجم: {file_size / 1024:.1f} كيلوبايت\n\n"
                f"🔑 أرسل كلمة المرور للتشفير:",
                parse_mode='Markdown'
            )
            context.user_data['file_action'] = 'encrypt'
            context.user_data['file_data'] = bytes(file_data)
            context.user_data['file_name'] = file_name
        
        # حفظ معرف رسالة الحالة لإرسال النتيجة لاحقاً
        context.user_data['status_msg_id'] = status_msg.message_id
        
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ في تحميل الملف: {e}")


async def handle_file_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة كلمة المرور للملفات"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    password = update.message.text.strip()
    action = context.user_data.get('file_action')
    
    if not action:
        return
    
    status_msg_id = context.user_data.get('status_msg_id')
    
    try:
        # حذف رسالة "أرسل كلمة المرور" القديمة
        await update.message.delete()
        
        if action == 'encrypt':
            # تشفير الملف
            file_data = context.user_data.get('file_data')
            file_name = context.user_data.get('file_name')
            
            # إرسال رسالة معالجة
            processing_msg = await update.message.reply_text(
                f"🔐 **جاري تشفير الملف...**\n"
                f"📄 `{file_name}`\n"
                f"⏳ قد يستغرق بضع ثوانٍ...",
                parse_mode='Markdown'
            )
            
            # تنفيذ التشفير
            encrypted_data = encryption_bot.encrypt_file(file_data, password)
            
            # حفظ الملف المشفر مؤقتاً
            encrypted_file_name = f"{file_name}.encrypted"
            with tempfile.NamedTemporaryFile(delete=False, suffix='.encrypted') as tmp:
                tmp.write(encrypted_data)
                tmp_path = tmp.name
            
            # إرسال الملف المشفر
            with open(tmp_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=encrypted_file_name,
                    caption=f"✅ **تم تشفير الملف بنجاح!**\n\n"
                           f"📄 الاسم الأصلي: `{file_name}`\n"
                           f"🔑 كلمة المرور: `{password}`\n\n"
                           f"⚠️ **احتفظ بكلمة المرور بأمان!**\n"
                           f"بدونها لا يمكن استعادة الملف.",
                    parse_mode='Markdown'
                )
            
            # تنظيف الملفات المؤقتة
            os.unlink(tmp_path)
            await processing_msg.delete()
            
            # حذف رسالة الحالة القديمة
            if status_msg_id:
                await context.bot.delete_message(chat_id=user_id, message_id=status_msg_id)
            
            context.user_data.clear()
        
        elif action == 'decrypt':
            # فك تشفير الملف
            encrypted_data = context.user_data.get('encrypted_data')
            original_name = context.user_data.get('original_name', 'decrypted_file')
            
            # إرسال رسالة معالجة
            processing_msg = await update.message.reply_text(
                f"🔓 **جاري فك تشفير الملف...**\n"
                f"📄 `{original_name}`\n"
                f"⏳ جاري المعالجة...",
                parse_mode='Markdown'
            )
            
            # تنفيذ فك التشفير
            decrypted_data = encryption_bot.decrypt_file(encrypted_data, password)
            
            if decrypted_data:
                # حفظ الملف المفكك مؤقتاً
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_name)[1]) as tmp:
                    tmp.write(decrypted_data)
                    tmp_path = tmp.name
                
                # إرسال الملف المفكك
                with open(tmp_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        filename=original_name,
                        caption=f"✅ **تم فك تشفير الملف بنجاح!**\n\n"
                               f"📄 الاسم الأصلي: `{original_name}`\n"
                               f"📦 الحجم: {len(decrypted_data) / 1024:.1f} كيلوبايت",
                        parse_mode='Markdown'
                    )
                
                # تنظيف الملفات المؤقتة
                os.unlink(tmp_path)
            else:
                await update.message.reply_text(
                    "❌ **فشل فك التشفير!**\n\n"
                    "🔍 **الأسباب المحتملة:**\n"
                    "• كلمة المرور غير صحيحة\n"
                    "• الملف تالف أو غير مدعوم\n\n"
                    "💡 **نصيحة:** تأكد من صحة كلمة المرور وحاول مرة أخرى."
                )
            
            await processing_msg.delete()
            
            # حذف رسالة الحالة القديمة
            if status_msg_id:
                await context.bot.delete_message(chat_id=user_id, message_id=status_msg_id)
            
            context.user_data.clear()
    
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {e}")
        logger.error(f"Error in file password handler: {e}")
        context.user_data.clear()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ **تم إلغاء العملية بنجاح.**\n\n"
        "📌 يمكنك بدء عملية جديدة باستخدام الأوامر.",
        parse_mode='Markdown'
    )


# ============= تشغيل البوت ============= #

def main():
    """تشغيل البوت"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN غير موجود!")
        return
    
    if OWNER_ID == 0:
        logger.error("OWNER_ID غير موجود!")
        return
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("encrypt_text", encrypt_text_command))
    app.add_handler(CommandHandler("decrypt_text", decrypt_text_command))
    app.add_handler(CommandHandler("encode_b64", encode_b64_command))
    app.add_handler(CommandHandler("decode_b64", decode_b64_command))
    app.add_handler(CommandHandler("hash", hash_command))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # معالجة الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # معالجة الرسائل (النصية والملفات)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    # معالجة كلمات المرور للملفات (بعد تلقي الملف)
    # نضيف معالج إضافي للرسائل النصية بعد تلقي الملف
    # لكننا سنستخدم نفس handle_message مع التحقق من وجود file_action
    
    logger.info(f"✅ تشغيل البوت... PORT={PORT}")
    logger.info(f"👤 المالك ID: {OWNER_ID}")
    
    # تشغيل البوت مع webhook لـ Render
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
    )


if __name__ == "__main__":
    main()
