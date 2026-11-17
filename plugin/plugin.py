# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
import os
import sys
import socket


def getIconPath():
    icon = "/usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/icon.png"
    if os.path.exists(icon) and os.path.getsize(icon) > 0:
        return icon
    return None


class Online4TechPanel(Screen):
    skin = """
    <screen name="Online4TechPanel" position="0,0" size="1920,1080" title="Online4Tech Command Dashboard v6.0" backgroundColor="#040b1c" flags="wfNoBorder">
        <!-- Top Header Bar -->
        <eLabel position="0,0" size="1920,105" backgroundColor="#081533" zPosition="-10" />
        <eLabel position="0,103" size="1920,3" backgroundColor="#00d4ff" zPosition="-5" />
        <widget name="logo" position="40,32" size="100,40" alphatest="blend" zPosition="5" />
        <eLabel text="ONLINE4TECH" position="155,15" size="420,45" font="Regular;36" foregroundColor="#ffffff" backgroundColor="#081533" transparent="1" zPosition="5" />
        <eLabel text="Dreambox • Vu+ • Enigma2" position="155,62" size="420,30" font="Regular;21" foregroundColor="#38bdf8" backgroundColor="#081533" transparent="1" zPosition="5" />

        <!-- Top Navigation Bar (Visual Tabs matching Dashboard) -->
        <eLabel text="الرئيسية    •    البلجنات    •    الأدوات    •    النسخ الاحتياطية    •    الأقسام    •    الإعدادات" position="580,35" size="880,40" font="Regular;23" halign="center" foregroundColor="#cbd5e1" backgroundColor="#081533" transparent="1" zPosition="5" />

        <!-- Top Right Search / Status Pill -->
        <eLabel position="1490,26" size="390,52" backgroundColor="#050e24" zPosition="-5" />
        <eLabel position="1490,26" size="390,2" backgroundColor="#0284c7" zPosition="-4" />
        <widget name="status_top" position="1505,36" size="360,34" font="Regular;22" halign="center" foregroundColor="#38bdf8" backgroundColor="#050e24" transparent="1" zPosition="5" />

        <!-- LEFT COLUMN: Categories Sidebar (x: 35..445) -->
        <eLabel position="35,125" size="410,920" backgroundColor="#091738" zPosition="-10" />
        <eLabel position="35,125" size="410,4" backgroundColor="#00d4ff" zPosition="-5" />
        <eLabel position="50,140" size="380,55" backgroundColor="#061029" zPosition="-8" />
        <eLabel text="الأقسام" position="65,148" size="350,42" font="Regular;30" halign="right" foregroundColor="#ffffff" backgroundColor="#061029" transparent="1" zPosition="5" />
        <eLabel position="50,202" size="380,2" backgroundColor="#1d4ed8" zPosition="-5" />

        <widget name="cat_menu" position="50,218" size="380,680" scrollbarMode="showNever" font="Regular;26" itemHeight="68" foregroundColor="#cbd5e1" backgroundColor="#091738" backgroundColorSelected="#0284c7" foregroundColorSelected="#ffffff" transparent="1" zPosition="5" />

        <eLabel position="50,915" size="380,110" backgroundColor="#061029" zPosition="-8" />
        <widget name="sys_mini" position="65,922" size="350,96" font="Regular;20" halign="center" foregroundColor="#94a3b8" backgroundColor="#061029" transparent="1" zPosition="5" />

        <!-- CENTER COLUMN: Commands & Plugins List (x: 470..1240) -->
        <eLabel position="470,125" size="770,920" backgroundColor="#091738" zPosition="-10" />
        <eLabel position="470,125" size="770,4" backgroundColor="#3b82f6" zPosition="-5" />
        <eLabel position="490,140" size="730,60" backgroundColor="#061029" zPosition="-8" />
        <eLabel text="[-_-]" position="505,148" size="70,42" font="Regular;26" halign="center" foregroundColor="#00d4ff" backgroundColor="#061029" transparent="1" zPosition="5" />
        <widget name="cat_header" position="585,148" size="420,42" font="Regular;30" halign="right" foregroundColor="#ffffff" backgroundColor="#061029" transparent="1" zPosition="5" />
        <widget name="cat_counter" position="1020,152" size="185,36" font="Regular;22" halign="center" foregroundColor="#38bdf8" backgroundColor="#061029" transparent="1" zPosition="5" />
        <eLabel position="490,208" size="730,2" backgroundColor="#1d4ed8" zPosition="-5" />

        <widget name="menu" position="490,222" size="730,795" scrollbarMode="showOnDemand" font="Regular;26" itemHeight="56" foregroundColor="#f8fafc" backgroundColor="#091738" backgroundColorSelected="#0284c7" foregroundColorSelected="#ffffff" transparent="1" zPosition="5" />

        <!-- RIGHT COLUMN: Item Details & Command Execution Box (x: 1265..1885) -->
        <eLabel position="1265,125" size="620,920" backgroundColor="#091738" zPosition="-10" />
        <eLabel position="1265,125" size="620,4" backgroundColor="#00d4ff" zPosition="-5" />
        <eLabel position="1285,140" size="580,55" backgroundColor="#061029" zPosition="-8" />
        <eLabel text="(i)  تفاصيل العنصر" position="1300,148" size="550,42" font="Regular;28" halign="right" foregroundColor="#ffffff" backgroundColor="#061029" transparent="1" zPosition="5" />
        <eLabel position="1285,202" size="580,2" backgroundColor="#1d4ed8" zPosition="-5" />

        <!-- Big Terminal Icon Box inside Details -->
        <eLabel position="1305,235" size="135,125" backgroundColor="#040b1c" zPosition="-8" />
        <eLabel position="1305,235" size="135,3" backgroundColor="#00d4ff" zPosition="-5" />
        <eLabel text=">_" position="1305,260" size="135,75" font="Regular;50" halign="center" foregroundColor="#00d4ff" backgroundColor="#040b1c" transparent="1" zPosition="5" />

        <!-- Selected Item Title & Category Subtitle -->
        <widget name="detail_title" position="1460,240" size="395,70" font="Regular;28" halign="right" foregroundColor="#ffffff" backgroundColor="#091738" transparent="1" zPosition="5" />
        <widget name="detail_cat" position="1460,315" size="395,38" font="Regular;23" halign="right" foregroundColor="#00d4ff" backgroundColor="#091738" transparent="1" zPosition="5" />

        <!-- Item Description Text -->
        <widget name="item_desc" position="1300,390" size="555,180" font="Regular;25" halign="right" foregroundColor="#cbd5e1" backgroundColor="#091738" transparent="1" zPosition="5" />

        <!-- Command Execution Box (أمر التنفيذ) -->
        <eLabel position="1290,590" size="570,220" backgroundColor="#061029" zPosition="-8" />
        <eLabel position="1290,590" size="570,2" backgroundColor="#1e3a8a" zPosition="-5" />
        <eLabel text="أمر التنفيذ" position="1680,605" size="160,36" font="Regular;24" halign="right" foregroundColor="#ffffff" backgroundColor="#061029" transparent="1" zPosition="5" />
        <eLabel position="1310,605" size="120,36" backgroundColor="#1d4ed8" zPosition="-6" />
        <eLabel text="جاهز للتنفيذ" position="1310,609" size="120,30" font="Regular;19" halign="center" foregroundColor="#ffffff" backgroundColor="#1d4ed8" transparent="1" zPosition="5" />

        <eLabel position="1310,655" size="530,135" backgroundColor="#030814" zPosition="-6" />
        <widget name="cmd_preview" position="1325,668" size="500,110" font="Regular;21" halign="left" foregroundColor="#38bdf8" backgroundColor="#030814" transparent="1" zPosition="5" />

        <!-- Action Buttons inside Right Column (Matching Dashboard Buttons) -->
        <!-- Green Button: Direct Run -->
        <eLabel position="1290,840" size="275,75" backgroundColor="#15803d" zPosition="-8" />
        <ePixmap pixmap="buttons/green.png" position="1305,860" size="35,35" alphatest="on" zPosition="5" />
        <widget name="key_green" position="1345,858" size="210,40" font="Regular;24" halign="center" foregroundColor="#ffffff" backgroundColor="#15803d" transparent="1" zPosition="5" />

        <!-- Blue Button: Cloud / Repo -->
        <eLabel position="1585,840" size="275,75" backgroundColor="#1d4ed8" zPosition="-8" />
        <ePixmap pixmap="buttons/blue.png" position="1600,860" size="35,35" alphatest="on" zPosition="5" />
        <widget name="key_blue" position="1640,858" size="210,40" font="Regular;24" halign="center" foregroundColor="#ffffff" backgroundColor="#1d4ed8" transparent="1" zPosition="5" />

        <!-- Yellow Button: Restart GUI -->
        <eLabel position="1290,935" size="275,75" backgroundColor="#a16207" zPosition="-8" />
        <ePixmap pixmap="buttons/yellow.png" position="1305,955" size="35,35" alphatest="on" zPosition="5" />
        <widget name="key_yellow" position="1345,953" size="210,40" font="Regular;24" halign="center" foregroundColor="#ffffff" backgroundColor="#a16207" transparent="1" zPosition="5" />

        <!-- Red Button: Exit -->
        <eLabel position="1585,935" size="275,75" backgroundColor="#b91c1c" zPosition="-8" />
        <ePixmap pixmap="buttons/red.png" position="1600,955" size="35,35" alphatest="on" zPosition="5" />
        <widget name="key_red" position="1640,953" size="210,40" font="Regular;24" halign="center" foregroundColor="#ffffff" backgroundColor="#b91c1c" transparent="1" zPosition="5" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.github_base = "https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/"

        # Format: ("Display Name", "Direct Shell Command", ask_restart_bool, "Arabic Description")
        self.categories = [
            (">_  أوامر النظام", [
                ("show system info", "uname -a && echo '' && cat /etc/issue && echo '' && free -m && echo '' && df -h", False, "عرض معلومات النظام الأساسية مثل النسخة والذاكرة والمعالج والمساحة."),
                ("uptime", "uptime", False, "عرض مدة تشغيل الريسفر المتواصلة منذ آخر إعادة تشغيل."),
                ("reboot now", "reboot", False, "إعادة تشغيل الريسفر بالكامل فوراً (Full Reboot)."),
                ("shutdown", "init 0", False, "إيقاف تشغيل الريسفر بالكامل (Deep Standby / Shutdown)."),
                ("mount", "mount", False, "عرض جميع وحدات التخزين المربوطة بالنظام (HDD / USB / Network)."),
                ("umount /media/hdd", "umount /media/hdd 2>/dev/null || umount /media/usb 2>/dev/null || echo 'Nothing to unmount'", False, "فصل وحدة التخزين الخارجية بأمان قبل إزالتها."),
                ("df -h", "df -h", False, "عرض المساحة الكلية والمستخدمة والمتبقية في الفلاشة الداخلية والهارد."),
                ("free -m", "free -m", False, "عرض حالة الذاكرة العشوائية (RAM) بالميجابايت."),
                ("top (snapshot)", "top -b -n 1 | head -n 25", False, "عرض أكثر العمليات استهلاكاً للمعالج والذاكرة في الوقت الحالي."),
                ("ps aux", "ps aux || ps", False, "عرض قائمة بجميع العمليات والخدمات النشطة في الخلفية."),
                ("killall enigma2 (Restart GUI)", "killall -9 enigma2", False, "إعادة تشغيل واجهة Enigma2 الرسومية فوراً."),
                ("sync", "sync && echo 'Filesystem buffers synced successfully!'", False, "حفظ ومزامنة جميع البيانات المعلقة في الذاكرة إلى وحدة التخزين."),
                ("date", "date", False, "عرض التاريخ والوقت الحاليين للنظام."),
                ("hwclock", "hwclock -r 2>/dev/null || date", False, "فحص توقيت الساعة الداخلية للهاردوير."),
                ("cat /proc/version", "cat /proc/version && echo '' && cat /proc/cpuinfo | head -n 20", False, "عرض إصدار نواة لينكس (Kernel) وتفاصيل معالج الريسفر.")
            ]),
            ("أوامر الشبكات", [
                ("show network info (ifconfig)", "ip addr 2>/dev/null || ifconfig", False, "عرض عنوان الـ IP الداخلي وبطاقات الشبكة المتصلة (LAN / WiFi)."),
                ("ping google dns (8.8.8.8)", "ping -c 4 8.8.8.8", False, "اختبار سرعة واستقرار الاتصال بالإنترنت عبر خوادم جوجل."),
                ("ping github server", "ping -c 4 raw.githubusercontent.com", False, "اختبار الاتصال المباشر بمستودع Online4Tech على GitHub."),
                ("netstat active ports", "netstat -tulnp 2>/dev/null || netstat -tuln", False, "عرض المنافذ المفتوحة والاتصالات النشطة على الريسفر."),
                ("restart network service", "/etc/init.d/networking restart && echo 'Network restarted!'", False, "إعادة تشغيل خدمة الشبكة وتجديد عنوان الـ IP."),
                ("show public IP & ISP", "wget -qO- http://ip-api.com/line?fields=query,country,isp || echo 'Offline'", False, "عرض الـ IP الخارجي والدولة ومزود خدمة الإنترنت.")
            ]),
            ("أوامر القنوات", [
                ("تحديث ملف قنوات Online4Tech", "wget -q --no-check-certificate -O /tmp/ch.sh '" + self.github_base + "update_channels.sh' && chmod 755 /tmp/ch.sh && sh /tmp/ch.sh", True, "تحميل وتثبيت أحدث ملف قنوات متحرك ونايل سات من مستودع Online4Tech."),
                ("reload bouquets & channels", "wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 && echo 'Channels Reloaded!'", False, "تحديث وإعادة قراءة ملفات القنوات والباقات بدون إعادة تشغيل الريسفر."),
                ("تثبيت بيكونات Chocholousek", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/ChocholousekPicons/main/installer.sh -O - | /bin/sh", True, "تثبيت بلجن تحميل وتحديث شعارات القنوات (Picons) لجميع الأقمار."),
                ("تثبيت البيكون الافتراضي O4T", "wget -q --no-check-certificate -O /usr/share/enigma2/picon_default.png 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/picon_default.png' && echo 'Default Picon Updated!'", True, "تركيب شعار Online4Tech كبيكون افتراضي للقنوات."),
                ("تثبيت وتحديث EPGImport", "opkg update && opkg install enigma2-plugin-extensions-epgimport", True, "تثبيت أداة جلب الدليل الإلكتروني للبرامج والقنوات.")
            ]),
            ("أوامر التحديث", [
                ("opkg update (تحديث الفيدات)", "opkg update", False, "تحديث قوائم الحزم والمستودعات الخاصة بصورة الريسفر."),
                ("opkg upgrade (ترقية النظام)", "opkg update && opkg upgrade", True, "ترقية حزم النظام والبلجنات المثبتة إلى أحدث إصدار."),
                ("تحديث مفاتيح SoftCam.Key", "mkdir -p /usr/keys /etc/tuxbox/config && wget -q --no-check-certificate -O /usr/keys/SoftCam.Key 'https://raw.githubusercontent.com/MOHAMED19OS/SoftCam_Emu/main/SoftCam.Key' && cp -f /usr/keys/SoftCam.Key /etc/tuxbox/config/SoftCam.Key && echo 'SoftCam.Key Updated!'", False, "تحديث أحدث شفرات BISS و PowerVU تلقائياً."),
                ("تحديث لوحة Online4Tech Panel", "wget -q --no-check-certificate -O /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/plugin.py 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/plugin/plugin.py' && echo 'Online4Tech Panel Updated!'", True, "جلب أحدث إصدار من لوحة تحكم Online4Tech مباشرة من GitHub."),
                ("تثبيت ServiceApp + Exteplayer3", "opkg update && opkg install ffmpeg exteplayer3 gstplayer enigma2-plugin-systemplugins-serviceapp", True, "تحديث مشغلات الميديا والـ IPTV لمنع التقطيع.")
            ]),
            ("أوامر الصيانة", [
                ("تنظيف الرام والكاش (Drop Cache)", "sync && echo 3 > /proc/sys/vm/drop_caches && rm -rf /tmp/*.ipk /tmp/*.tar.gz && free -m", False, "تفريغ الذاكرة العشوائية ومسح الملفات المؤقتة لتسريع الجهاز."),
                ("إعادة تشغيل الإيمو OSCam / NCam", "killall -9 oscam ncam 2>/dev/null; sleep 1; /etc/init.d/softcam restart 2>/dev/null || /usr/bin/oscam -b 2>/dev/null; echo 'Emulator Restarted!'", False, "إعادة تشغيل محاكي الشيرنج لتنشيط السيرفرات والقنوات المشفرة."),
                ("تثبيت محاكي OSCam-icam الحديث", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/OsCam_emu/main/installer.sh -O - | /bin/sh", True, "تثبيت أحدث إصدار من محاكي OSCam الداعم لكافة الباقات."),
                ("تثبيت محاكي NCam الرسمي", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/Ncam_emu/main/installer.sh -O - | /bin/sh", True, "تثبيت محاكي NCam السريع والمستقر."),
                ("تثبيت بوت لوجو Online4Tech", "wget -q --no-check-certificate -O /tmp/b.sh '" + self.github_base + "bootlogo_online4tech.sh' && chmod 755 /tmp/b.sh && sh /tmp/b.sh", True, "تعيين شعار Online4Tech كشاشة إقلاع رسمية للريسفر.")
            ]),
            ("أوامر النسخ الاحتياطية", [
                ("نسخ احتياطي للقنوات على /hdd", "mkdir -p /media/hdd/backup_o4t && tar -czf /media/hdd/backup_o4t/channels_backup.tar.gz /etc/enigma2/*bouquet* /etc/enigma2/lamedb* /etc/enigma2/settings && echo 'Saved to /media/hdd/backup_o4t/channels_backup.tar.gz'", False, "حفظ نسخة احتياطية كاملة من ملف القنوات والإعدادات على الهارد."),
                ("استعادة القنوات من /hdd", "tar -xzf /media/hdd/backup_o4t/channels_backup.tar.gz -C / && wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 && echo 'Channels Restored!'", False, "استرجاع ملف القنوات المحفوظ مسبقاً على الهارد."),
                ("نسخ احتياطي لإعدادات الإيمو", "mkdir -p /media/hdd/backup_o4t && tar -czf /media/hdd/backup_o4t/emu_keys_backup.tar.gz /etc/tuxbox/config /usr/keys 2>/dev/null && echo 'Emulator configs backed up!'", False, "حفظ نسخة احتياطية من ملفات سيرفرات OSCam / NCam والشفرات."),
                ("استعادة إعدادات الإيمو", "tar -xzf /media/hdd/backup_o4t/emu_keys_backup.tar.gz -C / && echo 'Emulator configs restored!'", False, "استرجاع ملفات السيرفرات والشفرات المحفوظة.")
            ]),
            ("أوامر الإصلاح", [
                ("إصلاح الحزم المعلقة (opkg configure)", "opkg configure && opkg update", False, "إصلاح مشاكل توقف مدير الحزم opkg عن تثبيت الإضافات."),
                ("فحص وإصلاح أخطاء الشبكة (DNS Fix)", "echo -e 'nameserver 8.8.8.8\nnameserver 1.1.1.1' > /etc/resolv.conf && echo 'DNS Fixed to 8.8.8.8 & 1.1.1.1!'", False, "ضبط خوادم DNS على جوجل وكلاودفلير لحل مشكلة انقطاع السيرفرات والتحميل."),
                ("ضبط الوقت تلقائياً من الإنترنت", "ntpd -q -p pool.ntp.org 2>/dev/null || rdate -s time.nist.gov 2>/dev/null; date", False, "مزامنة وإصلاح ساعة وتاريخ الريسفر عبر الإنترنت لتشغيل الشيرنج والـ EPG."),
                ("إصلاح صلاحيات مجلد الإيمو (/usr/bin)", "chmod 755 /usr/bin/*cam* /etc/init.d/softcam* 2>/dev/null; echo 'Permissions 755 applied!'", False, "منح تصاريح التشغيل 755 لملفات الإيمو المتوقفة.")
            ]),
            ("البلجنات والسكينات", [
                ("تثبيت لوحة التحكم AJPanel", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/AjPanel/main/installer.sh -O - | /bin/sh", True, "تثبيت أحدث إصدار من العملاق AJPanel."),
                ("تثبيت مشغل E2iPlayer + TSIPlayer", "wget -q --no-check-certificate http://www.e2iplayer.gitlab.io/online.sh -O - | /bin/sh", True, "تثبيت مشغل الأفلام والمسلسلات والمنصات أونلاين."),
                ("تثبيت MultiStalker Pro", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/MultiStalkerPro/main/installer.sh -O - | /bin/sh", True, "تثبيت مشغل بورتالات Stalker IPTV."),
                ("تثبيت XStreamity IPTV", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/XStreamity/main/installer.sh -O - | /bin/sh", True, "تثبيت مشغل اشتراكات Xtream Codes IPTV."),
                ("تثبيت الترجمة SubsSupport", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/SubsSupport/main/installer.sh -O - | /bin/sh", True, "تثبيت بلجن الترجمة العربية للأفلام والقنوات."),
                ("تثبيت جدول المباريات FootOnSat", "wget -q --no-check-certificate https://raw.githubusercontent.com/ziko-ZR1/FootOnsat/main/Download/install.sh -O - | /bin/sh", True, "عرض جدول المباريات اليومية والقنوات الناقلة."),
                ("تثبيت IPAudio Pro (التعليق العربي)", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/IPAudioPro/main/installer.sh -O - | /bin/sh", True, "تشغيل التعليق العربي على القنوات الرياضية."),
                ("تثبيت سكين Aglare FHD", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/Aglare-FHD/main/installer.sh -O - | /bin/sh", True, "تثبيت سكين Aglare Full HD العصري."),
                ("تثبيت سكين Nitro Advance FHD", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/Nitro-FHD/main/installer.sh -O - | /bin/sh", True, "تثبيت سكين Nitro FHD الرياضي السريع."),
                ("تثبيت سكين BlackSpirit FHD", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/BlackSpirit.FHD/main/installer.sh -O - | /bin/sh", True, "تثبيت سكين BlackSpirit الداكن الاحترافي.")
            ])
        ]

        self.current_cat = 0
        self.pending_restart = False

        first_cat_name, first_items = self.categories[0]
        first_item = first_items[0]

        self["logo"] = Pixmap()
        self["status_top"] = Label("البحث في... Online4Tech v6.0")
        self["sys_mini"] = Label(self.getSystemMiniInfo())

        self["cat_header"] = Label(first_cat_name)
        self["cat_counter"] = Label("جميع العناصر (%d)" % len(first_items))

        self["detail_title"] = Label(first_item[0])
        self["detail_cat"] = Label(first_cat_name)
        self["item_desc"] = Label(first_item[3])
        self["cmd_preview"] = Label(first_item[1])

        self["cat_menu"] = MenuList([c[0] for c in self.categories])
        self["menu"] = MenuList([x[0] for x in first_items])

        self["key_green"] = Label("تحميل / تنفيذ")
        self["key_blue"] = Label("المستودع")
        self["key_yellow"] = Label("إعادة الواجهة")
        self["key_red"] = Label("إغلاق")

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions"], {
            "ok": self.runSelectedTool,
            "green": self.runSelectedTool,
            "blue": self.checkRepoConnection,
            "yellow": self.confirmRestartGUI,
            "red": self.close,
            "cancel": self.close,
            "up": self.keyUp,
            "down": self.keyDown,
            "left": self.prevCategory,
            "right": self.nextCategory,
            "nextBouquet": self.nextCategory,
            "prevBouquet": self.prevCategory
        }, -1)

        self.onLayoutFinish.append(self.initUI)

    def initUI(self):
        icon = getIconPath()
        if icon and self["logo"].instance:
            self["logo"].instance.setPixmapFromFile(icon)
        try:
            self["cat_menu"].moveToIndex(0)
            self["menu"].moveToIndex(0)
        except Exception:
            pass

    def getSystemMiniInfo(self):
        py_ver = "%d.%d" % (sys.version_info[0], sys.version_info[1])
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "Offline"
        return "IP: %s  |  Python: %s\nأسهم يمين/يسار لتغيير القسم\nزر OK أو الأخضر للتنفيذ الفوري" % (ip, py_ver)

    def loadCategory(self, cat_idx):
        self.current_cat = cat_idx
        self["cat_menu"].moveToIndex(cat_idx)
        cat_name, items = self.categories[cat_idx]
        self["cat_header"].setText(cat_name)
        self["cat_counter"].setText("جميع العناصر (%d)" % len(items))
        self["menu"].setList([x[0] for x in items])
        self["menu"].moveToIndex(0)
        self.updateDescription()

    def updateDescription(self):
        cat_name, items = self.categories[self.current_cat]
        idx = self["menu"].getSelectedIndex()
        if 0 <= idx < len(items):
            title, cmd_str, _, desc = items[idx]
            self["detail_title"].setText(title)
            self["detail_cat"].setText(cat_name)
            self["item_desc"].setText(desc)
            self["cmd_preview"].setText(cmd_str[:110])

    def keyUp(self):
        self["menu"].up()
        self.updateDescription()

    def keyDown(self):
        self["menu"].down()
        self.updateDescription()

    def nextCategory(self):
        nxt = (self.current_cat + 1) % len(self.categories)
        self.loadCategory(nxt)

    def prevCategory(self):
        prv = (self.current_cat - 1) % len(self.categories)
        self.loadCategory(prv)

    def runSelectedTool(self):
        _, items = self.categories[self.current_cat]
        idx = self["menu"].getSelectedIndex()
        if 0 <= idx < len(items):
            name, cmd_str, restart_flag, _ = items[idx]
            self.pending_restart = restart_flag
            self.session.openWithCallback(self.onToolFinished, Console, title="Online4Tech - " + name, cmdlist=[cmd_str])

    def checkRepoConnection(self):
        cmd = "echo 'Checking Online4Tech GitHub Repository...' && ping -c 2 raw.githubusercontent.com && echo 'Repository Status: ONLINE (https://github.com/online4tech/Chanal-List)'"
        self.session.open(Console, title="Online4Tech GitHub Cloud Status", cmdlist=[cmd])

    def onToolFinished(self, result=None):
        self["sys_mini"].setText(self.getSystemMiniInfo())
        if self.pending_restart:
            self.session.openWithCallback(
                self.restartCallback,
                MessageBox,
                "تم تنفيذ العملية بنجاح! هل تريد إعادة تشغيل واجهة Enigma2 الآن؟",
                MessageBox.TYPE_YESNO
            )

    def confirmRestartGUI(self):
        self.session.openWithCallback(self.restartCallback, MessageBox, "إعادة تشغيل واجهة Enigma2 الآن؟", MessageBox.TYPE_YESNO)

    def restartCallback(self, answer):
        if answer:
            os.system("killall -9 enigma2")


def main(session, **kwargs):
    session.open(Online4TechPanel)


def Plugins(**kwargs):
    icon_path = getIconPath()
    return [
        PluginDescriptor(
            name="Online4Tech Panel",
            description="Online4Tech Command Dashboard v6.0",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=LoadPixmap(icon_path) if icon_path else None,
            fnc=main
        )
    ]
