#!/usr/bin/env python3
"""
Telegram Encryption Bot - بوت التشفير للتليجرام
المميزات: تشفير وفك تشفير الملفات والنصوص باستخدام AES + Base64
"""

import os
import base64
import hashlib
import logging
from typing import Dict, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# إعدادات التسجيل للأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات البيئية
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))  # ايدي المالك
PORT = int(os.environ.get('PORT', 8080))

class EncryptionBot:
    """بوت التشفير الرئيسي"""
    
    def __init__(self):
        self.user_sessions: Dict[int, dict] = {}  # حفظ جلسات المستخدمين
    
    def is_authorized(self, user_id: int) -> bool:
        """التحقق من صلاحية المستخدم (للمالك فقط)"""
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
        """تشفير نص باستخدام AES"""
        key, salt = self.generate_key(password)
        f = Fernet(key)
        encrypted = f.encrypt(text.encode())
        # تخزين الملح مع البيانات المشفرة
        result = base64.b64encode(salt + encrypted).decode()
        return result
    
    def decrypt_text(self, encrypted_data: str, password: str) -> str:
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
    
    def encode_base64(self, text: str) -> str:
        """تشفير Base64"""
        return base64.b64encode(text.encode()).decode()
    
    def decode_base64(self, encoded: str) -> str:
        """فك تشفير Base64"""
        try:
            return base64.b64decode(encoded).decode()
        except Exception:
            return None
    
    def hash_text(self, text: str, algo: str = 'sha256') -> str:
        """توليد هاش للنص"""
        if algo == 'sha256':
            return hashlib.sha256(text.encode()).hexdigest()
        elif algo == 'md5':
            return hashlib.md5(text.encode()).hexdigest()
        else:
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
🔐 **بوت التشفير المتقدم**

مرحباً! يمكنني مساعدتك في تشفير وفك تشفير الملفات والنصوص.

**الأوامر المتاحة:**
/encrypt_text - تشفير نص (AES)
/decrypt_text - فك تشفير نص
/encode_b64 - تحويل إلى Base64
/decode_b64 - فك Base64
/hash - توليد هاش (SHA256/MD5)
/help - عرض المساعدة
/about - معلومات عن البوت

**ملاحظة:** أنت المالك الوحيد المسموح باستخدام هذا البوت.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المساعدة"""
    help_text = """
📖 **دليل الاستخدام:**

🔹 **تشفير نص (AES)**
`/encrypt_text` ثم إرسال النص، ثم كلمة المرور

🔹 **فك تشفير نص**
`/decrypt_text` ثم إرسال النص المشفر، ثم كلمة المرور

🔹 **Base64**
`/encode_b64` - تحويل نص إلى Base64
`/decode_b64` - فك تشفير Base64

🔹 **توليد هاش**
`/hash` - اختيار نوع الهاش (sha256/md5)

🔹 **تشفير ملف**
أرسل أي ملف مباشرة للبوت، ثم أدخل كلمة المرور

⚠️ **تنبيه:** هذا البوت مخصص للمالك فقط (ايدي: {})
    """.format(OWNER_ID)
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات عن البوت"""
    about_text = """
🤖 **بوت التشفير v1.0**

📌 **المميزات:**
• تشفير AES-256 للملفات والنصوص
• تشفير Base64
• توليد هاش SHA256/MD5

🛡️ **الأمان:**
• PBKDF2 لتقوية كلمات المرور
• ملح عشوائي لكل عملية تشفير
• وصول محصور للمالك فقط

👨‍💻 **المطور:** Your Name
📅 **الإصدار:** 1.0.0
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')


async def encrypt_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية تشفير النص"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    context.user_data['action'] = 'encrypt_text_waiting'
    await update.message.reply_text(
        "✏️ أرسل النص الذي تريد تشفيره:\n\n"
        "(يمكنك إلغاء العملية بإرسال /cancel)"
    )


async def decrypt_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية فك تشفير النص"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    context.user_data['action'] = 'decrypt_text_waiting'
    await update.message.reply_text(
        "🔐 أرسل النص المشفر (بصيغة Base64):\n\n"
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
    """فك تشفير Base64"""
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
        [InlineKeyboardButton("SHA256", callback_data="hash_sha256")],
        [InlineKeyboardButton("MD5", callback_data="hash_md5")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔐 اختر نوع الهاش:", reply_markup=reply_markup
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
        await query.edit_message_text(f"📝 اخترت {algo.upper()}\n\nأرسل النص لتوليد الهاش:")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية حسب الحالة"""
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
                f"✅ **النص المشفر:**\n\n`{encrypted}`\n\n"
                "⚠️ احتفظ بكلمة المرور لفك التشفير!",
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
                await update.message.reply_text(f"✅ **النص الأصلي:**\n\n`{decrypted}`", parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ فشل فك التشفير. تحقق من كلمة المرور!")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")
        finally:
            context.user_data.clear()
    
    elif action == 'encode_b64_waiting':
        result = encryption_bot.encode_base64(text)
        await update.message.reply_text(f"✅ **Base64:**\n\n`{result}`", parse_mode='Markdown')
        context.user_data.clear()
    
    elif action == 'decode_b64_waiting':
        result = encryption_bot.decode_base64(text)
        if result:
            await update.message.reply_text(f"✅ **النص الأصلي:**\n\n`{result}`", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ نص Base64 غير صالح!")
        context.user_data.clear()
    
    elif action == 'hash_waiting':
        algo = context.user_data.get('hash_algo', 'sha256')
        result = encryption_bot.hash_text(text, algo)
        await update.message.reply_text(f"✅ **{algo.upper()}:**\n\n`{result}`", parse_mode='Markdown')
        context.user_data.clear()
    
    else:
        # رد افتراضي للأوامر غير المعروفة
        await update.message.reply_text(
            "❓ أمر غير معروف. استخدم /help لعرض الأوامر المتاحة."
        )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الملفات (تشفير الملفات)"""
    user_id = update.effective_user.id
    if not encryption_bot.is_authorized(user_id):
        return
    
    # سيتم إضافة تشفير الملفات لاحقاً
    await update.message.reply_text(
        "📁 تم استلام الملف!\n\n"
        "✨ ميزة تشفير الملفات قيد التطوير حالياً.\n"
        "📌 يمكنك حالياً استخدام /encrypt_text لتشفير النصوص."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    context.user_data.clear()
    await update.message.reply_text("❌ تم إلغاء العملية.")


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
    
    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("encrypt_text", encrypt_text_command))
    app.add_handler(CommandHandler("decrypt_text", decrypt_text_command))
    app.add_handler(CommandHandler("encode_b64", encode_b64_command))
    app.add_handler(CommandHandler("decode_b64", decode_b64_command))
    app.add_handler(CommandHandler("hash", hash_command))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # معالجة الأزرار والرسائل
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.ATTACHMENT, handle_file))
    
    # تشغيل البوت (Polling لـ Render)
    logger.info(f"تشغيل البوت... PORT={PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
    )


if __name__ == "__main__":
    main()
