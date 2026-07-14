"""
نظام الإشعارات التلقائية
Automated Notification System
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from pathlib import Path


class NotificationType(Enum):
    """أنواع الإشعارات"""
    ATTENDANCE_REMINDER = "تذكير بالحضور"
    TRAINING_REMINDER = "تذكير بالتدريب"
    PERFORMANCE_ALERT = "تنبيه الأداء"
    PAYMENT_DUE = "موعد الدفع"
    ACHIEVEMENT = "إنجاز جديد"
    LEVEL_UP = "ترقية مستوى"
    BIRTHDAY = "عيد ميلاد"
    ABSENCE_ALERT = "تنبيه غياب"
    COMPETITION = "منافسة"
    GENERAL = "عام"


class NotificationPriority(Enum):
    """أولوية الإشعار"""
    LOW = "منخفضة"
    MEDIUM = "متوسطة"
    HIGH = "عالية"
    URGENT = "عاجلة"


class NotificationChannel(Enum):
    """قنوات الإشعار"""
    EMAIL = "بريد إلكتروني"
    SMS = "رسالة نصية"
    APP = "التطبيق"
    PUSH = "إشعار فوري"
    WHATSAPP = "واتساب"


@dataclass
class Notification:
    """إشعار واحد"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    recipient_id: int
    recipient_name: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    channels: List[NotificationChannel] = field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    is_sent: bool = False
    is_read: bool = False
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """تحويل إلى dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'recipient_id': self.recipient_id,
            'recipient_name': self.recipient_name,
            'recipient_email': self.recipient_email,
            'recipient_phone': self.recipient_phone,
            'channels': [c.value for c in self.channels],
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'sent_time': self.sent_time.isoformat() if self.sent_time else None,
            'is_sent': self.is_sent,
            'is_read': self.is_read,
            'metadata': self.metadata
        }


class NotificationManager:
    """مدير الإشعارات"""

    def __init__(self, storage_path: str = "data/notifications"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.notifications: List[Notification] = []
        self.templates = self._load_templates()
        self._load_notifications()

    def _load_templates(self) -> Dict:
        """تحميل قوالب الإشعارات"""
        return {
            NotificationType.ATTENDANCE_REMINDER: {
                'title': '⏰ تذكير بالتدريب',
                'message': 'مرحباً {name}! لديك تدريب اليوم الساعة {time}. لا تنسى الحضور! 🎿'
            },
            NotificationType.TRAINING_REMINDER: {
                'title': '📅 تدريب قادم',
                'message': 'مرحباً {name}! لديك تدريب غداً الساعة {time}. استعد جيداً! 💪'
            },
            NotificationType.PERFORMANCE_ALERT: {
                'title': '📊 تنبيه الأداء',
                'message': 'مرحباً {name}! {performance_message}'
            },
            NotificationType.PAYMENT_DUE: {
                'title': '💳 موعد الدفع',
                'message': 'مرحباً {name}! حان موعد دفع الاشتراك. المبلغ: {amount} جنيه. 💰'
            },
            NotificationType.ACHIEVEMENT: {
                'title': '🏆 إنجاز جديد!',
                'message': 'مبروك {name}! حصلت على شارة "{badge_name}"! {icon}'
            },
            NotificationType.LEVEL_UP: {
                'title': '⭐ ترقية مستوى!',
                'message': 'رائع {name}! ارتقيت إلى مستوى "{level_name}"! استمر في التفوق! 🚀'
            },
            NotificationType.BIRTHDAY: {
                'title': '🎂 عيد ميلاد سعيد!',
                'message': 'كل سنة وأنت طيب {name}! نتمنى لك عاماً مليئاً بالإنجازات! 🎉'
            },
            NotificationType.ABSENCE_ALERT: {
                'title': '⚠️ تنبيه غياب',
                'message': 'مرحباً {name}! لاحظنا غيابك لمدة {days} أيام. نتمنى أن تكون بخير! 🤗'
            },
            NotificationType.COMPETITION: {
                'title': '🏅 منافسة جديدة',
                'message': 'مرحباً {name}! لديك منافسة قريباً في {date}. حظاً موفقاً! 🎯'
            },
            NotificationType.GENERAL: {
                'title': '📢 إشعار',
                'message': '{message}'
            }
        }

    def _load_notifications(self):
        """تحميل الإشعارات المخزنة"""
        notifications_file = self.storage_path / "notifications.json"
        if notifications_file.exists():
            with open(notifications_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # تحويل من dict إلى Notification
                    # (سيتم تحسينه لاحقاً)
                    pass

    def _save_notifications(self):
        """حفظ الإشعارات"""
        notifications_file = self.storage_path / "notifications.json"
        data = [n.to_dict() for n in self.notifications]
        with open(notifications_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_notification(
        self,
        notification_type: NotificationType,
        recipient_id: int,
        recipient_name: str,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None,
        scheduled_time: Optional[datetime] = None,
        **kwargs
    ) -> Notification:
        """إنشاء إشعار جديد"""

        if channels is None:
            channels = [NotificationChannel.APP]

        # توليد ID فريد
        notification_id = f"notif_{int(datetime.now().timestamp())}_{recipient_id}"

        # الحصول على القالب
        template = self.templates.get(notification_type, self.templates[NotificationType.GENERAL])

        # ملء القالب
        title = template['title']
        message = template['message'].format(
            name=recipient_name,
            **kwargs
        )

        notification = Notification(
            id=notification_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            channels=channels,
            scheduled_time=scheduled_time,
            metadata=kwargs
        )

        self.notifications.append(notification)
        self._save_notifications()

        return notification

    def send_notification(self, notification: Notification) -> bool:
        """إرسال إشعار"""
        success = False

        for channel in notification.channels:
            if channel == NotificationChannel.EMAIL:
                success = self._send_email(notification)
            elif channel == NotificationChannel.SMS:
                success = self._send_sms(notification)
            elif channel == NotificationChannel.APP:
                success = self._send_app_notification(notification)
            elif channel == NotificationChannel.PUSH:
                success = self._send_push_notification(notification)
            elif channel == NotificationChannel.WHATSAPP:
                success = self._send_whatsapp(notification)

        if success:
            notification.is_sent = True
            notification.sent_time = datetime.now()
            self._save_notifications()

        return success

    def _send_email(self, notification: Notification) -> bool:
        """إرسال بريد إلكتروني"""
        if not notification.recipient_email:
            return False

        try:
            # ملاحظة: يجب تكوين SMTP في الإعدادات
            # هذا مثال بسيط

            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.title
            msg['From'] = "noreply@skating-system.com"
            msg['To'] = notification.recipient_email

            # HTML content
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; direction: rtl;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                padding: 20px; border-radius: 10px; color: white;">
                        <h2>{notification.title}</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p style="font-size: 16px; line-height: 1.6;">
                            {notification.message}
                        </p>
                    </div>
                    <div style="text-align: center; color: #888; padding: 20px;">
                        <p>نظام تحليل أداء لاعبي التزلج</p>
                        <p>🎿 Skating Analysis System</p>
                    </div>
                </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            # ملاحظة: يجب تكوين SMTP server
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.starttls()
            # server.login("your_email@gmail.com", "your_password")
            # server.send_message(msg)
            # server.quit()

            # للتطوير: نحفظ البريد في ملف
            email_file = self.storage_path / f"email_{notification.id}.html"
            with open(email_file, 'w', encoding='utf-8') as f:
                f.write(html)

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def _send_sms(self, notification: Notification) -> bool:
        """إرسال رسالة نصية"""
        if not notification.recipient_phone:
            return False

        # ملاحظة: يتطلب خدمة SMS (Twilio, AWS SNS, etc.)
        # هذا مثال تجريبي

        sms_file = self.storage_path / f"sms_{notification.id}.txt"
        with open(sms_file, 'w', encoding='utf-8') as f:
            f.write(f"To: {notification.recipient_phone}\n")
            f.write(f"{notification.title}\n\n")
            f.write(f"{notification.message}\n")

        return True

    def _send_app_notification(self, notification: Notification) -> bool:
        """إرسال إشعار داخل التطبيق"""
        # حفظ في قاعدة البيانات أو ملف للعرض في التطبيق
        return True

    def _send_push_notification(self, notification: Notification) -> bool:
        """إرسال إشعار فوري (Push Notification)"""
        # يتطلب Firebase Cloud Messaging أو خدمة مشابهة
        return True

    def _send_whatsapp(self, notification: Notification) -> bool:
        """إرسال رسالة واتساب"""
        # يتطلب WhatsApp Business API
        return True

    def send_bulk_notifications(self, notifications: List[Notification]) -> Dict:
        """إرسال مجموعة إشعارات"""
        results = {
            'total': len(notifications),
            'sent': 0,
            'failed': 0
        }

        for notification in notifications:
            if self.send_notification(notification):
                results['sent'] += 1
            else:
                results['failed'] += 1

        return results

    def get_pending_notifications(self) -> List[Notification]:
        """الحصول على الإشعارات المعلقة"""
        return [n for n in self.notifications if not n.is_sent]

    def get_scheduled_notifications(self, before: datetime) -> List[Notification]:
        """الحصول على الإشعارات المجدولة قبل وقت معين"""
        return [
            n for n in self.notifications
            if not n.is_sent
            and n.scheduled_time
            and n.scheduled_time <= before
        ]

    def mark_as_read(self, notification_id: str):
        """تحديد الإشعار كمقروء"""
        for n in self.notifications:
            if n.id == notification_id:
                n.is_read = True
                self._save_notifications()
                break


class NotificationScheduler:
    """جدولة الإشعارات التلقائية"""

    def __init__(self, notification_manager: NotificationManager):
        self.manager = notification_manager

    def schedule_attendance_reminders(
        self,
        members_df: pd.DataFrame,
        training_times: Dict[str, str]
    ):
        """جدولة تذكير الحضور"""
        for _, member in members_df.iterrows():
            # مثال: تذكير قبل ساعة من التدريب
            for day, time in training_times.items():
                reminder_time = datetime.now() + timedelta(hours=1)

                self.manager.create_notification(
                    notification_type=NotificationType.ATTENDANCE_REMINDER,
                    recipient_id=member['id'],
                    recipient_name=member['name'],
                    recipient_email=member.get('email'),
                    priority=NotificationPriority.MEDIUM,
                    channels=[NotificationChannel.EMAIL, NotificationChannel.APP],
                    scheduled_time=reminder_time,
                    time=time
                )

    def check_absence_alerts(
        self,
        members_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
        absence_threshold: int = 7
    ):
        """فحص الغياب وإرسال تنبيهات"""
        for _, member in members_df.iterrows():
            member_attendance = attendance_df[
                attendance_df['member_id'] == member['id']
            ]

            if not member_attendance.empty:
                last_attendance = pd.to_datetime(member_attendance['date']).max()
                days_absent = (datetime.now() - last_attendance).days

                if days_absent >= absence_threshold:
                    self.manager.create_notification(
                        notification_type=NotificationType.ABSENCE_ALERT,
                        recipient_id=member['id'],
                        recipient_name=member['name'],
                        recipient_email=member.get('email'),
                        priority=NotificationPriority.HIGH,
                        channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
                        days=days_absent
                    )

    def check_birthdays(self, members_df: pd.DataFrame):
        """فحص أعياد الميلاد"""
        today = datetime.now()

        for _, member in members_df.iterrows():
            if 'birth_date' in member and pd.notna(member['birth_date']):
                birth_date = pd.to_datetime(member['birth_date'])

                # التحقق من عيد الميلاد اليوم
                if birth_date.month == today.month and birth_date.day == today.day:
                    self.manager.create_notification(
                        notification_type=NotificationType.BIRTHDAY,
                        recipient_id=member['id'],
                        recipient_name=member['name'],
                        recipient_email=member.get('email'),
                        priority=NotificationPriority.LOW,
                        channels=[NotificationChannel.EMAIL, NotificationChannel.APP]
                    )

    def send_achievement_notifications(
        self,
        member_id: int,
        member_name: str,
        member_email: str,
        badge_name: str,
        badge_icon: str
    ):
        """إرسال إشعار بالإنجاز"""
        self.manager.create_notification(
            notification_type=NotificationType.ACHIEVEMENT,
            recipient_id=member_id,
            recipient_name=member_name,
            recipient_email=member_email,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.APP, NotificationChannel.PUSH],
            badge_name=badge_name,
            icon=badge_icon
        )

    def send_level_up_notifications(
        self,
        member_id: int,
        member_name: str,
        member_email: str,
        level_name: str
    ):
        """إرسال إشعار بالترقية"""
        self.manager.create_notification(
            notification_type=NotificationType.LEVEL_UP,
            recipient_id=member_id,
            recipient_name=member_name,
            recipient_email=member_email,
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.APP, NotificationChannel.PUSH],
            level_name=level_name
        )


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مدير الإشعارات
    manager = NotificationManager()

    # إنشاء إشعار تذكير
    notification = manager.create_notification(
        notification_type=NotificationType.ATTENDANCE_REMINDER,
        recipient_id=1,
        recipient_name="محمد أحمد",
        recipient_email="mohamed@example.com",
        priority=NotificationPriority.MEDIUM,
        channels=[NotificationChannel.EMAIL, NotificationChannel.APP],
        time="5:00 مساءً"
    )

    # إرسال الإشعار
    manager.send_notification(notification)

    print(f"✅ تم إنشاء وإرسال الإشعار: {notification.id}")
