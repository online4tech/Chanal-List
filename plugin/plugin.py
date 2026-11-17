# -*- coding: utf-8 -*-
# Online4Tech Panel v8.0 — Enigma2 command dashboard
# Visual style: ElieSatPanel-like dark/gold theme (very dark background,
# dark cards, gold titles and selected rows, left system-info panel,
# right categories sidebar, bottom color-button bar, top clock/date bar).
# Auto-update: on panel open, a background thread (never blocks the UI)
# checks https://raw.githubusercontent.com/online4tech/Chanal-List/main/plugin/version.txt
# and offers to update when a newer version exists.
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from enigma2 import eTimer
import os
import sys
import socket
import threading
import time
import urllib.request

VERSION = "8.0"
VERSION_URL = "https://raw.githubusercontent.com/online4tech/Chanal-List/main/plugin/version.txt"
PLUGIN_URL = "https://raw.githubusercontent.com/online4tech/Chanal-List/main/plugin/plugin.py"
PLUGIN_DIR = "/usr/lib/enigma2/python/Plugins/Extensions/Online4Tech"


def getIconPath():
    icon = os.path.join(PLUGIN_DIR, "icon.png")
    if os.path.exists(icon) and os.path.getsize(icon) > 0:
        return icon
    return None


def _parseVersion(text):
    # "8.0" -> (8, 0); tolerates a leading "v" and trailing whitespace.
    try:
        text = text.strip().lstrip("vV")
        parts = []
        for chunk in text.split("."):
            parts.append(int(chunk))
        while len(parts) < 2:
            parts.append(0)
        return tuple(parts)
    except Exception:
        return None


def _isNewer(remote, local):
    r = _parseVersion(remote)
    l = _parseVersion(local)
    if r is None or l is None:
        return False
    return r > l


class Online4TechPanel(Screen):
    skin = """
    <screen name="Online4TechPanel" position="0,0" size="1920,1080" title="Online4Tech Command Dashboard v8.0" backgroundColor="#0d1117" flags="wfNoBorder">
        <!-- ===== Top bar: clock/date (left) — status pill (center) — gold title (right) ===== -->
        <widget name="clock" position="40,12" size="220,58" font="Regular;48" foregroundColor="#ffffff" backgroundColor="#0d1117" halign="left" transparent="1" zPosition="5" />
        <widget name="date" position="40,70" size="340,30" font="Regular;22" foregroundColor="#9aa0a6" backgroundColor="#0d1117" halign="left" transparent="1" zPosition="5" />
        <eLabel position="760,28" size="400,52" backgroundColor="#161b22" zPosition="-5" />
        <widget name="status_top" position="770,38" size="380,34" font="Regular;22" halign="center" foregroundColor="#f5c518" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <widget name="logo" position="1300,26" size="64,54" alphatest="blend" zPosition="5" />
        <eLabel text="Online4Tech" position="1370,10" size="510,56" font="Regular;44" foregroundColor="#f5c518" backgroundColor="#0d1117" halign="right" transparent="1" zPosition="5" />
        <eLabel text="Online4Tech | الإصدار 8.0" position="1370,66" size="510,32" font="Regular;22" foregroundColor="#9aa0a6" backgroundColor="#0d1117" halign="right" transparent="1" zPosition="5" />
        <eLabel position="0,106" size="1920,2" backgroundColor="#21262d" zPosition="-5" />

        <!-- ===== LEFT: system info panel ===== -->
        <eLabel position="35,122" size="410,866" backgroundColor="#161b22" zPosition="-10" />
        <eLabel position="35,122" size="410,4" backgroundColor="#f5c518" zPosition="-5" />
        <eLabel text="النظام" position="55,138" size="370,44" font="Regular;30" halign="center" foregroundColor="#f5c518" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="55,190" size="370,2" backgroundColor="#2a2f38" zPosition="-5" />
        <widget name="sys_info" position="55,205" size="370,640" font="Regular;25" halign="center" foregroundColor="#e6e6e6" backgroundColor="#161b22" transparent="1" zPosition="5" />

        <!-- ===== CENTER: commands list ===== -->
        <eLabel position="470,122" size="770,866" backgroundColor="#161b22" zPosition="-10" />
        <eLabel position="470,122" size="770,4" backgroundColor="#f5c518" zPosition="-5" />
        <widget name="cat_header" position="490,138" size="730,48" font="Regular;32" halign="center" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <widget name="cat_counter" position="490,190" size="730,30" font="Regular;22" halign="center" foregroundColor="#9aa0a6" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="490,228" size="730,2" backgroundColor="#2a2f38" zPosition="-5" />
        <widget name="menu" position="490,240" size="730,730" scrollbarMode="showOnDemand" font="Regular;26" itemHeight="62" foregroundColor="#e6e6e6" backgroundColor="#161b22" backgroundColorSelected="#26221a" foregroundColorSelected="#f5c518" transparent="1" zPosition="5" />

        <!-- ===== RIGHT: categories card (top) ===== -->
        <eLabel position="1265,122" size="620,420" backgroundColor="#161b22" zPosition="-10" />
        <eLabel position="1265,122" size="620,4" backgroundColor="#f5c518" zPosition="-5" />
        <eLabel text="الأقسام" position="1285,138" size="580,44" font="Regular;28" halign="center" foregroundColor="#f5c518" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1285,190" size="580,2" backgroundColor="#2a2f38" zPosition="-5" />
        <widget name="cat_menu" position="1285,200" size="580,320" scrollbarMode="showNever" font="Regular;24" itemHeight="40" foregroundColor="#cbd5e1" backgroundColor="#161b22" backgroundColorSelected="#26221a" foregroundColorSelected="#f5c518" transparent="1" zPosition="5" />

        <!-- ===== RIGHT: item details card (bottom) ===== -->
        <eLabel position="1265,558" size="620,430" backgroundColor="#161b22" zPosition="-10" />
        <eLabel position="1265,558" size="620,4" backgroundColor="#f5c518" zPosition="-5" />
        <eLabel text="تفاصيل العنصر" position="1285,572" size="580,40" font="Regular;26" halign="right" foregroundColor="#f5c518" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1285,618" size="580,2" backgroundColor="#2a2f38" zPosition="-5" />
        <widget name="detail_title" position="1285,628" size="580,36" font="Regular;26" halign="right" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <widget name="detail_cat" position="1285,666" size="580,30" font="Regular;22" halign="right" foregroundColor="#f5c518" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <widget name="item_desc" position="1285,700" size="580,92" font="Regular;22" halign="right" foregroundColor="#cbd5e1" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1295,798" size="130,32" backgroundColor="#f5c518" zPosition="-6" />
        <eLabel text="جاهز للتنفيذ" position="1295,800" size="130,28" font="Regular;19" halign="center" foregroundColor="#0d1117" backgroundColor="#f5c518" transparent="1" zPosition="5" />
        <eLabel text="أمر التنفيذ" position="1725,800" size="140,30" font="Regular;22" halign="right" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1285,838" size="580,130" backgroundColor="#0d1117" zPosition="-6" />
        <widget name="cmd_preview" position="1300,848" size="550,110" font="Regular;20" halign="left" foregroundColor="#f5c518" backgroundColor="#0d1117" transparent="1" zPosition="5" />

        <!-- ===== Bottom bar: colored buttons ===== -->
        <eLabel position="35,1002" size="1850,64" backgroundColor="#161b22" zPosition="-10" />
        <eLabel text="Online4Tech Panel v8.0" position="55,1018" size="320,34" font="Regular;24" halign="left" foregroundColor="#f5c518" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1845,1022" size="26,26" backgroundColor="#ff3b30" zPosition="5" />
        <eLabel text="إغلاق" position="1755,1018" size="85,34" font="Regular;24" halign="right" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1705,1022" size="26,26" backgroundColor="#34c759" zPosition="5" />
        <eLabel text="تحميل / تنفيذ" position="1545,1018" size="155,34" font="Regular;24" halign="right" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1495,1022" size="26,26" backgroundColor="#f5c518" zPosition="5" />
        <eLabel text="إعادة الواجهة" position="1345,1018" size="145,34" font="Regular;24" halign="right" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
        <eLabel position="1295,1022" size="26,26" backgroundColor="#0a84ff" zPosition="5" />
        <eLabel text="المستودع" position="1205,1018" size="85,34" font="Regular;24" halign="right" foregroundColor="#ffffff" backgroundColor="#161b22" transparent="1" zPosition="5" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.github_base = "https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/"

        # Format: ("Display Name", "Direct Shell Command", ask_restart_bool, "Arabic Description")
        self.categories = [
            ("أوامر النظام", [
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
                ("cat /proc/version", "cat /proc/version && echo '' && cat /proc/cpuinfo | head -n 20", False, "عرض إصدار نواة لينكس (Kernel) وتفاصيل معالج الريسفر."),
                ("3gmodemmanager-ALL Python", "wget https://dreambox4u.com/emilnabil237/plugins/3gmodemmanager/3gmodemmanager.sh -O - | /bin/sh", True, "تثبيت 3gmodemmanager-ALL Python."),
                ("arabic-language_for-egami-image", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/arabic-language_images/arabic-language_for-egami-image.sh -O - | /bin/sh", True, "ملف تعريب للصورة"),
                ("arabic-language_for-openatv-image", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/arabic-language_images/arabic-language_for-openatv-image.sh -O - | /bin/sh", True, "ملف تعريب للصورة"),
                ("arabic-language_for-openbh-image", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/arabic-language_images/arabic-language_for-openbh-image.sh -O - | /bin/sh", True, "ملف تعريب للصورة"),
                ("arabic-language_for-openhdf-image", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/arabic-language_images/arabic-language_for-openhdf-image.sh -O - | /bin/sh", True, "ملف تعريب للصورة"),
                ("arabic-language_for-openpli-image", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/arabic-language_images/arabic-language_for-openpli-image.sh -O - | /bin/sh", True, "ملف تعريب للصورة"),
                ("arabic-language_for-openvix-image", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/arabic-language_images/arabic-language_for-openvix-image.sh -O - | /bin/sh", True, "ملف تعريب للصورة"),
                ("AutomaticVolumeAdjustment-ALL Python", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/AutomaticVolumeAdjustment/AutomaticVolumeAdjustment.sh -O - | /bin/sh", True, "تثبيت AutomaticVolumeAdjustment-ALL Python."),
                ("CAM-abertis-astra-sm", "wget https://dreambox4u.com/emilnabil237/script/CAM-abertis-astra.sh -O - | /bin/sh", True, "تثبيت CAM-abertis-astra-sm."),
                ("Change-Password-To-root", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/scripts-servise/change-password-to-root.sh -O - | /bin/sh", True, "تثبيت Change-Password-To-root."),
                ("Delete-password", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/scripts-servise/delete-password.sh -O - | /bin/sh", True, "تثبيت Delete-password."),
                ("devicemanager-All Python", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/devicemanager.sh -O - | /bin/sh", True, "تثبيت devicemanager-All Python."),
                ("DNS AdGuard", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-adguard.sh -O - | /bin/sh", True, "تثبيت DNS AdGuard."),
                ("DNS Alternate", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-alternate.sh -O - | /bin/sh", True, "تثبيت DNS Alternate."),
                ("DNS CleanBrowsing", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-cleanbrowsing.sh -O - | /bin/sh", True, "تثبيت DNS CleanBrowsing."),
                ("DNS Cloudflare", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-cloudflare.sh -O - | /bin/sh", True, "تثبيت DNS Cloudflare."),
                ("DNS Comodo", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-comodo.sh -O - | /bin/sh", True, "تثبيت DNS Comodo."),
                ("DNS Control", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-control.sh -O - | /bin/sh", True, "تثبيت DNS Control."),
                ("DNS Google", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-google.sh -O - | /bin/sh", True, "تثبيت DNS Google."),
                ("DNS Open-Home", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-openhome.sh -O - | /bin/sh", True, "تثبيت DNS Open-Home."),
                ("DNS Quad9", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/dns/dns-quad9.sh -O - | /bin/sh", True, "تثبيت DNS Quad9."),
                ("EgamiBoot 10.5", "wget https://raw.githubusercontent.com/emil237/egamiboot/refs/heads/main/installer.sh -O - | /bin/sh", True, "تثبيت EgamiBoot 10.5."),
                ("EgamiBoot 10.6", "wget -q --no-check-certificate https://raw.githubusercontent.com/emil237/egamiboot/refs/heads/main/egamiboot-10.6.sh -O - | /bin/sh", True, "تثبيت EgamiBoot 10.6."),
                ("extnumberzap", "wget https://dreambox4u.com/emilnabil237/plugins/extnumberzap/extnumberzap.sh -O - | /bin/sh", True, "تثبيت extnumberzap."),
                ("Feed OpenPicons", "wget https://dreambox4u.com/emilnabil237/script/openpicons-feed.sh -O - | /bin/sh", True, "تثبيت Feed OpenPicons."),
                ("Fix Softcam Atv", "wget http://updates.mynonpublic.com/oea/feed -O - | /bin/sh", True, "تثبيت Fix Softcam Atv."),
                ("Fix Softcam OpenPli", "wget https://raw.githubusercontent.com/emil237/download-plugins/main/softcam-support-pli.sh -O - | /bin/sh", True, "تثبيت Fix Softcam OpenPli."),
                ("FIX-ipk-package-installation", "wget https://dreambox4u.com/emilnabil237/script/fix-ipk-package-installation.sh -O - | /bin/sh", True, "تثبيت FIX-ipk-package-installation."),
                ("Fix-Time-Shift-Openatv", "wget -O - -q https://feeds2.mynonpublic.com/preview-feed | bash", True, "تثبيت Fix-Time-Shift-Openatv."),
                ("Fix-Xtraevent-Download", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/fix-xtraevent-download.sh -O - | /bin/sh", True, "تثبيت Fix-Xtraevent-Download."),
                ("FORMAT_HDD_TO-Ext4", "wget https://raw.githubusercontent.com/emil237/scripts/refs/heads/main/format-hdd.sh -O - | /bin/sh", True, "تثبيت FORMAT_HDD_TO-Ext4."),
                ("Free Server Cccam", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/Free_Server.sh -O - | /bin/sh", True, "سيرفرات cccam مجانية"),
                ("Installer plugin from-tmp", "opkg install /tmp/*.ipk", True, "تحميل البلجنات من tmp"),
                ("mountmanager-All Python", "wget https://dreambox4u.com/emilnabil237/plugins/muntmanger/installer.sh -O - | /bin/sh", True, "تثبيت mountmanager-All Python."),
                ("Multiboot-FlashOnline", "wget https://raw.githubusercontent.com/emil237/download-plugins/main/multiboot-flashonline.sh -O - | /bin/sh", True, "تثبيت Multiboot-FlashOnline."),
                ("Neoboot 9.54 VIP", "wget https://raw.githubusercontent.com/emil237/neoboot_9.54/main/installer.sh -O - | /bin/sh", True, "تثبيت Neoboot 9.54 VIP."),
                ("Neoboot 9.58 VIP", "wget https://dreambox4u.com/emilnabil237/plugins/neoboot-v9.58/iNB.sh -O - | /bin/sh", True, "تثبيت Neoboot 9.58 VIP."),
                ("Neoboot 9.60 VIP", "wget https://dreambox4u.com/emilnabil237/plugins/neoboot-v9.60/iNB.sh -O - | /bin/sh", True, "تثبيت Neoboot 9.60 VIP."),
                ("Neoboot 9.65 Mod-ElSafty VIP", "wget https://raw.githubusercontent.com/emil237/neoboot_v9.65/main/iNB_9.65_mod-elsafty.sh -O - | /bin/sh", True, "تثبيت Neoboot 9.65 Mod-ElSafty VIP."),
                ("Neoboot 9.65 VIP", "wget https://dreambox4u.com/emilnabil237/plugins/neoboot-v9.65/iNB.sh -O - | /bin/sh", True, "تثبيت Neoboot 9.65 VIP."),
                ("OpenMultiboot 1.3", "wget https://raw.githubusercontent.com/emil237/openmultiboot/main/installer.sh -O - | /bin/sh", True, "تثبيت OpenMultiboot 1.3."),
                ("OpenMultiboot-E2turk", "wget https://raw.githubusercontent.com/e2TURK/omb-enhanced/main/install.sh -O - | /bin/sh", True, "تثبيت OpenMultiboot-E2turk."),
                ("Picons-Convert2Snp", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/picons-convert2snp.sh -O - | /bin/sh", True, "تثبيت Picons-Convert2Snp."),
                ("Remove-Cache", "rm -rf /var/cache/opkg/* && opkg update", True, "تثبيت Remove-Cache."),
                ("Repair-Inodes-From-Hdd", "wget https://raw.githubusercontent.com/emil237/scripts/refs/heads/main/repair-hdd.sh -O - | /bin/sh", True, "تثبيت Repair-Inodes-From-Hdd."),
                ("Script package", "wget https://raw.githubusercontent.com/emil237/ajpanel/refs/heads/main/script.sh -O - | /bin/sh", True, "تحميل حزمة السكريبتات"),
                ("Set_Time_NTP-Google", "wget https://dreambox4u.com/emilnabil237/script/set_time.sh -O - | /bin/sh", True, "تثبيت Set_Time_NTP-Google."),
                ("Setpasswd-ALL Python", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/setpasswd.sh -O - | /bin/sh", True, "تثبيت Setpasswd-ALL Python."),
                ("Signalfinder-ALL Python", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/signalfinder/signalfinder.sh -O - | /bin/sh", True, "تثبيت Signalfinder-ALL Python."),
                ("SoftwareManager-ALL Python", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/softwaremanager/softwaremanager.sh -O - | /bin/sh", True, "تثبيت SoftwareManager-ALL Python."),
                ("Super Script", "wget https://dreambox4u.com/emilnabil237/script/Super_Script.sh -O - | /bin/sh", True, "تحديث الصورة وتحميل بلجنات مهمة"),
                ("Timeshift Delay", "wget -qO - http://dreambox4u.com/mosadpro/scripts/timeshift-delay.sh | sh", True, "معلومات وأدوات مرتبطة بإعدادات الـ Timeshift وتقليل التأخير حسب الجهاز والصورة."),
                ("Ts-SatEditor-ALL Python", "wget https://dreambox4u.com/emilnabil237/plugins/ts-sateditor/ts-sateditor.sh -O - | /bin/sh", True, "تثبيت Ts-SatEditor-ALL Python."),
                ("Xmlupdate-ALL Python", "wget https://dreambox4u.com/emilnabil237/plugins/xmlupdate/xmlupdate.sh -O - | /bin/sh", True, "تثبيت Xmlupdate-ALL Python."),
                ("Zip2ipk", "wget http://dreambox4u.com/emilnabil237/script/zip2ipk.sh -O - | /bin/sh", True, "تثبيت Zip2ipk."),
                ("تحديث فهارس الحزم — DreamOS", "apt-get update", False, "تحديث قوائم الحزم في DreamOS دون ترقية الحزم المثبتة."),
                ("ترقية الحزم — DreamOS", "apt-get upgrade", True, "ترقية الحزم عبر apt في DreamOS. قد تغيّر مكونات النظام؛ استخدمها فقط عند توصية مطور الصورة وبعد نسخة احتياطية."),
                ("ترقية الحزم — OpenATV / Enigma2", "opkg upgrade", True, "ترقية حزم النظام عبر opkg. قد تؤدي ترقية الحزم عشوائياً إلى عدم استقرار الصورة أو تعارضات؛ استخدمها فقط عند توصية مطور الصورة وبعد نسخة ا..."),
                ("فحص القرص والرام والشبكة", "wget -q --no-check-certificate -O /tmp/check_net_disk.sh 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/check_net_disk.sh' && chmod 755 /tmp/check_net_disk.sh && sh /tmp/check_net_disk.sh", False, "فحص مساحة التخزين والرام واختبار الشبكة في أمر واحد."),
            ]),
            ("أوامر الشبكات", [
                ("show network info (ifconfig)", "ip addr 2>/dev/null || ifconfig", False, "عرض عنوان الـ IP الداخلي وبطاقات الشبكة المتصلة (LAN / WiFi)."),
                ("ping google dns (8.8.8.8)", "ping -c 4 8.8.8.8", False, "اختبار سرعة واستقرار الاتصال بالإنترنت عبر خوادم جوجل."),
                ("ping github server", "ping -c 4 raw.githubusercontent.com", False, "اختبار الاتصال المباشر بمستودع Online4Tech على GitHub."),
                ("netstat active ports", "netstat -tulnp 2>/dev/null || netstat -tuln", False, "عرض المنافذ المفتوحة والاتصالات النشطة على الريسفر."),
                ("restart network service", "/etc/init.d/networking restart && echo 'Network restarted!'", False, "إعادة تشغيل خدمة الشبكة وتجديد عنوان الـ IP."),
                ("show public IP & ISP", "wget -qO- http://ip-api.com/line?fields=query,country,isp || echo 'Offline'", False, "عرض الـ IP الخارجي والدولة ومزود خدمة الإنترنت."),
                ("OpenWebif", "opkg update && opkg install enigma2-plugin-extensions-openwebif", True, "واجهة ويب لإدارة الرسيفر ومشاهدة معلوماته والتحكم في بعض وظائفه عبر الشبكة."),
                ("Transmission", "opkg install transmission transmission-client python3-transmission-rpc xz python3-beautifulsoup4 && wget -q --no-check-certificate http://dreambox4u.com/dreamarabia/Transmission_e2/Transmission_e2.sh -O - | bash", True, "أدوات عميل Transmission وإدارة التنزيلات؛ يحتاج حزمًا إضافية قبل تشغيل السكريبت."),
            ]),
            ("أوامر القنوات", [
                ("تحديث ملف قنوات Online4Tech", "wget -q --no-check-certificate -O /tmp/ch.sh '" + self.github_base + "update_channels.sh' && chmod 755 /tmp/ch.sh && sh /tmp/ch.sh", True, "تحميل وتثبيت أحدث ملف قنوات متحرك ونايل سات من مستودع Online4Tech."),
                ("reload bouquets & channels", "wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 && echo 'Channels Reloaded!'", False, "تحديث وإعادة قراءة ملفات القنوات والباقات بدون إعادة تشغيل الريسفر."),
                ("تثبيت بيكونات Chocholousek", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/ChocholousekPicons/main/installer.sh -O - | /bin/sh", True, "تثبيت بلجن تحميل وتحديث شعارات القنوات (Picons) لجميع الأقمار."),
                ("تثبيت البيكون الافتراضي O4T", "wget -q --no-check-certificate -O /usr/share/enigma2/picon_default.png 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/picon_default.png' && echo 'Default Picon Updated!'", True, "تركيب شعار Online4Tech كبيكون افتراضي للقنوات."),
                ("تثبيت وتحديث EPGImport", "opkg update && opkg install enigma2-plugin-extensions-epgimport", True, "تثبيت أداة جلب الدليل الإلكتروني للبرامج والقنوات."),
                ("10sat-39E-28E-23E-19E-16E-13E-9E-4.8E-1.9E-0.8W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-10sat.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 10sat-39E-28E-23E-19E-16E-13E-9E-4.8E-1.9E-0.8W."),
                ("13sat-42E-39E-28E-23E-19E-16E-13E-9E-7E-4.8E-1.9E-0.8w-5w", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-13sat.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 13sat-42E-39E-28E-23E-19E-16E-13E-9E-7E-4.8E-1.9E-0.8w-5w."),
                ("16sat-42E-39E-28E-26E-23E-19E-16E-13E-10E-9E-7E-4.8E-1.9E-0.8w-4W-5w", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-16sat.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 16sat-42E-39E-28E-26E-23E-19E-16E-13E-10E-9E-7E-4.8E-1.9E-0.8w-4W-5w."),
                ("18sat-42E-39E-36E-33E-28E-26E-23E-19E-16E-13E-10E-9E-7E-4.8E-1.9E-0.8w-4w-5w", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-18sat.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 18sat-42E-39E-36E-33E-28E-26E-23E-19E-16E-13E-10E-9E-7E-4.8E-1.9E-0.8w-4w-5w."),
                ("1sat-19E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-1sat-19E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 1sat-19E."),
                ("2satA-19E-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-2satA-19E-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 2satA-19E-13E."),
                ("2satB-19E-16E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-2satB-19E-16E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 2satB-19E-16E."),
                ("3satA-9E-10E-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-3satA-9E-10E-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 3satA-9E-10E-13E."),
                ("3satB-19E-16E-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-3satB-19E-16E-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 3satB-19E-16E-13E."),
                ("4satA-28E-19E-13E-30W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-4satA-28E-19E-13E-30W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 4satA-28E-19E-13E-30W."),
                ("4satB-19E-16E-13E-0.8W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-4satB-19E-16E-13E-0.8W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 4satB-19E-16E-13E-0.8W."),
                ("5sat-19E-16E-13E-1.9E-0.8W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-5sat-19E-16E-13E-1.9E-0.8W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 5sat-19E-16E-13E-1.9E-0.8W."),
                ("6sat-23E-19E-16E-13E-1.9E-0.8W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-6sat-23E-19E-16E-13E-1.9E-0.8W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 6sat-23E-19E-16E-13E-1.9E-0.8W."),
                ("7sat-23E-19E-16E-13E-4.8E-1.9E-0.8W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-7sat-23E-19E-16E-13E-4.8E-1.9E-0.8W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 7sat-23E-19E-16E-13E-4.8E-1.9E-0.8W."),
                ("8sat-28E-23E-19E-16E-13E-4.8E-1.9E-0.8W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-8sat-28E-23E-19E-16E-13E-4.8E-1.9E-0.8W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 8sat-28E-23E-19E-16E-13E-4.8E-1.9E-0.8W."),
                ("9sat-28E-23E-19E-16E-13E-9E-1.9E-0.8W-5W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/ciefp-channels-e2/ciefp-E2-9sat-28E-23E-19E-16E-13E-9E-1.9E-0.8W-5W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات 9sat-28E-23E-19E-16E-13E-9E-1.9E-0.8W-5W."),
                ("ABS 3.0W", "wget https://dreambox4u.com/emilnabil237/picons/abs_3.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات ABS 3.0W."),
                ("ABS 75.0E", "wget https://dreambox4u.com/emilnabil237/picons/abs_75.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات ABS 75.0E."),
                ("Ahmed Romeh", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-romeh/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Ahmed Romeh."),
                ("Ahmed-Mosaad Modded", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/Channel-Omar2025/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Ahmed-Mosaad Modded."),
                ("Amos 4.0W", "wget https://dreambox4u.com/emilnabil237/picons/amos_4.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Amos 4.0W."),
                ("Arabsat 30.5E", "wget https://dreambox4u.com/emilnabil237/picons/arabsat_30.5e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Arabsat 30.5E."),
                ("Astra 19.2E", "wget https://dreambox4u.com/emilnabil237/picons/astra_19.2e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Astra 19.2E."),
                ("Astra 23.5E", "wget https://dreambox4u.com/emilnabil237/picons/astra_23.5e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Astra 23.5E."),
                ("Astra 28.2E", "wget https://dreambox4u.com/emilnabil237/picons/astra_28.2e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Astra 28.2E."),
                ("Astra 31.5E", "wget https://dreambox4u.com/emilnabil237/picons/astra_31.5e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Astra 31.5E."),
                ("Astra 4.8E", "wget https://dreambox4u.com/emilnabil237/picons/astra_4.8e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Astra 4.8E."),
                ("AutoTimer", "opkg update && opkg install enigma2-plugin-extensions-autotimer", True, "إنشاء تسجيلات تلقائية اعتمادًا على قواعد البحث في دليل البرامج الإلكتروني."),
                ("AzerSpace 45.0E", "wget https://dreambox4u.com/emilnabil237/picons/azerspace_45.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات AzerSpace 45.0E."),
                ("AzerSpace 46.0E", "wget https://dreambox4u.com/emilnabil237/picons/azerspace_46.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات AzerSpace 46.0E."),
                ("Badr 26.0E", "wget https://dreambox4u.com/emilnabil237/picons/badr_26.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Badr 26.0E."),
                ("Belintersat 51.5E", "wget https://dreambox4u.com/emilnabil237/picons/belintersat_51.5e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Belintersat 51.5E."),
                ("BouquetMakerXtream", "wget https://raw.githubusercontent.com/biko-73/BouquetMakerXtream/main/installer.sh -O - | /bin/sh", True, "أداة لإنشاء وترتيب الباقات والقنوات تلقائياً من مزودي Xtream بطريقة احترافية."),
                ("BulgariaSat 1.9E", "wget https://dreambox4u.com/emilnabil237/picons/bulgariasat_1.9e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات BulgariaSat 1.9E."),
                ("Chocholousek Picons", "wget https://github.com/s3n0/e2plugins/raw/master/ChocholousekPicons/online-setup -O - | /bin/sh", True, "تثبيت حزمة بيكونات Chocholousek Picons."),
                ("Ciefp — 6 أقمار", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/ciefp-channels-e2/ciefp-E2-6sat-23E-19E-16E-13E-1.9E-0.8W.sh | /bin/sh", True, "قائمة متعددة الأقمار تشمل 23°E و19.2°E و16°E و13°E و1.9°E و0.8°W. تأكد من إعدادات الـDiSEqC قبل التثبيت."),
                ("Ciefp — قمر واحد 19°E", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/ciefp-channels-e2/ciefp-E2-1sat-19E.sh | /bin/sh", True, "قائمة قنوات لقمر Astra 19.2°E. سكربت المصدر يحدّث ملفات إعدادات القنوات على الرسيفر؛ احتفظ بنسخة احتياطية قبل التنفيذ."),
                ("Ciefp — قمران 19°E + 13°E", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/ciefp-channels-e2/ciefp-E2-2satA-19E-13E.sh | /bin/sh", True, "قائمة قنوات لتجميعة Astra 19.2°E وHot Bird 13°E. قد تستبدل إعدادات القنوات الحالية؛ راجع توافق الأقمار والتوصيلات وخذ نسخة احتياطية."),
                ("ciefp-channels-e2-75e-34w", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/main/ciefp-channels-e2/ciefp-channels-e2-75e-34w.sh -O - | /bin/sh", True, "تثبيت ملف قنوات ciefp-channels-e2-75e-34w."),
                ("Elsafty-Tv-Radio-Steaming", "wget -q \"--no-check-certificate\" https://dreambox4u.com/emilnabil237/settings/elsafty/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Elsafty-Tv-Radio-Steaming."),
                ("EPG-khaled", "wget https://raw.githubusercontent.com/emilnabil/epg-khaled/main/EPG-khaled.sh -O - | /bin/sh", True, "دليل للقنوات"),
                ("Eshail 25.5E", "wget https://dreambox4u.com/emilnabil237/picons/eshail_25.5e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eshail 25.5E."),
                ("Eutelsat 10.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_10.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 10.0E."),
                ("Eutelsat 16.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_16.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 16.0E."),
                ("Eutelsat 21.6E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_21.6e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 21.6E."),
                ("Eutelsat 3.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_3.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 3.0E."),
                ("Eutelsat 36.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_36.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 36.0E."),
                ("Eutelsat 5.0W", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_5.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 5.0W."),
                ("Eutelsat 7.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_7.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 7.0E."),
                ("Eutelsat 70.0E-75.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_70.0e_74.9e_75.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 70.0E-75.0E."),
                ("Eutelsat 9.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat_9.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Eutelsat 9.0E."),
                ("Express 11.0W-14.0W", "wget https://dreambox4u.com/emilnabil237/picons/express_11.0w-14.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Express 11.0W-14.0W."),
                ("Express 14W", "wget https://dreambox4u.com/emilnabil237/picons/express_14w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Express 14W."),
                ("Express 53.0E", "wget https://dreambox4u.com/emilnabil237/picons/express_53.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Express 53.0E."),
                ("FIFA WORLD CUP 2026_By Hazem-Wahba", "wget -q \"--no-check-certificate\" https://dreambox4u.com/emilnabil237/channel/fifa-world/fifa-world.sh -O - | /bin/sh", True, "تثبيت ملف قنوات FIFA WORLD CUP 2026_By Hazem-Wahba."),
                ("Hazem-Wahba", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-hazem-wahba/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Hazem-Wahba."),
                ("Hellas-Sat 39.0E", "wget https://dreambox4u.com/emilnabil237/picons/hellas-sat_39.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Hellas-Sat 39.0E."),
                ("Hispasat 30.0W", "wget https://dreambox4u.com/emilnabil237/picons/hispasat_30.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Hispasat 30.0W."),
                ("Hotbird 13.0E", "wget https://dreambox4u.com/emilnabil237/picons/hotbird_13.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Hotbird 13.0E."),
                ("Intelsat 24.5W", "wget https://dreambox4u.com/emilnabil237/picons/intelsat_24.5w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 24.5W."),
                ("Intelsat 27.5W", "wget https://dreambox4u.com/emilnabil237/picons/intelsat_27.5w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 27.5W."),
                ("Intelsat 31.5W", "wget https://dreambox4u.com/emilnabil237/picons/intelsat_31.5w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 31.5W."),
                ("Intelsat 33.0E", "wget https://dreambox4u.com/emilnabil237/picons/eutelsat-intelsat_33.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 33.0E."),
                ("Intelsat 60.0E-68.0E", "wget https://dreambox4u.com/emilnabil237/picons/intelsat_60.0e_66.0e_68.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 60.0E-68.0E."),
                ("Intelsat 62.0E", "wget https://dreambox4u.com/emilnabil237/picons/intelsat_62.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 62.0E."),
                ("Intelsat 72.1E", "wget https://dreambox4u.com/emilnabil237/picons/Intelsat_72.1e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Intelsat 72.1E."),
                ("Khaled Ali", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-khaled/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Khaled Ali."),
                ("Modded By Emil Nabil", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-emil-nabil/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Modded By Emil Nabil."),
                ("Mohamed Goda", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-mohamed-goda/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Mohamed Goda."),
                ("Mohamed-Nasr", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-mnasr/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Mohamed-Nasr."),
                ("Morph883_0.8W-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_0.8W-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_0.8W-13E."),
                ("Morph883_0.8W-13E-19.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_0.8W-13E-19.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_0.8W-13E-19.2E."),
                ("Morph883_0.8W-13E-19.2E-28.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_0.8W-13E-19.2E-28.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_0.8W-13E-19.2E-28.2E."),
                ("Morph883_0.8W-4.8E-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_0.8W-4.8E-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_0.8W-4.8E-13E."),
                ("Morph883_13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E."),
                ("Morph883_13E-16E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-16E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-16E."),
                ("Morph883_13E-16E-19.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-16E-19.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-16E-19.2E."),
                ("Morph883_13E-19.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-19.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-19.2E."),
                ("Morph883_13E-19.2E-23.5E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-19.2E-23.5E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-19.2E-23.5E."),
                ("Morph883_13E-19.2E-23.5E-28.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-19.2E-23.5E-28.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-19.2E-23.5E-28.2E."),
                ("Morph883_13E-19.2E-28.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-19.2E-28.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-19.2E-28.2E."),
                ("Morph883_13E-19.2E-42E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-19.2E-42E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-19.2E-42E."),
                ("Morph883_13E-23.5E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-23.5E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-23.5E."),
                ("Morph883_13E-28.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-28.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-28.2E."),
                ("Morph883_13E-42E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_13E-42E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_13E-42E."),
                ("Morph883_30W-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_30W-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_30W-13E."),
                ("Morph883_30W-13E-19.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_30W-13E-19.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_30W-13E-19.2E."),
                ("Morph883_4.8E-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_4.8E-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_4.8E-13E."),
                ("Morph883_4.8E-13E-19.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_4.8E-13E-19.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_4.8E-13E-19.2E."),
                ("Morph883_9E-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_9E-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_9E-13E."),
                ("Morph883_9E-13E-19.2E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_9E-13E-19.2E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_9E-13E-19.2E."),
                ("Morph883_Motor", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_Motor.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_Motor."),
                ("Morph883_Settings", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/morpheus883-channels/E2_Morph883_Settings.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Morph883_Settings."),
                ("Morpheus883 — Hot Bird + Astra", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/morpheus883-channels/E2_Morph883_13E-19.2E.sh | /bin/sh", True, "قائمة قنوات متعددة الأقمار من Morpheus883 لتجميعة 13°E و19.2°E. السكربت ينشئ نسخة احتياطية من /etc/enigma2 قبل الاستبدال."),
                ("Morpheus883 — Motor Settings", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/morpheus883-channels/E2_Morph883_Motor.sh | /bin/sh", True, "إعدادات قنوات للموتور من Morpheus883. السكربت ينشئ نسخة احتياطية مؤرخة من /etc/enigma2 قبل نسخ الإعدادات الجديدة."),
                ("Morpheus883 — Settings", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/morpheus883-channels/E2_Morph883_Settings.sh | /bin/sh", True, "حزمة إعدادات قنوات عامة من Morpheus883. السكربت ينشئ نسخة احتياطية قبل تحديث ملفات /etc/enigma2."),
                ("Nilesat 7W-8W", "wget https://dreambox4u.com/emilnabil237/picons/nilesat/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Nilesat 7W-8W."),
                ("NSS 7 20.0W", "wget https://dreambox4u.com/emilnabil237/picons/nss7_20.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات NSS 7 20.0W."),
                ("PiconMaker", "wget \"https://dreambox4u.com/emilnabil237/plugins/PiconMaker/PiconMaker.sh\" -O - | /bin/sh", True, "إنشاء البيكونات"),
                ("Picons Other", "wget https://raw.githubusercontent.com/emil237/picon-other/main/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Picons Other."),
                ("Satelliweb_e2", "wget -q --no-check-certificate http://dreambox4u.com/dreamarabia/Satelliweb_e2/install_satelliweb.sh -O - | bash", True, "أداة مرتبطة ببيانات الأقمار/القنوات على Enigma2."),
                ("Sayed Refaey", "wget -q \"--no-check-certificate\" https://github.com/emilnabil/channels-sayed-refaey/raw/refs/heads/main/sayed-refaey.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Sayed Refaey."),
                ("SeriesPlugin", "opkg update && opkg install enigma2-plugin-extensions-seriesplugin", True, "مساعدة في التعرف على المسلسلات وربطها بمعلومات الحلقات حسب المصدر والإعدادات."),
                ("SES 4 22.0W", "wget https://dreambox4u.com/emilnabil237/picons/ses4_22.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات SES 4 22.0W."),
                ("SetPicon", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/setpicon/installer.sh -O - | /bin/sh", True, "أداة متخصصة لإدارة البيكونات وتحديد مسارها وتثبيتها تلقائياً."),
                ("Tarek Ashry", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/channel-tarek-ashry/main/installer.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Tarek Ashry."),
                ("Telstar 15.0W", "wget https://dreambox4u.com/emilnabil237/picons/telstar_15.0w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Telstar 15.0W."),
                ("Thor 0.8W", "wget https://dreambox4u.com/emilnabil237/picons/thor_0.8w/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Thor 0.8W."),
                ("Tuner_Backup_By-Emil-Nabil", "wget -q \"--no-check-certificate\" https://github.com/emilnabil/download-plugins/raw/refs/heads/main/restore-tuner-emil.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Tuner_Backup_By-Emil-Nabil."),
                ("Tuner_Backup_By-M-Goda", "wget -q \"--no-check-certificate\" https://github.com/emilnabil/download-plugins/raw/refs/heads/main/restore-tuner-goda.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Tuner_Backup_By-M-Goda."),
                ("TurkmenAlem 52.0E", "wget https://dreambox4u.com/emilnabil237/picons/turkmenalem_52.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات TurkmenAlem 52.0E."),
                ("Turksat 42.0E", "wget https://dreambox4u.com/emilnabil237/picons/turksat_42.0e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Turksat 42.0E."),
                ("Turksat 50.0E-57E", "wget https://dreambox4u.com/emilnabil237/picons/turksat_50.0e_56.0e_57e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Turksat 50.0E-57E."),
                ("Vhaninbal-Dual-13-19E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Dual-13-19E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Dual-13-19E."),
                ("Vhaninbal-Dual-DTT-Campania", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Dual-DTT-Campania.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Dual-DTT-Campania."),
                ("Vhaninbal-Dual-DTT-Italia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Dual-DTT-Italia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Dual-DTT-Italia."),
                ("Vhaninbal-Dual-DTT-Lazio", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Dual-DTT-Lazio.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Dual-DTT-Lazio."),
                ("Vhaninbal-Dual-DTT-Lombardia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Dual-DTT-Lombardia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Dual-DTT-Lombardia."),
                ("Vhaninbal-Dual-DTT-Piemonte", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Dual-DTT-Piemonte.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Dual-DTT-Piemonte."),
                ("Vhaninbal-HotBird-13E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-HotBird-13E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-HotBird-13E."),
                ("Vhaninbal-HotBird-DTT-Campania", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-HotBird-DTT-Campania.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-HotBird-DTT-Campania."),
                ("Vhaninbal-HotBird-DTT-Italia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-HotBird-DTT-Italia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-HotBird-DTT-Italia."),
                ("Vhaninbal-HotBird-DTT-Lazio", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-HotBird-DTT-Lazio.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-HotBird-DTT-Lazio."),
                ("Vhaninbal-HotBird-DTT-Lombardia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-HotBird-DTT-Lombardia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-HotBird-DTT-Lombardia."),
                ("Vhaninbal-HotBird-DTT-Piemonte", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-HotBird-DTT-Piemonte.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-HotBird-DTT-Piemonte."),
                ("Vhaninbal-Motor-70E-45W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-70E-45W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-70E-45W."),
                ("Vhaninbal-Motor-DTT-Campania", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Campania.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Campania."),
                ("Vhaninbal-Motor-DTT-Italia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Italia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Italia."),
                ("Vhaninbal-Motor-DTT-Lazio", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Lazio.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Lazio."),
                ("Vhaninbal-Motor-DTT-Lombardia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Lombardia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Lombardia."),
                ("Vhaninbal-Motor-DTT-Piemonte", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Piemonte.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Piemonte."),
                ("Vhaninbal-Motor-DTT-Romagna", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Romagna.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Romagna."),
                ("Vhaninbal-Motor-DTT-Sardegna", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Sardegna.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Sardegna."),
                ("Vhaninbal-Motor-DTT-Sicilia", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Motor-DTT-Sicilia.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Motor-DTT-Sicilia."),
                ("Vhaninbal-Quadri-13-19-23-28E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Quadri-13-19-23-28E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Quadri-13-19-23-28E."),
                ("Vhaninbal-Quadri-13-19-5E-1W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Quadri-13-19-5E-1W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Quadri-13-19-5E-1W."),
                ("Vhaninbal-Quadri-13-19-9E-5W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Quadri-13-19-9E-5W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Quadri-13-19-9E-5W."),
                ("Vhaninbal-Quadri-9-13-16-19-23E", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Quadri-9-13-16-19-23E.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Quadri-9-13-16-19-23E."),
                ("Vhaninbal-Trial-13-19E-30W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Trial-13-19E-30W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Trial-13-19E-30W."),
                ("Vhaninbal-Trial-13-19E-5W", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/vanenbal-channels/Vhannibal-Trial-13-19E-5W.sh -O - | /bin/sh", True, "تثبيت ملف قنوات Vhaninbal-Trial-13-19E-5W."),
                ("Vhannibal — Dual 13°E + 19°E", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/vanenbal-channels/Vhannibal-Dual-13-19E.sh | /bin/sh", True, "قائمة Vhannibal لقمرين Hot Bird 13°E وAstra 19.2°E. راجع توافق إعدادات الأقمار قبل الاستبدال."),
                ("Vhannibal — Hot Bird 13°E", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/vanenbal-channels/Vhannibal-HotBird-13E.sh | /bin/sh", True, "قائمة Vhannibal لقمر Hot Bird 13°E. تنبيه: السكربت يحذف ملفات القنوات والراديو الحالية قبل نسخ الجديدة؛ خذ نسخة احتياطية أولاً."),
                ("Vhannibal — Motor 70°E إلى 45°W", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/vanenbal-channels/Vhannibal-Motor-70E-45W.sh | /bin/sh", True, "إعدادات Vhannibal للموتور عبر نطاق أقمار واسع. السكربت يحذف ملفات القنوات والراديو الحالية؛ تأكد من إعدادات الموتور وخذ نسخة احتياطية."),
                ("xtraEvent", "wget -q \"--no-check-certificate\" https://github.com/digiteng/xtra/raw/main/xtraEvent.sh -O - | /bin/sh", True, "إضافة لعرض أو معالجة بيانات الأحداث والبرامج بحسب مصدر المطوّر."),
                ("Yahsat 52.5E", "wget https://dreambox4u.com/emilnabil237/picons/alyahsat_52.5e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Yahsat 52.5E."),
                ("Yamal 54.9E", "wget https://dreambox4u.com/emilnabil237/picons/gsat-yamal_54.9e/installer.sh -O - | /bin/sh", True, "تثبيت حزمة بيكونات Yamal 54.9E."),
            ]),
            ("أوامر التحديث", [
                ("opkg update (تحديث الفيدات)", "opkg update", False, "تحديث قوائم الحزم والمستودعات الخاصة بصورة الريسفر."),
                ("opkg upgrade (ترقية النظام)", "opkg update && opkg upgrade", True, "ترقية حزم النظام والبلجنات المثبتة إلى أحدث إصدار."),
                ("تحديث مفاتيح SoftCam.Key", "mkdir -p /usr/keys /etc/tuxbox/config && wget -q --no-check-certificate -O /usr/keys/SoftCam.Key 'https://raw.githubusercontent.com/MOHAMED19OS/SoftCam_Emu/main/SoftCam.Key' && cp -f /usr/keys/SoftCam.Key /etc/tuxbox/config/SoftCam.Key && echo 'SoftCam.Key Updated!'", False, "تحديث أحدث شفرات BISS و PowerVU تلقائياً."),
                ("تحديث لوحة Online4Tech Panel", "wget -q --no-check-certificate -O /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/plugin.py 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/plugin/plugin.py' && echo 'Online4Tech Panel Updated!'", True, "جلب أحدث إصدار من لوحة تحكم Online4Tech مباشرة من GitHub."),
                ("تثبيت ServiceApp + Exteplayer3", "opkg update && opkg install ffmpeg exteplayer3 gstplayer enigma2-plugin-systemplugins-serviceapp", True, "تحديث مشغلات الميديا والـ IPTV لمنع التقطيع."),
                ("Curl", "opkg install curl", True, "أداة تحميل مهمة جداً"),
                ("Eliesat", "wget https://gitlab.com/eliesat/scripts/-/raw/main/feed/eliesat-feed.sh -O - | /bin/sh", True, "فيد اضافي للصورة"),
                ("Emil", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/FEED-emil-feed.sh -O - | /bin/sh", True, "فيد أضافي للصورة"),
                ("Jungle", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/FEED-jungle-feed.sh -O - | /bin/sh", True, "فيد أضافي للصورة"),
                ("Libraries_3.12.4", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-libraries-3.12.4.sh -O - | /bin/sh", True, "إضافة فيد Libraries_3.12.4 إلى الصورة."),
                ("Libraries_3.12.6", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-libraries-3.12.sh -O - | /bin/sh", True, "إضافة فيد Libraries_3.12.6 إلى الصورة."),
                ("Oe-alliance-Picons", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-oe-picons.sh -O - | /bin/sh", True, "فيد به بايكونات"),
                ("Oe-alliance-Settings", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-oe-settings.sh -O - | /bin/sh", True, "فيد به ملفات قنوات"),
                ("Openatv-Deval", "wget -O - -q https://feeds2.mynonpublic.com/devel-feed | bash", True, "فيد صورة openatv للمطورين"),
                ("OpenDroid-softcam", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-OpenDroid-softcam.sh -O - | /bin/sh", True, "اضافة سوفتكام لفيد الصورة"),
                ("OpenEight-softcam", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-OpenEight-softcam.sh -O - | /bin/sh", True, "اضافة سوفتكام لفيد الصورة"),
                ("OpenPicons", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-openpicons.sh -O - | /bin/sh", True, "فيد بايكونات"),
                ("Opkg Tools_1.4", "wget https://github.com/emil237/plugins/raw/refs/heads/main/opkg.sh -O - | /bin/sh", True, "حزمة مهمة للصورة"),
                ("Opkg Tools_1.5", "wget https://github.com/emil237/plugins/raw/refs/heads/main/opkg-tools_1.5.sh -O - | /bin/sh", True, "حزمة مهمة للصورة"),
                ("Softcams-Feed-Openatv", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-OpenAtv-softcam-ALL-Python.sh -O - | /bin/sh", True, "اضافة سوفتكام لفيد الصورة"),
                ("Softcams-Feed-Pure2", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-pure2-softcam.sh -O - | /bin/sh", True, "اضافة سوفتكام لفيد الصورة"),
                ("Tarek-Hanfy", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-Tarek.sh -O - | /bin/sh", True, "فيد اضافي للصورة"),
                ("TeamBlue-softcam", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/FEED-TeamBlue-softcam.sh -O - | /bin/sh", True, "اضافة سوتكام لفيد الصورة"),
                ("Update Enigma2 All Python", "wget https://raw.githubusercontent.com/emil237/updates-enigma/main/update-all-python.sh -O - | /bin/sh", True, "تحميل الحزم المهمة"),
                ("Update-Astra-sm Plugin", "wget -q \"--no-check-certificate\" https://github.com/emilnabil/download-plugins/raw/refs/heads/main/astra-sm/astra-sm.sh -O - | /bin/sh", True, "حزمة مهمة للبث المتعدد"),
                ("Update-Astra-sm-Config", "wget -q \"--no-check-certificate\" https://github.com/emilnabil/download-plugins/raw/refs/heads/main/astra-sm/update-abertis-astra.config.sh -O - | /bin/sh", True, "حزمة مهمة للبث المتعدد"),
                ("Updated-All-Dependencic", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/emil237/updates-enigma/main/update-all-python.sh -O - | /bin/sh", True, "تحميل الحزم المهمة"),
                ("UpdateSatellitesOealliance", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Satellites-Oealliance.sh -O - | /bin/sh", True, "تثبيت UpdateSatellitesOealliance."),
                ("UpdateSatellitesOpenPli", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/satellites-openpli.sh -O - | /bin/sh", True, "تثبيت UpdateSatellitesOpenPli."),
                ("Wget", "opkg install wget", True, "أداة تحميل مهمة جداً"),
            ]),
            ("أوامر الصيانة", [
                ("تنظيف الرام والكاش (Drop Cache)", "sync && echo 3 > /proc/sys/vm/drop_caches && rm -rf /tmp/*.ipk /tmp/*.tar.gz && free -m", False, "تفريغ الذاكرة العشوائية ومسح الملفات المؤقتة لتسريع الجهاز."),
                ("إعادة تشغيل الإيمو OSCam / NCam", "killall -9 oscam ncam 2>/dev/null; sleep 1; /etc/init.d/softcam restart 2>/dev/null || /usr/bin/oscam -b 2>/dev/null; echo 'Emulator Restarted!'", False, "إعادة تشغيل محاكي الشيرنج لتنشيط السيرفرات والقنوات المشفرة."),
                ("تثبيت محاكي OSCam-icam الحديث", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/OsCam_emu/main/installer.sh -O - | /bin/sh", True, "تثبيت أحدث إصدار من محاكي OSCam الداعم لكافة الباقات."),
                ("تثبيت محاكي NCam الرسمي", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/Ncam_emu/main/installer.sh -O - | /bin/sh", True, "تثبيت محاكي NCam السريع والمستقر."),
                ("تثبيت بوت لوجو Online4Tech", "wget -q --no-check-certificate -O /tmp/b.sh '" + self.github_base + "bootlogo_online4tech.sh' && chmod 755 /tmp/b.sh && sh /tmp/b.sh", True, "تعيين شعار Online4Tech كشاشة إقلاع رسمية للريسفر."),
                ("BootlogoSwapper Atv", "wget http://dreambox4u.com/emilnabil237/script/bootlogoswapper-Atv.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper Christmas", "wget -O - https://dreambox4u.com/emilnabil237/script/bootlogoswapper-christmas.sh | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper Egami", "wget http://dreambox4u.com/emilnabil237/script/bootLogoswapper-Egami.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper Eid-Aldha", "wget http://dreambox4u.com/emilnabil237/script/bootlogoswapper-Eid-Aldha.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper Kids", "wget http://dreambox4u.com/emilnabil237/script/bootlogoswapper-kids.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper OpenBH", "wget http://dreambox4u.com/emilnabil237/script/bootlogoswapper-OpenBH.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper OpenSpa", "wget http://dreambox4u.com/emilnabil237/script/BootLogoSwapper-openspa.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper OpenVix", "wget http://dreambox4u.com/emilnabil237/script/bootlogoswapper-OpenVix.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper Pli", "wget http://dreambox4u.com/emilnabil237/script/bootlogoswapper-pli.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper Ramadan", "wget http://dreambox4u.com/emilnabil237/script/bootlogo-swapper-ramadan.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper V2.1", "wget http://dreambox4u.com/emilnabil237/script/BootlogoSwapper_v2.1.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper V2.3", "wget http://dreambox4u.com/emilnabil237/script/BootlogoSwapper_v2.3.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("BootlogoSwapper-PURE2", "wget -O - http://dreambox4u.com/emilnabil237/script/bootLogoswapper-Pure2.sh | /bin/sh", True, "بوت لوجو متعدد"),
                ("EGAMI", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-egami/backup-egami.sh - - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("gosatplus-ncam", "wget https://dreambox4u.com/emilnabil237/emu/installer-gosatplus-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي gosatplus-ncam."),
                ("gosatplus-oscam", "wget https://dreambox4u.com/emilnabil237/emu/installer-gosatplus-oscam.sh -O - | /bin/sh", True, "تثبيت محاكي gosatplus-oscam."),
                ("gosatplus_v3_arm", "wget http://e2.gosatplus.com/Plugin/V3/arm-openpli-installer_py3_v3.sh -O - | /bin/sh", True, "تثبيت محاكي gosatplus_v3_arm."),
                ("gosatplus_v3_Fix", "wget http://e2.gosatplus.com/Plugin/V3/GosatPlusPluginFixPy.sh -O - | /bin/sh", True, "تثبيت محاكي gosatplus_v3_Fix."),
                ("gosatplus_v3_mips", "wget http://e2.gosatplus.com/Plugin/V3/mips-openpli-installer_py3_v3.sh -O - | /bin/sh", True, "تثبيت محاكي gosatplus_v3_mips."),
                ("Hold-flag-ncam", "wget https://dreambox4u.com/emilnabil237/script/Hold-flag-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي Hold-flag-ncam."),
                ("Hold-flag-Oscam", "wget https://dreambox4u.com/emilnabil237/script/Hold-flag-Oscam.sh -O - | /bin/sh", True, "تثبيت محاكي Hold-flag-Oscam."),
                ("Levi45 Emulator (IPK)", "wget -q --no-check-certificate -O /tmp/levi45-emulator.ipk 'https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/levi45emulator/enigma2-plugin-extensions-levi45emulator_all.ipk' && opkg install /tmp/levi45-emulator.ipk && rm -f /tmp/levi45-emulator.ipk", True, "حزمة IPK لإضافة Levi45 Emulator."),
                ("Ncam_v15.8", "wget https://dreambox4u.com/emilnabil237/emu/installer-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي Ncam_v15.8."),
                ("OpenATV", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-openatv/backup-openatv_7.6.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("OpenBH", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-openbh/backup-openbh.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("OpenDroid", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-opendroid/backup-opendroid.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("OpenPli Py2", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/Backup-openpli-py2/backup-openpli-py2.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("OpenPli Py3", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-openpli/backup-openpli.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("OpenSpa", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/Backup-OpenSpa/backup-openspa.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("OpenVix", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-openvix/backup-openvix.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("Oscam-11.726-By-lenuxsat", "wget https://dreambox4u.com/emilnabil237/emu/oscam-by-lenuxsat/installer.sh -O - | /bin/sh", True, "تثبيت محاكي Oscam-11.726-By-lenuxsat."),
                ("Oscam_By-Mohamed-Os", "wget https://dreambox4u.com/emilnabil237/emu/installer-oscam.sh -O - | /bin/sh", True, "تثبيت محاكي Oscam_By-Mohamed-Os."),
                ("oscamicam", "wget https://dreambox4u.com/emilnabil237/emu/installer-oscamicam.sh -O - | /bin/sh", True, "تثبيت محاكي oscamicam."),
                ("powercam-Ncam", "wget https://dreambox4u.com/emilnabil237/emu/installer-powercam-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي powercam-Ncam."),
                ("powercam-Oscam", "wget https://dreambox4u.com/emilnabil237/emu/installer-powercam-oscam.sh -O - | /bin/sh", True, "تثبيت محاكي powercam-Oscam."),
                ("powercam_v2-icam-arm", "wget https://dreambox4u.com/emilnabil237/emu/powercam/installer.sh -O - | /bin/sh", True, "تثبيت محاكي powercam_v2-icam-arm."),
                ("Pure2", "wget https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-pure/backup-pure.sh -O - | /bin/sh", True, "تحديث الحزم وتحميل إضافات مهمة"),
                ("Restore-flag-ncam", "wget https://dreambox4u.com/emilnabil237/script/Restore-flag-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي Restore-flag-ncam."),
                ("Restore-flag-oscam", "wget https://dreambox4u.com/emilnabil237/script/Restore-flag-Oscam.sh -O - | /bin/sh", True, "تثبيت محاكي Restore-flag-oscam."),
                ("Revcam", "wget https://dreambox4u.com/emilnabil237/emu/installer-revcam.sh -O - | /bin/sh", True, "تثبيت محاكي Revcam."),
                ("Revcam-Ncam", "wget https://dreambox4u.com/emilnabil237/emu/installer-revcam-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي Revcam-Ncam."),
                ("Revcam-Oscam", "wget https://dreambox4u.com/emilnabil237/emu/installer-revcam-oscam.sh -O - | /bin/sh", True, "تثبيت محاكي Revcam-Oscam."),
                ("Spinner-3d", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-3D.sh | /bin/sh", True, "تثبيت سينر Spinner-3d."),
                ("Spinner-Aglare", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-aglare.sh | /bin/sh", True, "تثبيت سينر Spinner-Aglare."),
                ("Spinner-Barcelona", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-barcelona.sh | /bin/sh", True, "تثبيت سينر Spinner-Barcelona."),
                ("Spinner-Bayern-Munich", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-bayern-munich.sh | /bin/sh", True, "تثبيت سينر Spinner-Bayern-Munich."),
                ("Spinner-Chelsea", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-chelsea.sh | /bin/sh", True, "تثبيت سينر Spinner-Chelsea."),
                ("Spinner-Circle", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-circle.sh | /bin/sh", True, "تثبيت سينر Spinner-Circle."),
                ("Spinner-Circle-Brown", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-circle-brown.sh | /bin/sh", True, "تثبيت سينر Spinner-Circle-Brown."),
                ("Spinner-Collar", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-collar.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Collar."),
                ("Spinner-Colored-Rings", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-colored-Rings.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Colored-Rings."),
                ("Spinner-Dance", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-dance.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Dance."),
                ("Spinner-Dart", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-dart.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Dart."),
                ("Spinner-Echse", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Echse.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Echse."),
                ("Spinner-Fan", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-fan.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Fan."),
                ("Spinner-Girls", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-girls.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Girls."),
                ("Spinner-Girls-Dance", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-girls-dance.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Girls-Dance."),
                ("Spinner-Jack-Sparrow", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Jack-Sparrow.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Jack-Sparrow."),
                ("Spinner-kare-dugmeler", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-kare-dugmeler.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-kare-dugmeler."),
                ("Spinner-Kum-saati-kare", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Kum-saati-kare.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Kum-saati-kare."),
                ("Spinner-kupler", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Kupler.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-kupler."),
                ("Spinner-Liverpool", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-liverpool.sh | /bin/sh", True, "تثبيت سينر Spinner-Liverpool."),
                ("Spinner-MadMax", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-MadMax.sh | /bin/sh", True, "تثبيت سينر Spinner-MadMax."),
                ("Spinner-Nasht", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-nasht.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Nasht."),
                ("Spinner-Number-Counter", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Number-Counter.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Number-Counter."),
                ("Spinner-PapaSchlumpf", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-PapaSchlumpf.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-PapaSchlumpf."),
                ("Spinner-Pigeon", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-pigeon.sh | /bin/sh", True, "تثبيت سينر Spinner-Pigeon."),
                ("Spinner-Pingu", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Pingu.sh | /bin/sh", True, "تثبيت سينر Spinner-Pingu."),
                ("Spinner-presupaci-hodiny", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-presupaci-hodiny.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-presupaci-hodiny."),
                ("Spinner-Renkli-donen-cemberler", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Renkli-donen-cemberler.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Renkli-donen-cemberler."),
                ("Spinner-Revolution", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Revolution.sh | /bin/sh", True, "تثبيت سينر Spinner-Revolution."),
                ("Spinner-Simba", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Simba.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Simba."),
                ("Spinner-SylvesterTweety", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-SylvesterTweety.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-SylvesterTweety."),
                ("Spinner-TS", "wget -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-ts.sh | /bin/sh", True, "تثبيت سينر Spinner-TS."),
                ("Spinner-Vu+", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-vu+.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Vu+."),
                ("Spinner-Wheel", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-wheel.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Wheel."),
                ("Spinner-Window", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-window.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Window."),
                ("Spinner-Xdreamy", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/spinners/spinner-Xdreamy.sh -O - | /bin/sh", True, "تثبيت سينر Spinner-Xdreamy."),
                ("Supcam-Ncam", "wget https://dreambox4u.com/emilnabil237/emu/installer-supcam-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي Supcam-Ncam."),
                ("Supcam-Oscam", "wget https://dreambox4u.com/emilnabil237/emu/installer-supcam-oscam.sh -O - | /bin/sh", True, "تثبيت محاكي Supcam-Oscam."),
                ("Ultracam-Ncam", "wget https://dreambox4u.com/emilnabil237/emu/installer-ultracam-ncam.sh -O - | /bin/sh", True, "تثبيت محاكي Ultracam-Ncam."),
                ("Ultracam-Oscam", "wget https://dreambox4u.com/emilnabil237/emu/installer-ultracam-oscam.sh -O - | /bin/sh", True, "تثبيت محاكي Ultracam-Oscam."),
            ]),
            ("النسخ الاحتياطية", [
                ("نسخ احتياطي للقنوات على /hdd", "mkdir -p /media/hdd/backup_o4t && tar -czf /media/hdd/backup_o4t/channels_backup.tar.gz /etc/enigma2/*bouquet* /etc/enigma2/lamedb* /etc/enigma2/settings && echo 'Saved to /media/hdd/backup_o4t/channels_backup.tar.gz'", False, "حفظ نسخة احتياطية كاملة من ملف القنوات والإعدادات على الهارد."),
                ("استعادة القنوات من /hdd", "tar -xzf /media/hdd/backup_o4t/channels_backup.tar.gz -C / && wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 && echo 'Channels Restored!'", False, "استرجاع ملف القنوات المحفوظ مسبقاً على الهارد."),
                ("نسخ احتياطي لإعدادات الإيمو", "mkdir -p /media/hdd/backup_o4t && tar -czf /media/hdd/backup_o4t/emu_keys_backup.tar.gz /etc/tuxbox/config /usr/keys 2>/dev/null && echo 'Emulator configs backed up!'", False, "حفظ نسخة احتياطية من ملفات سيرفرات OSCam / NCam والشفرات."),
                ("استعادة إعدادات الإيمو", "tar -xzf /media/hdd/backup_o4t/emu_keys_backup.tar.gz -C / && echo 'Emulator configs restored!'", False, "استرجاع ملفات السيرفرات والشفرات المحفوظة."),
                ("Backup-hotkey", "wget http://dreambox4u.com/emilnabil237/script/backup-hotkey.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-hotkey."),
                ("Backup-my-bouquetmakerxtream", "wget http://dreambox4u.com/emilnabil237/script/backup-my-bouquetmakerxtream.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-bouquetmakerxtream."),
                ("Backup-my-Channels", "wget http://dreambox4u.com/emilnabil237/script/Create-My-backup-shannels.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-Channels."),
                ("Backup-my-ip2sat-server", "wget http://dreambox4u.com/emilnabil237/script/backup-my-ip2sat-server.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-ip2sat-server."),
                ("Backup-my-ipaudio-server", "wget http://dreambox4u.com/emilnabil237/script/backup-my-ipaudio-server.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-ipaudio-server."),
                ("Backup-my-ipaudiopro-server", "wget http://dreambox4u.com/emilnabil237/script/backup-my-ipaudiopro-server.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-ipaudiopro-server."),
                ("Backup-my-jediplaylists", "wget http://dreambox4u.com/emilnabil237/script/backup-my-jediplaylists.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-jediplaylists."),
                ("Backup-my-multistalkerpro", "wget http://dreambox4u.com/emilnabil237/script/backup-my-multistalkerpro.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-multistalkerpro."),
                ("Backup-my-Subtitle-Setting", "wget http://dreambox4u.com/emilnabil237/script/backup_my-subtitle-setting.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-Subtitle-Setting."),
                ("Backup-my-xstreamity-servers", "wget http://dreambox4u.com/emilnabil237/script/backup-my-xstreamity-servers.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-my-xstreamity-servers."),
                ("Backup-network", "wget http://dreambox4u.com/emilnabil237/script/backup-network.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-network."),
                ("Backup-sittings-xtraevent", "wget http://dreambox4u.com/emilnabil237/script/backup-sittings-xtraevent.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-sittings-xtraevent."),
                ("Backup-softcams", "wget http://dreambox4u.com/emilnabil237/script/backup-softcams.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-softcams."),
                ("Backup-tuner", "wget http://dreambox4u.com/emilnabil237/script/backup-tuner.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Backup-tuner."),
                ("Full-Backup-Image", "wget https://raw.githubusercontent.com/emilnabil/fullbackup/main/fullbackup-vu4k-encrypt.sh -O - | /bin/sh", True, "إنشاء نسخة احتياطية: Full-Backup-Image."),
                ("Restore Settings", "wget \"https://github.com/emilnabil/backup-images/raw/refs/heads/main/backup-egami/restore-settings.sh\" -O - | /bin/sh", True, "استعادة الإعدادات"),
                ("Restore-hotkey", "wget http://dreambox4u.com/emilnabil237/script/restore-hotkey.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-hotkey."),
                ("Restore-my-bouquetmakerxtream", "wget http://dreambox4u.com/emilnabil237/script/restore-my-bouquetmakerxtream.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-bouquetmakerxtream."),
                ("Restore-my-Channels", "wget http://dreambox4u.com/emilnabil237/script/Restore-My-backup-shannels.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-Channels."),
                ("Restore-my-ip2sat-server", "wget http://dreambox4u.com/emilnabil237/script/restore-my-ip2sat-server.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-ip2sat-server."),
                ("Restore-my-ipaudio-server", "wget http://dreambox4u.com/emilnabil237/script/restore-my-ipaudio-server.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-ipaudio-server."),
                ("Restore-my-ipaudiopro-server", "wget http://dreambox4u.com/emilnabil237/script/restore-my-ipaudiopro-server.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-ipaudiopro-server."),
                ("Restore-my-jediplaylists", "wget http://dreambox4u.com/emilnabil237/script/restore-my-jediplaylists.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-jediplaylists."),
                ("Restore-my-multistalkerpro", "wget http://dreambox4u.com/emilnabil237/script/restore-my-multistalkerpro.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-multistalkerpro."),
                ("Restore-My-Subtitle-Setting", "wget http://dreambox4u.com/emilnabil237/script/Restore_my-subtitle-setting.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-My-Subtitle-Setting."),
                ("Restore-my-xstreamity-servers", "wget http://dreambox4u.com/emilnabil237/script/restore-my-xstreamity-servers.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-my-xstreamity-servers."),
                ("Restore-network", "wget http://dreambox4u.com/emilnabil237/script/restore-network.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-network."),
                ("Restore-sittings-xtraevent", "wget http://dreambox4u.com/emilnabil237/script/restore-sittings-xtraevent.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-sittings-xtraevent."),
                ("Restore-softcams", "wget http://dreambox4u.com/emilnabil237/script/restore-softcams.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-softcams."),
                ("Restore-tuner", "wget http://dreambox4u.com/emilnabil237/script/restore-tuner.sh -O - | /bin/sh", True, "استعادة نسخة احتياطية: Restore-tuner."),
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
                ("تثبيت سكين BlackSpirit FHD", "wget -q --no-check-certificate https://raw.githubusercontent.com/biko-73/BlackSpirit.FHD/main/installer.sh -O - | /bin/sh", True, "تثبيت سكين BlackSpirit الداكن الاحترافي."),
                ("Abertis-Auto-Switcher", "wget https://raw.githubusercontent.com/prof-abdo/Abertis-Auto-Switcher-PRO/main/installer.sh -O - | /bin/sh", True, "تشغيل باقة ابيرنس المالتي ستريم علي الهسباسات"),
                ("Abstract", "wget https://dreambox4u.com/emilnabil237/plugins/xtreamity/installer-skin-abstract.sh -O - | /bin/sh", True, "تثبيت سكين Abstract."),
                ("Acherone", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/acherone/installer.sh -O - | /bin/sh", True, "تصفح السكريبتات"),
                ("AdenChManager", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/AdenChManager/AdenChManager.sh -O - | /bin/sh", True, "مدير القنوات"),
                ("Advanced Screenshot", "wget -q --no-check-certificate -O /tmp/enigma2-plugin-extensions-advancedscreenshot_all.ipk 'https://raw.githubusercontent.com/emilnabil/download-plugins/main/advancedscreenshot/enigma2-plugin-extensions-advancedscreenshot_all.ipk' && opkg install /tmp/enigma2-plugin-extensions-advancedscreenshot_all.ipk && rm -f /tmp/enigma2-plugin-extensions-advancedscreenshot_all.ipk", True, "أداة لالتقاط صور من واجهة Enigma2. ملف التثبيت IPK؛ السكربت يثبته باستخدام opkg ويحتاج curl. تحقق من معمارية وتوافق الصورة قبل التثبيت."),
                ("AdvancedBootLogoSwapper-By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/abls/main/installer.sh -O - | /bin/sh", True, "صانع بوت لوجو"),
                ("Aglare-FHD (Egami)", "wget https://github.com/emilnabil/aglare/raw/refs/heads/main/skins-aglare-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Aglare-FHD."),
                ("Aglare-fhd (OpenBH)", "wget https://github.com/emilnabil/aglare/raw/refs/heads/main/skins-aglare-fhd-pli.sh -O - | /bin/sh", True, "تثبيت سكين Aglare-fhd."),
                ("AglareATV Skin", "wget \"https://raw.githubusercontent.com/popking159/skins/refs/heads/main/aglareatv/installer.sh\" -O - | /bin/sh", True, "تثبيت سكين AglareATV Skin."),
                ("AIO Panel", "wget -q -O - https://raw.githubusercontent.com/OliOli2013/PanelAIO-Plugin/main/installer.sh | /bin/sh", True, "لوحة شاملة تجمع عشرات الأدوات والإضافات والخدمات في مكان واحد."),
                ("Airnet-Fn", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/airnet-fn.sh -O - | /bin/sh", True, "تثبيت Airnet-Fn."),
                ("AiSubtitles", "wget -q --no-check-certificate https://gitlab.com/hmeng80/extensions/-/raw/main/AISubtitles/aisubtitles.sh -O - | /bin/sh", True, "إضافة تعتمد على تقنيات الذكاء الاصطناعي لإنشاء وترجمة الترجمات بشكل أسرع وأكثر دقة."),
                ("AjPanel", "wget https://raw.githubusercontent.com/AMAJamry/AJPanel/main/installer.sh -O - | /bin/sh", True, "لوحة أدوات لإدارة وظائف متعددة على جهاز Enigma2."),
                ("ajpanel_menu1", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/tarekzoka/ajpanel/refs/heads/main/ajpanel_menu1.sh -O - | /bin/sh", True, "سكريبت تثبيت قائمة AjPanel من مستودع المطوّر."),
                ("Alajre", "wget https://dreambox4u.com/emilnabil237/plugins/alajre/installer.sh -O - | /bin/sh", True, "الأجر"),
                ("AlAyam-FHD", "wget https://raw.githubusercontent.com/biko-73/TeamNitro/main/script/installerAL.sh -O - | /bin/sh", True, "تثبيت سكين AlAyam-FHD."),
                ("Alkuds-IpAudio", "wget https://raw.githubusercontent.com/xximhxx/Alkuds-ipaudio-MAC-Xtreme-Player/main/installer.sh -O - | /bin/sh", True, "أضافة صوتيات علي قنوات السات"),
                ("AlMoaddin Modded by Emil", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/AlMuaddhin/almoaddhin.sh -O - | /bin/sh", True, "المؤذن"),
                ("AlMuaddhin", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/AlMuaddhin/almoaddhin.sh | /bin/sh", True, "إضافة مواقيت الصلاة والتنبيه لها على أجهزة Enigma2. سكربت المصدر يحذف مجلد الإضافة السابق قبل فك النسخة الجديدة؛ خذ نسخة من إعداداتك وراج..."),
                ("AlternativeSoftcamManager", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/AlternativeSoftcamManager/AlternativeSoftcamManager.sh -O - | /bin/sh", True, "ادارة الايميوهات"),
                ("AlternativeSoftCamManager_iet5", "wget https://raw.githubusercontent.com/Saiedf/AlternativeSoftCamManager/main/installer_alternativesoftcammanager_auto.sh -O - | /bin/sh", True, "ادارة الايميوهات"),
                ("Ansite", "wget https://raw.githubusercontent.com/emil237/ansite/refs/heads/main/installer.sh -O - | /bin/sh", True, "أنصت"),
                ("Apod", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/apod/installer.sh -O - | /bin/sh", True, "معلومات عن كوكب الأرض"),
                ("Apsattv", "wget https://raw.githubusercontent.com/Belfagor2005/Apsattv/main/installer.sh -O - | /bin/sh", True, "تثبيت Apsattv."),
                ("ArabicPlayer", "wget https://raw.githubusercontent.com/asdrere123-alt/ArabicPlayer/main/installer.sh -O - | /bin/sh", True, "تشغيل ال iptv"),
                ("ArabicSavior", "wget https://raw.githubusercontent.com/fairbird/ArabicSavior/main/installer.sh -O - | /bin/sh", True, "أداة مساعدة عربية لـ Enigma2 من مستودع المطوّر."),
                ("Areadeltasat_fhd", "wget https://github.com/emil237/skins-enigma2/raw/refs/heads/main/ATV/skins_areadeltasat_fhd_dragon_1_9_Poster_Backdrop.sh -O - | /bin/sh", True, "تثبيت سكين Areadeltasat_fhd."),
                ("Astronomy", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/astronomy/installer.sh -O - | /bin/sh", True, "حركة الكواكب"),
                ("Athan Times", "wget https://dreambox4u.com/emilnabil237/plugins/athantimes/installer.sh -O - | /bin/sh", True, "مواقيت الصلاة"),
                ("Atilehd", "wget https://dreambox4u.com/emilnabil237/plugins/atilehd/installer.sh -O - | /bin/sh", True, "مدير الثيمات"),
                ("AudioMerge", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/audiomerge/audiomerge.sh -O - | /bin/sh", True, "دمح صوتيات قناتين"),
                ("AudioSelectionPatcher-By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/audioselectionpatcher/refs/heads/main/myinstaller.sh -O - | /bin/sh", True, "صوتيات فوكس مع تايم شفت"),
                ("AudioShift", "wget -O - https://xfayez95.github.io/audioshift/installer.sh | sh", True, "أداة سريعة لتبديل المسارات الصوتية داخل القنوات والأفلام بسهولة."),
                ("Auto-DCW-Key-Add", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/auto-dcw-key-add/auto-dcw-key-add.sh -O - | /bin/sh", True, "مفاتيح الشفرات"),
                ("AutoBiss", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/AutoBiss/AutoBiss.sh -O - | /bin/sh", True, "جلب شفرات بيس اوتوماتيك"),
                ("automatic-fullbackup", "wget https://dreambox4u.com/emilnabil237/plugins/automatic-fullbackup/installer.sh -O - | /bin/sh", True, "نسخ احتياطي للصورة"),
                ("AutoSub", "wget -q --no-check-certificate https://github.com/emilnabil/download-plugins/raw/refs/heads/main/AutoSub/AutoSub.sh -O - | /bin/sh", True, "مترجم البث المباشر للقنوات"),
                ("AutoSub AI", "wget -q -O /tmp/AutoSub.tar.gz https://raw.githubusercontent.com/HBK2010/AutoSub/main/AutoSub.tar.gz && tar xzf /tmp/AutoSub.tar.gz -C /usr/lib/enigma2/python/Plugins/Extensions", True, "أداة ذكية لإنشاء ترجمات تلقائية للمحتوى المرئي باستخدام تقنيات التعرف على الصوت."),
                ("AutoZap Recovery", "wget -q --no-check-certificate https://raw.githubusercontent.com/HBK2010/-AutoZap-Recovery-by-Ahmad-Alamri/main/installer.sh -O - | /bin/sh", True, "تصحيح بث القنوات"),
                ("Azkar Almuslim", "wget https://dreambox4u.com/emilnabil237/plugins/azkar-almuslim/installer.sh -O - | /bin/sh", True, "أذكار المسلم"),
                ("BackupAndFlash-mod-Emil", "wget https://github.com/emil237/download-plugins/raw/refs/heads/main/backupflash/backupflash.sh -O - | /bin/sh", True, "نسخ احتياطي للصورة"),
                ("BackupFlash", "wget https://raw.githubusercontent.com/fairbird/backupflash/main/installer.sh -O - | /bin/sh", True, "أداة لإنشاء نسخة احتياطية كاملة من النظام الحالي واستعادتها بسهولة عند الحاجة."),
                ("BackupSuite", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/backupsuite/backupsuite.sh -O - | /bin/sh", True, "نسخ احتياطي للصورة"),
                ("Barby-Black-py3-FHD", "wget https://dreambox4u.com/emilnabil237/script/SKIN-Barby-Black-py3-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Barby-Black-py3-FHD."),
                ("Barby-Green-py3-FHD", "wget https://dreambox4u.com/emilnabil237/script/SKIN-Barby-Green-py3-FHD.sh -O - | /bin/sh", True, "تثبيت سكين Barby-Green-py3-FHD."),
                ("Barby-purple-py3-FHD", "wget https://dreambox4u.com/emilnabil237/script/SKIN-Barby-purple-py3-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Barby-purple-py3-FHD."),
                ("Barby-py3-FHD", "wget https://dreambox4u.com/emilnabil237/script/SKIN-Barby-py3-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Barby-py3-FHD."),
                ("BARDO-FHD", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/refs/heads/main/pli/Skin-bardo-fhd_3.7.2.sh -O - | /bin/sh", True, "تثبيت سكين BARDO-FHD."),
                ("BATMAN-MP-HD", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/main/pli/SKIN-BATMAN-MP-HD-By-Muaath.sh -O - | /bin/sh", True, "تثبيت سكين BATMAN-MP-HD."),
                ("Beengo", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/beengo.sh -O - | /bin/sh", True, "تثبيت Beengo."),
                ("BissFeedAutoKey", "wget https://raw.githubusercontent.com/emilnabil/bissfeed-autokey/main/installer.sh -O - | /bin/sh", True, "مفاتيح بيس"),
                ("Bitrate", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/bitrate/bitrate.sh -O - | /bin/sh", True, "معدل البث"),
                ("Bitrate-mod-ariad", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/bitrate/bitrate-mod-ariad.sh -O - | /bin/sh", True, "معدل البث"),
                ("BLACKNEON-XP-FHD-V2_ArabicDiscription", "wget https://github.com/emilnabil/skins-openatv/raw/refs/heads/main/skin-BLACKNEON-XP-FHD-v2_arabicdiscription.sh -O - | /bin/sh", True, "تثبيت سكين BLACKNEON-XP-FHD-V2_ArabicDiscription."),
                ("BLACKNEON-XP_Mod_M-Nasr", "wget https://dreambox4u.com/emilnabil237/skins/pli9x/Skin-BLACKNEON-XP_mod_mnasr-pli9x.sh -O - | /bin/sh", True, "تثبيت سكين BLACKNEON-XP_Mod_M-Nasr."),
                ("BlackShadow_X2P_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/BlackShadow_X2P_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين BlackShadow_X2P_OBH."),
                ("BLACKSKY-S-HD", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/main/pli/SKIN-BLACKSKY-S-HD-MOD-By-Muaath.sh -O - | /bin/sh", True, "تثبيت سكين BLACKSKY-S-HD."),
                ("Bluemetal-FHD", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/refs/heads/main/pli/Skin-bluemetal-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Bluemetal-FHD."),
                ("BoHLALA-FHD", "wget https://gitlab.com/emilnabil1/teamnitro/-/raw/main/installer.sh -O - | /bin/sh", True, "تثبيت سكين BoHLALA-FHD."),
                ("BootlogoSwapper V2.4", "wget http://dreambox4u.com/emilnabil237/script/BootlogoSwapper_v2.4.sh -O - | /bin/sh", True, "بوت لوجو متعدد"),
                ("Brushedalu HD", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/skins-for-dreambox/Brushedalu-HD.sh | /bin/sh", True, "Skin HD لأجهزة DreamOS. ملف تثبيت مباشر؛ راجع التوافق مع صورة جهازك قبل فك الملفات إلى النظام."),
                ("Bundesliga-Permanent-Clock", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/bundesliga-permanent-clock/bundesliga-permanent-clock.sh -O - | /bin/sh", True, "ساعة رقمية"),
                ("CacheFlush", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/cacheflush/cacheflush.sh -O - | /bin/sh", True, "مسح الكاش"),
                ("Calculator-E2", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/calculator-e2/calculator-e2.sh -O - | /bin/sh", True, "الآلة الحاسبة"),
                ("Calendar", "wget https://raw.githubusercontent.com/Belfagor2005/Calendar/main/installer.sh -O - | /bin/sh", True, "التقويم"),
                ("Cccam", "wget https://dreambox4u.com/emilnabil237/emu/installer-cccam.sh -O - | /bin/sh", True, "تثبيت Cccam."),
                ("Cccaminfo-py2", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/cccaminfo/cccaminfo_py2.sh -O - | /bin/sh", True, "بيانات الـ CCCam"),
                ("Cccaminfo-py3", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/cccaminfo/cccaminfo_py3.sh -O - | /bin/sh", True, "بيانات الـ CCCam"),
                ("Cccaminfo_All-Python", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/cccaminfo/cccaminfo_all-py.sh -O - | /bin/sh", True, "بيانات الـ CCCam"),
                ("CFG_ZOOM_FINAL", "wget https://dreambox4u.com/emilnabil237/plugins/cfg_Zoom_Final_FIX7x/installer.sh -O - | /bin/sh", True, "سيرفرات مجانية"),
                ("CH.LEAGUE-FHD", "wget http://dreambox4u.com/emilnabil237/script/SKIN-PLI-CH.LEAGUE-FHD.sh -O - | /bin/sh", True, "تثبيت سكين CH.LEAGUE-FHD."),
                ("CHLogoChanger", "wget https://dreambox4u.com/emilnabil237/plugins/CHLogoChanger/CHLogoChanger.sh -O - | /bin/sh", True, "تخصيص الشعار"),
                ("chocholousek-picons", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/chocholousek-picons.sh -O - | /bin/sh", True, "تحميل البيكونات"),
                ("Chromium", "opkg install enigma2-plugin-extensions-chromium", True, "تثبيت حزمة Chromium من مستودعات صورة النظام؛ التوافق يعتمد على الصورة والمعمارية."),
                ("Ciefp TMDB Search", "wget -q https://raw.githubusercontent.com/ciefp/CiefpTMDBSearch/main/installer.sh -O - | /bin/sh", True, "عرض بيانات وصفية للأفلام والمسلسلات من The Movie Database في البلجنز المتوافقة."),
                ("CiefpBootlogo", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpBootlogo/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpBootlogo."),
                ("CiefpBouquetUpdater", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpBouquetUpdater/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpBouquetUpdater."),
                ("CiefpChannelManager", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpChannelManager/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpChannelManager."),
                ("CiefpE2Converter", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpE2Converter/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpE2Converter."),
                ("CiefpE2editor", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/Ciefpe2editor/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpE2editor."),
                ("CiefpEasySetup", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpEasySetup/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpEasySetup."),
                ("CiefpEPGshare", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpEPGshare/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpEPGshare."),
                ("CiefpIPTVBouquets", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpIPTVBouquets/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpIPTVBouquets."),
                ("CiefpKingSat", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpKingSat/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpKingSat."),
                ("CiefpMojTvEPG", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpMojTvEPG/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpMojTvEPG."),
                ("CiefpOpenDirectories", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOpenDirectories/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpOpenDirectories."),
                ("CiefpOpenSubtitles", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOpenSubtitles/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpOpenSubtitles."),
                ("CiefpOscamEditor", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpOscamEditor/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpOscamEditor."),
                ("CiefpParabolaCZ", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpParabolaCZ/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpParabolaCZ."),
                ("CiefpPiconManager", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpPiconManager/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpPiconManager."),
                ("CiefpPicturePlayer", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpPicturePlayer/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpPicturePlayer."),
                ("CiefpPlugins", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpPlugins/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpPlugins."),
                ("CiefpRottenTomatoes", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpRottenTomatoes/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpRottenTomatoes."),
                ("CiefpSatelliteAnalyzer", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSatelliteAnalyzer/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSatelliteAnalyzer."),
                ("CiefpSatellitesXmlEditor", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSatelliteXmlEditor/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSatellitesXmlEditor."),
                ("CiefpScreenGrab", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpScreenGrab/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpScreenGrab."),
                ("CiefpSelectSatellite", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSelectSatellite/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSelectSatellite."),
                ("CiefpSettingsDownloader", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSettingsDownloader/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSettingsDownloader."),
                ("CiefpsettingsMotor", "wget https://raw.githubusercontent.com/ciefp/CiefpsettingsMotor/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpsettingsMotor."),
                ("CiefpSettingsPanel", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpsettingsPanel/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSettingsPanel."),
                ("CiefpSettingsStreamrelay PY2", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSettingsStreamrelayPY2/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSettingsStreamrelay PY2."),
                ("CiefpSettingsStreamrelay PY3", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSettingsStreamrelay/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSettingsStreamrelay PY3."),
                ("CiefpSettingsT2miAbertis", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSettingsT2miAbertis/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSettingsT2miAbertis."),
                ("CiefpSettingsT2miAbertisOpenPLi", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSettingsT2miAbertisOpenPLi/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpSettingsT2miAbertisOpenPLi."),
                ("CiefpTvProgram", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpTvProgram/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpTvProgram."),
                ("CiefpTvProgramA1HR", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpTvProgramA1HR/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpTvProgramA1HR."),
                ("CiefpTvProgramSBB", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpTvProgramSBB/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpTvProgramSBB."),
                ("CiefpTvProgramSK", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpTvProgramSK/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpTvProgramSK."),
                ("CiefpTvTodayDE", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpTvTodayDE/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpTvTodayDE."),
                ("CiefpVibes", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpVibes/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpVibes."),
                ("CiefpVideoPlayer", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpVideoPlayer/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpVideoPlayer."),
                ("CiefpWhitelistStreamrelay", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpWhitelistStreamrelay/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpWhitelistStreamrelay."),
                ("CiefpYouTube", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpYouTube/main/installer.sh -O - | /bin/sh", True, "تثبيت CiefpYouTube."),
                ("CineView FHD", "wget -qO /tmp/cineview-install.sh https://raw.githubusercontent.com/habeb-s/CineView-MLA-Install/main/cineview-install.sh && sh /tmp/cineview-install.sh", True, "واجهة سينمائية متقدمة تركز على عرض البوسترات ومعلومات الأفلام بصورة جذابة."),
                ("CineView FHD MLA", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/skin-cineview/CineView.sh | /bin/sh", True, "ثيم FHD مع مثبت ذكي يحدد عائلة الصورة ويتحقق من إصدار Python وملف IPK ببصمة SHA256 قبل التثبيت. مدعوم حسب السكربت: OpenATV وEGAMI وPurE2 ..."),
                ("CineView-FHD (Egami)", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/skin-cineview/CineView.sh -O - | /bin/sh", True, "تثبيت سكين CineView-FHD."),
                ("Ciplushelper", "wget https://raw.githubusercontent.com/OwnerPlugins/Ciplushelper/main/installer.sh -O - | /bin/sh", True, "تشغيل الكامات الرسمية"),
                ("CommandCenter", "wget https://raw.githubusercontent.com/OwnerPlugins/CommandCenter/main/installer.sh -O - | /bin/sh", True, "تثبيت CommandCenter."),
                ("CrashLogoViewer_1.6", "wget https://dreambox4u.com/emilnabil237/plugins/crashlogviewer/install-CrashLogViewer.sh -O - | /bin/sh", True, "تصفح الكراشات"),
                ("CrashLogoViewer_1.8", "wget https://dreambox4u.com/emilnabil237/plugins/crashlogviewer/crashlogviewer_1.8.sh -O - | /bin/sh", True, "تصفح الكراشات"),
                ("CrashLogoViewer_1.9", "wget https://dreambox4u.com/emilnabil237/plugins/crashlogviewer/crashlogviewer_1.9.sh -O - | /bin/sh", True, "تصفح الكراشات"),
                ("CrondManager", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/crondmanager/installer.sh -O - | /bin/sh", True, "تحديد وقت للسكريبت"),
                ("Custom Channel Selection-By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/customchannelselection/refs/heads/main/myinstaller.sh -O - | /bin/sh", True, "قائمة للقنوات"),
                ("CustomIptvArchiveMakerpro", "wget https://dreambox4u.com/emilnabil237/plugins/CustomIptvArchiveMakerpro/CustomIptvArchiveMakerpro.sh -O - | /bin/sh", True, "أضافة اشتراكات iptv"),
                ("CutsClear", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/cutsclear/cutsclear.sh -O - | /bin/sh", True, "حذف الأفلام"),
                ("Desert-FHD", "wget https://gitlab.com/emilnabil1/teamnitro/-/raw/main/installer-skin-desert.sh -O - | /bin/sh", True, "تثبيت سكين Desert-FHD."),
                ("Disk_And_CPU_Temperature", "wget https://raw.githubusercontent.com/emilnabil/dreambox/refs/heads/main/disk_and_cpu_temperature.sh -O - | /bin/sh", True, "حرارة القرص الصلب"),
                ("display-oe-a-lcdskin-1", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-1.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-1."),
                ("display-oe-a-lcdskin-10", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-10.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-10."),
                ("display-oe-a-lcdskin-11", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-11.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-11."),
                ("display-oe-a-lcdskin-12", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-12.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-12."),
                ("display-oe-a-lcdskin-13", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-13.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-13."),
                ("display-oe-a-lcdskin-2", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-2.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-2."),
                ("display-oe-a-lcdskin-3", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-3.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-3."),
                ("display-oe-a-lcdskin-4", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-4.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-4."),
                ("display-oe-a-lcdskin-5", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-5.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-5."),
                ("display-oe-a-lcdskin-6", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-6.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-6."),
                ("display-oe-a-lcdskin-7", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-7.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-7."),
                ("display-oe-a-lcdskin-8", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-8.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-8."),
                ("display-oe-a-lcdskin-9", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Display-Skin/display-oe-a-lcdskin-9.sh -O - | /bin/sh", True, "تثبيت سكين display-oe-a-lcdskin-9."),
                ("Dragon-FHD", "wget https://raw.githubusercontent.com/biko-73/TeamNitro/main/script/installerD.sh -O - | /bin/sh", True, "تثبيت سكين Dragon-FHD."),
                ("DreamArabia", "wget -q --no-check-certificate http://dreambox4u.com/dreamarabia/scripts/installer.sh -O - | /bin/sh", True, "لوحة عربية متكاملة تحتوي على مجموعة كبيرة من الإضافات والأدوات الخاصة بإنجما2."),
                ("DreamExplorer", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/dreamexplorer/dreamexplorer.sh -O - | /bin/sh", True, "تصفح الملفات"),
                ("dreamosat-downloader", "wget https://dreambox4u.com/emilnabil237/plugins/dreamosat-downloader/installer.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("DreamOSatCamManager", "wget https://raw.githubusercontent.com/biko-73/DreamOSat_cam_Manager/main/installer.sh -O - | /bin/sh", True, "تحميل الايميوهات"),
                ("DreamXtream", "wget http://dreambox4u.com/ch/E2/enigma2-plugin-extensions-dreamxtream_0.3-r9.0_arm64.deb -O /tmp/enigma2-plugin-extensions-dreamxtream_0.3-r9.0_arm64.deb && dpkg -i /tmp/enigma2-plugin-extensions-dreamxtream_0.3-r9.0_arm64.deb", True, "إضافة IPTV خفيفة مخصصة لصور DreamOS توفر تجربة مشاهدة مستقرة مع دعم قوائم Xtream."),
                ("E2-darkos-FHD", "wget https://dreambox4u.com/emilnabil237/skins/openvix/skins-e2-darkos.sh -O - | /bin/sh", True, "تثبيت سكين E2-darkos-FHD."),
                ("E2-Duplicate-Channels-Manager", "wget https://raw.githubusercontent.com/Saiedf/E2DuplicateChannelsManager/main/installer_duplicatechannelsmanager_auto.sh -O - | /bin/sh", True, "مدير القنوات"),
                ("E2-Tube", "wget https://dreambox4u.com/emilnabil237/plugins/E2Tube/e2tube.sh -O - | /bin/sh", True, "يوتيوب"),
                ("E2BissKeysEditor", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/E2BissKeysEditor/E2BissKeysEditor.sh -O - | /bin/sh", True, "تعديل الشفرات"),
                ("e2iplayer", "wget -q \"--no-check-certificate\" https://github.com/angelheart150/My_e2iplayer_hosts/raw/main/install-e2iplayer-update-hosts.sh -O - | /bin/sh", True, "مشغل وسائط وإضافات مضيفين؛ توجد طريقتان للتثبيت من المصادر المقدمة."),
                ("E2IplayerUpdater-Angel_Heart", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/E2IplayerUpdater/E2IplayerUpdater.sh -O - | /bin/sh", True, "تحديث السبرفرات"),
                ("E2m3ubouquet", "wget https://dreambox4u.com/emilnabil237/plugins/e2m3u2bouquet/installer.sh -O - | /bin/sh", True, "تحويل iptv m3u الي المفضلات"),
                ("E2Player", "wget -q https://raw.githubusercontent.com/oe-mirrors/e2iplayer/refs/heads/python3/e2iplayer_install.sh -O - | /bin/sh", True, "واحدة من أشهر إضافات تشغيل المحتوى المرئي عبر الإنترنت لمشاهدة الأفلام والمسلسلات من مصادر متعددة."),
                ("E2Player Hosts Update", "wget -q --no-check-certificate https://github.com/angelheart150/My_e2iplayer_hosts/raw/main/install-e2iplayer-update-hosts.sh -O - | /bin/sh", True, "تحديث واستكمال هوستات E2Player."),
                ("E2Player-Angel_Heart", "wget https://github.com/angelheart150/My_e2iplayer_hosts/raw/main/install-e2iplayer-update-hosts.sh -O - | /bin/sh", True, "برنامج مشاهدة"),
                ("E2Player-Biko", "wget https://raw.githubusercontent.com/biko-73/E2IPlayer/main/installer_E2.sh -O - | /bin/sh", True, "برنامج مشاهدة"),
                ("E2Player-MAXBAMBY", "wget https://gitlab.com/maxbambi/e2iplayer/-/raw/master/install-e2iplayer.sh -O - | /bin/sh", True, "برنامج مشاهدة"),
                ("E2Player-ZADMARIO", "wget https://gitlab.com/zadmario/e2iplayer/-/raw/master/install-e2iplayer.sh -O - | /bin/sh", True, "برنامج مشاهدة"),
                ("Easy-Cccam", "wget https://raw.githubusercontent.com/emil237/plugins/refs/heads/main/easy-cccam/easy-cccam.sh -O - | /bin/sh", True, "إدخال CCCam"),
                ("EclipseFHD_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/EclipseFHD_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين EclipseFHD_OBH."),
                ("EclipseFire_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/EclipseFire_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين EclipseFire_OBH."),
                ("Emil BootLogos", "wget --no-check-certificate -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/emilbootlogos/emilbootlogos.sh | /bin/sh", True, "بوت لوجو"),
                ("Emil Channels", "wget --no-check-certificate -O - https://github.com/emilnabil/download-plugins/raw/refs/heads/main/EmilChannels/emilchannels.sh | /bin/sh", True, "تحميل ملفات القنوات"),
                ("Emil Panel Lite", "wget -q \"--no-check-certificate\" https://dreambox4u.com/emilnabil237/plugins/ajpanel/new/emil-panel-lite.sh -O - | /bin/sh", True, "نسخة خفيفة من لوحة أدوات Emil لأجهزة Enigma2."),
                ("EmilPanelPro", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/EmilPanelPro/emilpanelpro.sh -O - | /bin/sh", True, "لوحة أدوات إضافية لأجهزة Enigma2 من مستودع EmilNabil."),
                ("EmilRemovePackage", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/EmilRemovePackage/EmilRemovePackage.sh -O - | /bin/sh", True, "حذف الإضافات"),
                ("enigma2readeradder", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/enigma2readeradder/enigma2readeradder.sh -O - | /bin/sh", True, "إدخال CCCam"),
                ("Enigma2uninstaller", "wget http://dreambox4u.com/emilnabil237/plugins/unstaller-plugins/installer.sh -O - | /bin/sh", True, "حذف البلجنات"),
                ("EnigmaPlay", "wget -qO- https://raw.githubusercontent.com/Ahmadarjan1/EnigmaPlay-Repo/main/install.sh | sh", True, "مشغل ومركز محتوى لإضافات Enigma2 حسب مستودع المطوّر."),
                ("EnigmaPrayer", "wget --no-check-certificate -O - https://dreambox4u.com/emilnabil237/plugins/EnigmaPrayer/EnigmaPrayer.sh | /bin/sh", True, "مواقيت الصلاة بدون انترنت"),
                ("Epanel", "wget https://dreambox4u.com/emilnabil237/plugins/epanel/installer.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("Epg Grabber", "wget https://dreambox4u.com/emilnabil237/plugins/Epg-Grabber/installer.sh -O - | /bin/sh", True, "دليل القنوات"),
                ("EPGImport", "wget -qO- https://raw.githubusercontent.com/Saiedf/EPGImport/main/installer_epgimportiet5_auto.sh | /bin/sh", True, "أداة استيراد وتحديث بيانات دليل البرامج الإلكتروني EPG من مصادر متعددة."),
                ("EPGImport-99", "wget https://raw.githubusercontent.com/Belfagor2005/EPGImport-99/main/installer.sh -O - | /bin/sh", True, "دليل القنوات"),
                ("EPGImport-auto - iet5", "wget https://raw.githubusercontent.com/Saiedf/EPGImport/main/installer_epgimportiet5_auto.sh -O - | /bin/sh", True, "دليل القنوات"),
                ("EPGTranslator", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/epgtranslator.sh -O - | /bin/sh", True, "مترجم دليل القنوات"),
                ("Estalker", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/EStalker/EStalker.sh -O - | /bin/sh", True, "مشغل بورتلات"),
                ("EstalkerWebControl", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/EstalkerWebControl/estalkerwebcontrol.sh -O - | /bin/sh", True, "التحكم في اضافة بورتلات والحذف"),
                ("estuary-1080-FHD", "wget https://gitlab.com/elbrins/skins/-/raw/main/Spa/Skin-estuary-1080.sh -O - | /bin/sh", True, "تثبيت سكين estuary-1080-FHD."),
                ("EvgQuickSignal", "wget https://dreambox4u.com/emilnabil237/plugins/EvgQuickSignal/EvgQuickSignal.sh -O - | /bin/sh", True, "بيان إشارة الترددات"),
                ("Feeds-Finder", "wget https://dreambox4u.com/emilnabil237/plugins/feeds-finder/installer.sh -O - | /bin/sh", True, "بحث الفيدات"),
                ("FileCommander", "opkg update && opkg install enigma2-plugin-extensions-filecommander", True, "مدير ملفات لأجهزة Enigma2 لتصفح الملفات وتنفيذ عمليات الإدارة المتاحة."),
                ("Filmon", "wget https://github.com/OwnerPlugins/Filmon/raw/refs/heads/main/installer.sh -O - | /bin/sh", True, "تثبيت Filmon."),
                ("Filmxy", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/filmxy/filmxy.sh -O - | /bin/sh", True, "تثبيت Filmxy."),
                ("FootOnSat", "wget -q https://raw.githubusercontent.com/fairbird/FootOnsat/main/Download/install.sh -O - | /bin/sh", True, "إضافة مرتبطة بمحتوى رياضي على أجهزة Enigma2؛ راجع صفحة التفاصيل والتوافق."),
                ("Foreca1", "wget https://github.com/OwnerPlugins/ForecaOne/raw/refs/heads/main/installer.sh -O - | /bin/sh", True, "تثبيت Foreca1."),
                ("Freearhey", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/freearhey/freearhey.sh -O - | /bin/sh", True, "تثبيت Freearhey."),
                ("FreeCCcamServer", "wget https://ia803104.us.archive.org/0/items/freecccamserver/installer.sh -O - | /bin/sh", True, "CCCam مجاني"),
                ("Full HD Glass17", "wget http://dreambox4u.com/emilnabil237/skins/skin-fullhdglass17/installer.sh -O - | /bin/sh", True, "تثبيت سكين Full HD Glass17."),
                ("Fury-FHD (Egami)", "wget https://raw.githubusercontent.com/islam-2412/IPKS/refs/heads/main/fury/installer.sh -O - | /bin/sh", True, "تثبيت سكين Fury-FHD."),
                ("FuryBissPro", "wget https://raw.githubusercontent.com/islam-2412/FuryBiss/refs/heads/main/fury/installer.sh -O - | /bin/sh", True, "جالب الفيدات"),
                ("GeminiPatcher", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/GeminiPatcher/geminipatcher.sh -O - | /bin/sh", True, "تثبيت GeminiPatcher."),
                ("gioppygio", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/gioppygio/gioppygio.sh -O - | /bin/sh", True, "تثبيت gioppygio."),
                ("GP4.2", "apt update && wget -O /tmp/geminilocale_all.deb http://download.blue-panel.com/geminilocale_gp4.php && apt install -y /tmp/geminilocale_all.deb", True, "حزمة Gemini الشهيرة التي تضيف العديد من الوظائف المتقدمة وأدوات الإدارة."),
                ("Gradient-fhd", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/skins-gradient-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Gradient-fhd."),
                ("GT IPTV Player Pro", "wget https://dreambox4u.com/emilnabil237/plugins/GT-IPTV-PlayerPro/GT-IPTV-PlayerPro.sh -O - | /bin/sh", True, "مشغل اكستريم iptv و بورتلات"),
                ("hardwareinfo", "wget https://dreambox4u.com/emilnabil237/plugins/hardwareinfo/installer.sh -O - | /bin/sh", True, "معلومات الهاردوير"),
                ("HasBahCa", "wget https://dreambox4u.com/emilnabil237/plugins/HasBahCa/installer.sh -O - | /bin/sh", True, "iptv مجاني"),
                ("HisnMuslim", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/hisnmuslim/hisnmuslim.sh -O - | /bin/sh", True, "حصن المسلم"),
                ("HistoryZapSelector", "wget https://dreambox4u.com/emilnabil237/plugins/historyzap/installer1.sh -O - | /bin/sh", True, "تصفح آخر القنوات"),
                ("HolidayCountdown", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/HolidayCountdown/installer.sh -O - | /bin/sh", True, "خاص بالأعياد"),
                ("HoloFHD Black", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/skins-for-dreambox/HoloFHD-Black.sh | /bin/sh", True, "Skin FHD لأجهزة DreamOS. مثبت المصدر يحاول تحديث الحزم ويثبت عدة مكونات Skin إضافية قبل فك الأرشيف؛ راجع الاعتماديات ومساحة التخزين."),
                ("horoscope", "wget https://raw.githubusercontent.com/emilnabil/horoscope/refs/heads/main/horoscope.sh -O - | /bin/sh", True, "الأبراج"),
                ("ImagesDownloader", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/ImagesDownloader/ImagesDownloader.sh | /bin/sh", True, "أداة تنزيل الصور/الملفات المرتبطة ببيئة Enigma2. سكربت المصدر يحذف مجلد الإضافة القديم قبل التثبيت؛ لا تنفّذه أثناء وجود تحديث أو عملية أ..."),
                ("ImagesDownloader - Mod Emil Nabil", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/ImagesDownloader/ImagesDownloader.sh -O - | /bin/sh", True, "تحميل الصور"),
                ("InfoBarWeather", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/InfoBarWeather/InfobarWeather.sh | /bin/sh", True, "إضافة عرض معلومات الطقس على شريط المعلومات. سكربت المصدر يزيل مجلد النسخة السابقة ويثبت curl عند الحاجة؛ التوافق يعتمد على صورة Enigma2."),
                ("Internet-SpeedTest", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/internet-speedtest.sh -O - | /bin/sh", True, "اختبار الإنترنت"),
                ("Ip2sat-By-Mosaad", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/ip2sat/ip2sat.sh -O - | /bin/sh", True, "مشاهدة iptv علي قنوات السات"),
                ("IP_Checker", "wget https://raw.githubusercontent.com/emil237/plugins/refs/heads/main/IP_Checker.sh -O - | /bin/sh", True, "معلومات IP الإنترنت"),
                ("IpAudio 6.7", "wget https://dreambox4u.com/emilnabil237/plugins/ipaudio/installer.sh -O - | /bin/sh", True, "py2) (مشغل صوتيات"),
                ("IpAudio 7.4", "wget https://dreambox4u.com/emilnabil237/plugins/ipaudio/ipaudio-7.4-ffmpeg.sh -O - | /bin/sh", True, "py3) (مشغل صوتيات"),
                ("IpAudio 8.02 By-M-Nasr", "wget https://github.com/emil237/ipaudio/raw/refs/heads/main/ipaudio_8.0.sh -O - | /bin/sh", True, "All python) ( مشغل صوتيات"),
                ("IpAudio By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/ipaudio/main/installer-ipaudio.sh -O - | /bin/sh", True, "Py3) (مشغل صوتيات"),
                ("IPAudio Pro", "wget https://raw.githubusercontent.com/emilnabil/ipaudiopro/refs/heads/main/ipaudiopro.sh -O - | /bin/sh", True, "إضافة أدوات صوتية لأجهزة Enigma2."),
                ("IPAudioPlus", "wget -q -O - https://raw.githubusercontent.com/Ahmadarjan1/IPAudioPlus-Releases/main/installer.sh | /bin/sh", True, "نسخة مطورة من خدمات الصوت عبر الإنترنت مع واجهة أكثر سهولة ودعماً لعدد أكبر من المصادر."),
                ("IpAudioPro Latest Version", "wget https://github.com/zKhadiri/IPAudioPro-Releases-/raw/refs/heads/main/installer.sh -O - | /bin/sh", True, "مشغل صوتيات"),
                ("IpAudioPro_1.5", "wget https://github.com/emilnabil/ipaudiopro/raw/refs/heads/main/ipaudiopro.sh -O - | /bin/sh", True, "مشغل صوتيات"),
                ("ipsat", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/ipsat.sh -O - | /bin/sh", True, "تثبيت ipsat."),
                ("IpStreamer By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/ipstreamer/main/installer-ipstreamer.sh -O - | /bin/sh", True, "Py3) (مشغل صوتيات"),
                ("Iptosat_v1.8", "wget https://dreambox4u.com/emilnabil237/plugins/iptosat/installer.sh -O - | /bin/sh", True, "مشاهدة iptv علي قنوات السات"),
                ("Iptosat_v1.9-Modded-by-Emil", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/iptosat/iptosat_1.9.sh -O - | /bin/sh", True, "مشاهدة iptv علي قنوات السات"),
                ("Iptv-Org-Playlists", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/iptv-org-playlists/iptv-org-playlists.sh -O - | /bin/sh", True, "تثبيت Iptv-Org-Playlists."),
                ("iptvdream", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/main/iptvdream/iptvdream.sh -O - | /bin/sh", True, "مشغل m3u"),
                ("IptvPlayer", "wget https://raw.githubusercontent.com/emil237/iptvplayer/main/iptvinstaller.sh -O - | /bin/sh", True, "مشغل ،iptv"),
                ("Jedi Maker Xtream", "wget -qO- https://raw.githubusercontent.com/biko-73/JediMakerXtream/main/installer.sh | /bin/sh", True, "إدارة قوائم Xtream وتحويلها إلى قوائم IPTV مناسبة لبيئات Enigma2 المتوافقة."),
                ("JediEpgExtream", "wget https://dreambox4u.com/emilnabil237/plugins/jediepgextream/installer.sh -O - | /bin/sh", True, "نقل الدليل الي ال iptv"),
                ("JediMakerXtream", "wget -q --no-check-certificate -O /tmp/install_jedimaker.sh 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/install_jedimaker.sh' && chmod 755 /tmp/install_jedimaker.sh && sh /tmp/install_jedimaker.sh", True, "تثبيت بلجن JediMakerXtream لإدارة اشتراكات IPTV."),
                ("KeyAdder", "wget https://raw.githubusercontent.com/fairbird/KeyAdder/main/installer.sh -O - | /bin/sh", True, "مفاتيح الشفرات"),
                ("KeyAdder (Online4Tech)", "wget -q --no-check-certificate -O /tmp/install_keyadder.sh 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/install_keyadder.sh' && chmod 755 /tmp/install_keyadder.sh && sh /tmp/install_keyadder.sh", True, "تثبيت بلجن KeyAdder لإدخال الشفرات."),
                ("Klll-Pro-FHD", "wget https://raw.githubusercontent.com/biko-73/zelda77/main/installer.sh -O - | /bin/sh", True, "تثبيت سكين Klll-Pro-FHD."),
                ("levi45-AddonsManager", "wget https://dreambox4u.com/emilnabil237/plugins/levi45-addonsmanager/installer.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("levi45-free-iptv", "wget https://raw.githubusercontent.com/emil237/plugins/refs/heads/main/levi45-free-iptv/levi45-freeiptv.sh -O - | /bin/sh", True, "IPTV مجاني"),
                ("levi45-freeserver", "wget https://raw.githubusercontent.com/emil237/plugins/refs/heads/main/levi45-freeserver/levi45-freeserver.sh -O - | /bin/sh", True, "CCCam مجاني"),
                ("levi45-settings", "wget https://dreambox4u.com/emilnabil237/plugins/levi45-settings/levi45-settings.sh -O - | /bin/sh", True, "ملف القنوات"),
                ("Levi45MulticamManager", "wget https://dreambox4u.com/emilnabil237/plugins/levi45multicammanager/installer.sh -O - | /bin/sh", True, "لوحة تحميل الكامات"),
                ("LinuxSat Panel", "wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/LinuxsatPanel/main/installer.sh -O - | /bin/bash", True, "إحدى أشهر لوحات إدارة الإضافات والأدوات والتحديثات لأجهزة إنجما2."),
                ("LiveFeed", "wget https://live-feed.net/enigma2/installer.sh -O - | /bin/sh", True, "تثبيت LiveFeed."),
                ("LiveMatch", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/livematch/livematch.sh -O - | /bin/sh", True, "عرض نتائج الرياضة"),
                ("m3uconverter", "wget https://raw.githubusercontent.com/Belfagor2005/Archimede-M3UConverter/main/installer.sh -O - | /bin/sh", True, "تحويل m3u الي مفضلات"),
                ("Magic-FHD", "wget https://dreambox4u.com/emilnabil237/skins/openvix/skins-openvix-magic-fhd.sh -O - | /bin/sh", True, "تثبيت سكين Magic-FHD."),
                ("MagicPanelMax", "wget -q --no-check-certificate https://raw.githubusercontent.com/Ham-ahmed/G12/refs/heads/main/MagicPanelMax-install.sh -O - | /bin/sh", True, "لوحة متقدمة تجمع الأدوات والإضافات والخدمات الشائعة في واجهة موحدة."),
                ("malek-fhd (OpenATV)", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/main/ATV/skins-malek-fhd_2.2_py3.11.2-py3.12.1.sh -O - | /bin/sh", True, "تثبيت سكين malek-fhd."),
                ("malek-fhd (OpenPLi Py3)", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/main/pli/Skin-malek-fhd_1.2.sh -O - | /bin/sh", True, "تثبيت سكين malek-fhd."),
                ("Mawaqit", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/Mawaqit/Mawaqit.sh | /bin/sh", True, "إضافة Mawaqit لعرض مواقيت الصلاة. سكربت المصدر يحذف مجلد الإضافة السابق قبل فك الأرشيف؛ راجع التوافق وخذ نسخة احتياطية."),
                ("Maxy-FHD (OpenATV)", "wget https://raw.githubusercontent.com/popking159/skins/refs/heads/main/maxyatv/installer.sh -O - | /bin/sh", True, "تثبيت سكين Maxy-FHD."),
                ("Maxy-FHD (OpenPLi Py2)", "wget https://dreambox4u.com/emilnabil237/skins/script/skins-Maxy-FHD.sh -O - | /bin/sh", True, "تثبيت سكين Maxy-FHD."),
                ("MenuSort", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/menusort.sh -O - | /bin/sh", True, "ترتيب القائمة"),
                ("Metrix Poster", "wget -q --no-check-certificate https://gitlab.com/hmeng80/addons/-/raw/main/metrix-fhd-parts-ec.sh -O - | /bin/sh", True, "إضافات ومكونات لواجهة MetrixHD تضيف بوسترات وأشكال عرض حديثة للقنوات والأفلام."),
                ("MetrixFHD-Extraevent-PosterXD", "wget https://dreambox4u.com/emilnabil237/skins/openatv/SKIN-MetrixFHD-OpenATV-Extraevent-PosterX.sh -O - | /bin/sh", True, "تثبيت سكين MetrixFHD-Extraevent-PosterXD."),
                ("MetrixHD Skin", "wget -q --no-check-certificate -O /tmp/skin_metrix.sh 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/skin_metrix.sh' && chmod 755 /tmp/skin_metrix.sh && sh /tmp/skin_metrix.sh", True, "تثبيت سكين MetrixHD من فيد الصورة."),
                ("MetrixPoster-By_MNASR", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/MetrixPoster-By_MNASR/installer.sh -O - | /bin/sh", True, "تثبيت سكين MetrixPoster-By_MNASR."),
                ("MmPicons", "wget https://raw.githubusercontent.com/Belfagor2005/mmPicons/main/installer.sh -O - | /bin/sh", True, "تحميل البيكونات"),
                ("Mohamed Store", "wget -O - https://raw.githubusercontent.com/wwwgoper77-wq/MohamedStore/main/install.sh | sh", True, "متجر إضافات عربي يتيح تثبيت وتحديث العديد من البلجنات من مكان واحد."),
                ("Mohammed Skin", "wget -q --no-check-certificate https://raw.githubusercontent.com/mido00020/MohammedSkin/main/installer.sh -O - | /bin/sh", True, "سكين عربي حديث يتميز بتصميم أنيق وخفيف مع دعم أغلب إضافات Enigma2."),
                ("Moviebrowser", "wget https://github.com/OwnerPlugins/MovieBrowser/raw/refs/heads/main/installer.sh -O - | /bin/sh", True, "تثبيت Moviebrowser."),
                ("MoviesManager", "wget http://dreambox4u.com/dreamarabia/Transmission_e2/MoviesManager.sh -O - | /bin/sh", True, "مدير افلام"),
                ("Multi-Iptv-Adder_By-Emil", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/MultiIptvAdder/installer.sh -O - | /bin/sh", True, "إدخال IPTV"),
                ("Multi-Stalker", "wget https://raw.githubusercontent.com/biko-73/Multi-Stalker/main/pro/installer.sh -O - | /bin/sh", True, "إضافة مرتبطة بخدمات Stalker على Enigma2."),
                ("MultiCamAdder", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/MultiCamAdder/installer.sh -O - | /bin/sh", True, "إضافة لإدارة وإضافة أنظمة SoftCam المختلفة وتسهيل التبديل بينها."),
                ("MultiStalkerPro", "wget https://raw.githubusercontent.com/emilnabil/multi-stalkerpro/main/installer.sh -O - | /bin/sh", True, "مشغل بورتلات"),
                ("MX Maestra Black Weather", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/Skin-MX_Maestra_Black_weather/Skin-MX_Maestra_Black_weather.sh | /bin/sh", True, "ملف السكين المخصص لبيئات Python 3.12 فقط. لا تستخدمه مع إصدار Python مختلف؛ سكربت التثبيت يحذف مجلد السكين والحزمة السابقة."),
                ("MX-Sline-Black-Red-Gradient", "wget https://dreambox4u.com/emilnabil237/skins/obh/mx-sline-black-red-gradient_py3.12.sh -O - | /bin/sh", True, "تثبيت سكين MX-Sline-Black-Red-Gradient."),
                ("Mx-Sline-Glass-Gradient", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/skins-mx-sline-glass-gradient.sh -O - | /bin/sh", True, "تثبيت سكين Mx-Sline-Glass-Gradient."),
                ("MX_BlackSea", "wget https://dreambox4u.com/emilnabil237/skins/obh/skins-MX_BlackSea.sh -O - | /bin/sh", True, "تثبيت سكين MX_BlackSea."),
                ("MX_GrayDots_X2B_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/MX_GrayDots_X2B_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين MX_GrayDots_X2B_OBH."),
                ("MX_GreenDots_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/MX_GreenDots_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين MX_GreenDots_OBH."),
                ("MX_HQ7_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/MX_HQ7_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين MX_HQ7_OBH."),
                ("MX_Maestra2b_weather", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/MX_Maestra2b_weather_5.0.sh -O - | /bin/sh", True, "تثبيت سكين MX_Maestra2b_weather."),
                ("MX_Maestra_Black_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/MX_Maestra_Black_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين MX_Maestra_Black_OBH."),
                ("MX_Sline-Blue", "wget https://dreambox4u.com/emilnabil237/skins/obh/MX_Sline-Blue_OBH_5.4_py3.12_py3.12.sh -O - | /bin/sh", True, "تثبيت سكين MX_Sline-Blue."),
                ("MX_Sline-Red_X2", "wget https://dreambox4u.com/emilnabil237/skins/obh/MX_Sline-Red_X2_py3.12.sh -O - | /bin/sh", True, "تثبيت سكين MX_Sline-Red_X2."),
                ("my translator_By Ismail elkhooly", "wget https://github.com/emilnabil/mytranslator/raw/refs/heads/main/mytranslator.sh -O - | /bin/sh", True, "مترجم"),
                ("My-tsiplayer", "wget -q \"--no-check-certificate\" https://github.com/angelheart150/My-tsiplayer/raw/main/install-tsiplayer-update-hosts.sh -O - | /bin/sh", True, "إضافة وسائط ومضيفين لـ Enigma2 من المستودع المقدم."),
                ("MyCam-Plugin", "wget https://dreambox4u.com/emilnabil237/plugins/mycam/installer.sh -O - | /bin/sh", True, "إدخال سيرفر CCCam"),
                ("MyHits-By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/myhits/refs/heads/main/myinstaller.sh -O - | /bin/sh", True, "مشغل اغاني"),
                ("MyMetrixLiteBackup", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/MyMetrixLiteBackup.sh -O - | /bin/sh", True, "تثبيت سكين MyMetrixLiteBackup."),
                ("MyStreamer", "wget -qO - https://raw.githubusercontent.com/popking159/MyStreamer/refs/heads/main/myinstaller.sh | /bin/sh", True, "مشغل IPTV متطور يدعم القنوات المباشرة ومكتبات الفيديو مع واجهة عربية سهلة الاستخدام."),
                ("MyTranslator", "wget -O /tmp/mytranslator.ipk https://github.com/ismailelkhooly/Ismail-/raw/refs/heads/main/enigma2-plugin-extensions-mytranslator_1.75.ipk && opkg install --force-reinstall /tmp/mytranslator.ipk", True, "مترجم متعدد اللغات لترجمة النصوص والقوائم داخل إضافات Enigma2."),
                ("Nacht_1.7.3", "wget http://dreambox4u.com/emilnabil237/script/SKIN-ATV-nacht_1.7.3.sh -O - | /bin/sh", True, "تثبيت سكين Nacht_1.7.3."),
                ("Nacht_7.1", "wget https://dreambox4u.com/emilnabil237/skins/openatv/nacht_7.1.sh -O - | /bin/sh", True, "تثبيت سكين Nacht_7.1."),
                ("Ncam_v15.7", "wget https://dreambox4u.com/emilnabil237/emu/installer-ncam_v15.7.sh -O - | /bin/sh", True, "تثبيت Ncam_v15.7."),
                ("Net Usage Pro", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/netusagepro/netusagepro.sh -O - | /bin/sh", True, "معلومات الإنترنت"),
                ("NewVirtualkeyBoard", "wget https://dreambox4u.com/emilnabil237/plugins/NewVirtualKeyBoard/installer.sh -O - | /bin/sh", True, "كيبورد متقدم"),
                ("NewVirtualKeyBoard", "wget -q --no-check-certificate -O /tmp/install_virtualkb.sh 'https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/install_virtualkb.sh' && chmod 755 /tmp/install_virtualkb.sh && sh /tmp/install_virtualkb.sh", True, "تثبيت لوحة المفاتيح الافتراضية الجديدة."),
                ("NitroAdvance-FHD", "wget https://raw.githubusercontent.com/biko-73/TeamNitro/main/script/installerN.sh -O - | /bin/sh", True, "تثبيت سكين NitroAdvance-FHD."),
                ("NovaCamPro", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/novacampro.sh -O - | /bin/sh", True, "تثبيت NovaCamPro."),
                ("Novaler Downloader", "wget https://raw.githubusercontent.com/popking159/novalerdownloader/refs/heads/main/myinstaller.sh -O - | /bin/sh", True, "تثبيت Novaler Downloader."),
                ("novalerStore", "wget -q \"--no-check-certificate\" https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/novalerStore.sh -O - | /bin/sh", True, "تثبيت novalerStore."),
                ("NovalerTv", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/novalertv.sh -O - | /bin/sh", True, "تثبيت NovalerTv."),
                ("NovaTv", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/novatv.sh -O - | /bin/sh", True, "تثبيت NovaTv."),
                ("NumberZapExt", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/NumberZapExt/NumberZapExt.sh | /bin/sh", True, "إضافة موسعة للتعامل مع التنقل بالأرقام بين القنوات. سكربت المصدر يحذف مجلد SystemPlugins السابق قبل التثبيت؛ لا تستخدمه إلا بعد التأكد من..."),
                ("Oaweather", "wget https://raw.githubusercontent.com/biko-73/OAWeather/main/installer.sh -O - | /bin/sh -O - | /bin/sh", True, "معلومات الطقس"),
                ("Obsidian FHD", "wget -qO- https://raw.githubusercontent.com/dali44g/Obsidian-FHD/main/install.sh | sh", True, "سكين Full HD احترافي بواجهة عصرية ومعلومات موسعة عن القنوات والمحتوى."),
                ("ONEupdater", "wget https://raw.githubusercontent.com/Sat-Club/ONEupdaterE2/main/installer.sh -O - | /bin/sh", True, "تثبيت ONEupdater."),
                ("Op-Artkoala-FHD", "wget https://dreambox4u.com/emilnabil237/skins/openatv/skins-op-artkoala.sh -O - | /bin/sh", True, "تثبيت سكين Op-Artkoala-FHD."),
                ("OpenBhGreenFHD", "wget https://dreambox4u.com/emilnabil237/skins/obh/skin_OpenBhGreenFHD.sh -O - | /bin/sh", True, "تثبيت سكين OpenBhGreenFHD."),
                ("OrangeAudio", "wget -qO- https://raw.githubusercontent.com/popking159/OrangeAudio/main/installer.sh | sh", True, "مشغل صوتي متطور يدعم البث الصوتي عبر الإنترنت ومحطات الراديو المختلفة."),
                ("OrangeAudioPlugin-By-M-Nasr", "wget https://raw.githubusercontent.com/popking159/OrangeAudio/refs/heads/main/installer.sh -O - | /bin/sh", True, "اضافة صوتيات اورانج و فاميلي"),
                ("Oscam By Levi45", "wget https://raw.githubusercontent.com/levi-45/Levi45Emulator/main/installer.sh -O - | /bin/sh", True, "تثبيت Oscam By Levi45."),
                ("Ozeta-Skins-Setup", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/main/PLUGIN_Skin-ozeta.sh -O - | /bin/sh", True, "إعدادات الثيم"),
                ("Ozeta-Xtra (OpenATV)", "wget http://dreambox4u.com/emilnabil237/script/SKIN-ATV-ozeta-xtra.sh -O - | /bin/sh", True, "تثبيت سكين Ozeta-Xtra."),
                ("Ozeta-Xtra (OpenPLi Py2)", "wget http://dreambox4u.com/emilnabil237/script/SKIN-PLI-ozeta-xtra.sh -O - | /bin/sh", True, "تثبيت سكين Ozeta-Xtra."),
                ("Panelaio", "wget https://raw.githubusercontent.com/OliOli2013/PanelAIO-Plugin/main/installer.sh -O - | /bin/sh", True, "لوحة تحميل أضافات"),
                ("Picons", "URL=\"https://github.com/picons/picons/releases/download/2026-10-25--00-12-17/srp-full.220x132-190x102.light.on.transparent_2026-10-25--00-12-17.hardlink.tar.xz\"; [ -d /media/hdd ] && BASE=/media/hdd || { [ -d /media/usb ] && BASE=/media/usb || { [ -d /media/mmc ] && BASE=/media/mmc || BASE=/usr/share/enigma2; }; }; mkdir -p $BASE/picon && cd /tmp && wget -O picons.tar.xz \"$URL\" && tar -xJf picons.tar.xz -C $BASE/picon --strip-components=1 && rm -rf /usr/share/enigma2/picon && ln -sfn $BASE/picon /usr/share/enigma2/picon && rm -f picons.tar.xz && sync && killall -9 enigma2", True, "عرض شعارات القنوات داخل الواجهة أو قائمة القنوات حسب إعدادات الصورة والسكين."),
                ("PiconsRename", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/PiconsRename/PiconsRename.sh -O - | /bin/sh", True, "تحويل البيكونات بالاسم"),
                ("PluginBrowser-Grid-Pli_8.3", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/PluginBrowser-Grid/pluginbrowser-grid-pli_8.3.sh -O - | /bin/sh", True, "تثبيت PluginBrowser-Grid-Pli_8.3."),
                ("PluginBrowser-Grid-V2_All-Py3 (OpenBH-Vix-Pli)", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/PluginBrowser-Grid/pluginbrowser-grid-v2.sh -O - | /bin/sh", True, "تثبيت PluginBrowser-Grid-V2_All-Py3 (OpenBH-Vix-Pli)."),
                ("PluginMover", "wget http://dreambox4u.com/emilnabil237/plugins/pluginmover/installer.sh -O - | /bin/sh", True, "نقل الإضافات للخارجي"),
                ("PluginSkinMover", "wget http://dreambox4u.com/emilnabil237/plugins/pluginskinmover/installer.sh -O - | /bin/sh", True, "نقل الثيمات للخارجي"),
                ("Plutotv", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/main/plutotv/plutotv.sh -O - | /bin/sh", True, "تثبيت Plutotv."),
                ("Premium-Black-Fhd (Egami)", "wget https://dreambox4u.com/emilnabil237/skins/script/SKIN-egami-premium--black-fhd-py3.sh -O - | /bin/sh", True, "تثبيت سكين Premium-Black-Fhd."),
                ("Premium-Blue-Fhd (Egami)", "wget https://dreambox4u.com/emilnabil237/skins/script/SKIN-egami-premium--blue-fhd-py3.sh -O - | /bin/sh", True, "تثبيت سكين Premium-Blue-Fhd."),
                ("Premium-Magenta-Fhd (Egami)", "wget https://dreambox4u.com/emilnabil237/skins/script/SKIN-egami-premium-fhd-py3.sh -O - | /bin/sh", True, "تثبيت سكين Premium-Magenta-Fhd."),
                ("QATAR-2022-V3-FHD", "wget http://dreambox4u.com/emilnabil237/script/SKIN-PLI-QATAR-2022-V3-FHD.sh -O - | /bin/sh", True, "تثبيت سكين QATAR-2022-V3-FHD."),
                ("qatar2022", "wget https://dreambox4u.com/emilnabil237/plugins/xtreamity/installer-skin-qatar.sh -O - | /bin/sh", True, "تثبيت سكين qatar2022."),
                ("QuadPip", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/QuadPip/QuadPip.sh | /bin/sh", True, "إضافة وظائف العرض متعدد النوافذ (Quad PiP) للأجهزة والصور المتوافقة. سكربت المصدر يزيل الحزمة ومجلد الإضافة القديمين قبل التثبيت."),
                ("Quarter pounder", "wget http://dreambox4u.com/emilnabil237/script/quarterpounder.sh -O - | /bin/sh", True, "تنشيط قنوات ال iptv"),
                ("QuickSignal - iet5", "wget https://raw.githubusercontent.com/Saiedf/QuickSignalIet5/main/installer_quicksignaliet5_auto.sh -O - | /bin/sh", True, "بيان إشارة للقنوات"),
                ("Quran Kareem", "wget https://raw.githubusercontent.com/MOHAMED19OS/Download/main/Quran/installer.sh -qO - | /bin/sh", True, "إضافة القرآن الكريم لأجهزة Enigma2؛ راجع صفحة الإضافة لمعرفة الخصائص وطريقة الاستخدام."),
                ("Quran Kareem-By-M-Nasr", "wget https://raw.githubusercontent.com/emil237/quran/main/installer.sh -O - | /bin/sh", True, "القرآن الكريم"),
                ("Quran-karem", "wget https://dreambox4u.com/emilnabil237/plugins/quran/installer.sh -O - | /bin/sh", True, "القرآن الكريم"),
                ("Radio-80-s", "wget https://raw.githubusercontent.com/Belfagor2005/Radio-80-s/main/installer.sh -O - | /bin/sh", True, "راديو"),
                ("Radio-Stream-Relay", "wget https://raw.githubusercontent.com/angelheart150/RadioRelay/main/installer.sh -O - | /bin/sh", True, "راديو و استريم"),
                ("RadioGit", "wget https://dreambox4u.com/emilnabil237/plugins/radiogit/radiogit.sh -O - | /bin/sh", True, "ستريم محطات راديو"),
                ("Radiom", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/main/radiom/radiom.sh -O - | /bin/sh", True, "ستريم محطات راديو"),
                ("RaedQuickSignal", "opkg update && opkg install wget && wget https://raw.githubusercontent.com/fairbird/RaedQuickSignal/main/installer.sh -O - | /bin/sh", True, "أداة للوصول السريع إلى معلومات إشارة الاستقبال."),
                ("Rakutentv", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/main/rakutentv/rakutentv.sh -O - | /bin/sh", True, "تثبيت Rakutentv."),
                ("ReaderManager", "wget https://raw.githubusercontent.com/ismail9875/ReaderManager/main/installer.sh -O - | /bin/sh", True, "مدير السيرفرات"),
                ("S4a Updater", "wget http://s4aupdater.one.pl/instalujs4aupdater.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("SamsungTvPlus", "wget http://dreambox4u.com/emilnabil237/plugins/samsungtvplus/samsungtvplus.sh -O - | /bin/sh", True, "iptv مجاني"),
                ("SatelliWebLiveFeeds_py3.12", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/satelliweblivefeeds/satelliweblivefeeds-py3.12.sh -O - | /bin/sh", True, "فيدات"),
                ("SatelliWebLiveFeeds_py3.13", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/satelliweblivefeeds/satelliweblivefeeds-py3.13.sh -O - | /bin/sh", True, "فيدات"),
                ("SatVenusPanel", "wget https://dreambox4u.com/emilnabil237/plugins/satvenuspanel/installer.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("Screen-Recorder-By-Emil", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/screenrecorder/installer.sh -O - | /bin/sh", True, "تسجيل الشاشة"),
                ("ScreenNames", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/screennames/screennames.sh -O - | /bin/sh", True, "اسم الشاشة"),
                ("scriptexecuter", "wget http://dreambox4u.com/emilnabil237/plugins/scriptexecuter/installer.sh -O - | /bin/sh", True, "تشغيل السكريبت"),
                ("ScSearch", "wget https://raw.githubusercontent.com/OwnerPlugins/scsearch/main/installer.sh -O - | /bin/sh", True, "مشاهدة الافلام"),
                ("Server EagleSat", "wget -qO- --no-check-certificate https://raw.githubusercontent.com/eliesat/ServerEagleSat/main/installer.sh | bash", True, "خدمة وأدوات إضافية خاصة بمنصة EagleSat لتوسيع وظائف الجهاز."),
                ("ServerColoring", "wget https://github.com/islam-2412/ServerColoring/raw/refs/heads/main/fury/installer.sh -O - | /bin/sh", True, "تلوين القنوات المشفرة"),
                ("ServiceScanUpdates", "wget https://dreambox4u.com/emilnabil237/plugins/servicescanupdates/servicescanupdates.sh -O - | /bin/sh", True, "معلومات بحث القنوات"),
                ("ServiceScanUpdates - iet5", "wget https://raw.githubusercontent.com/Saiedf/ServiceScanUpdatesIet5/main/installer_servicescanupdatesiet5_auto.sh -O - | /bin/sh", True, "معلومات بحث القنوات"),
                ("Sherlockmod", "wget https://raw.githubusercontent.com/emil237/sherlockmod/main/installer.sh -O - | /bin/sh", True, "أضافة انفوبار 2 به معلومات"),
                ("ShiaVoice", "wget https://raw.githubusercontent.com/kongon13/Shiavoice-enigma2/main/install.sh -O - | /bin/sh", True, "اصوات قرأن وادعية"),
                ("showclock", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/showclock/showclock.sh -O - | /bin/sh", True, "ساعة"),
                ("SilentRunner", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/SilentRunner/SilentRunner.sh -O - | /bin/sh", True, "تشغيل سكريبتات صامت"),
                ("Simple-Zoom-Panel", "wget https://dreambox4u.com/emilnabil237/plugins/simple-zoom-panel/installer.sh -O - | /bin/sh", True, "سيرفرات مجانية"),
                ("SimplySports", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/SimplySports/SimplySports.sh -O - | /bin/sh", True, "معلومات رياضة"),
                ("Skyline", "wget https://github.com/emilnabil/skins-spa/raw/refs/heads/main/skin-Skyline.sh -O - | /bin/sh", True, "تثبيت سكين Skyline."),
                ("SLwebcams", "wget https://raw.githubusercontent.com/OwnerPlugins/SLwebcams/main/installer.sh -O - | /bin/sh", True, "تثبيت SLwebcams."),
                ("SmartAddons Panel Pro", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/SmartAddonspanel/smart-Panel.sh -O - | /bin/sh", True, "إصدار متطور من لوحة SmartAddons مزود بأدوات إضافية."),
                ("SmartAddonspanel (HAN)", "wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/Ham-ahmed/Secript-Panel/main/1New-Ajpanel-Panel-v5.0_HAN.sh -O - | /bin/sh", True, "نسخة SmartAddonspanel من مستودع HAN."),
                ("SPIDERMAN-FHD", "wget http://dreambox4u.com/emilnabil237/script/SKIN-PLI-SPIDERMAN-FHD.sh -O - | /bin/sh", True, "تثبيت سكين SPIDERMAN-FHD."),
                ("Spinner-Selector-All-Python", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/SpinnerSelector/spinner-selector.sh -O - | /bin/sh", True, "تحميل الدوار"),
                ("SSupport", "wget -q --no-check-certificate https://github.com/popking159/ssupport/raw/main/subssupport-install.sh -O - | /bin/sh", True, "إضافة لتحميل وإدارة الترجمات للمحتوى المرئى."),
                ("StalkerPortalConverter", "wget https://raw.githubusercontent.com/Belfagor2005/StalkerPortalConverter/main/installer.sh -O - | /bin/sh", True, "تحويل بورتلات لمفضلات"),
                ("SubExtractor Lite", "wget https://raw.githubusercontent.com/Arian7s/SubExtractorLite/main/installer.sh -O - | /bin/sh", True, "أداة لاستخراج الترجمات المدمجة من ملفات الفيديو وإنشاء ملفات ترجمة مستقلة."),
                ("SubsSupport", "wget -q \"--no-check-certificate\" https://github.com/popking159/ssupport/raw/main/subssupport-install.sh -O - | /bin/sh", True, "أداة لدعم الترجمة وملفاتها في Enigma2."),
                ("SubsSupport_1.5.8-r9", "wget https://dreambox4u.com/emilnabil237/plugins/SubsSupport/installer1.sh -O - | /bin/sh", True, "ترجمة الأفلام"),
                ("SubsSupport_2.1", "wget https://dreambox4u.com/emilnabil237/plugins/SubsSupport/subssupport_2.1.sh -O - | /bin/sh", True, "ترجمة الأفلام"),
                ("SubsSupport_by-m.nasr", "wget https://github.com/popking159/ssupport/raw/main/subssupport-install.sh -O - | /bin/sh", True, "ترجمة الأفلام"),
                ("SubsSupportPro", "wget https://github.com/popking159/SubsSupportPro/raw/refs/heads/main/myinstaller.sh -O - | /bin/sh", True, "أدوات دعم الترجمة وإدارة ملفات الترجمة أثناء تشغيل الوسائط."),
                ("SuperBackupImages_by Emil Nabil", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/SuperBackupImages/SuperBackupImages.sh -O - | /bin/sh", True, "تحميل الإضافات"),
                ("Suptv", "wget https://raw.githubusercontent.com/emil237/suptv/main/installer.sh -O - | /bin/sh", True, "تثبيت Suptv."),
                ("TeamNitro", "wget https://raw.githubusercontent.com/biko-73/TeamNitro/main/script/installerB.sh -O - | /bin/sh", True, "مجموعة أدوات وخدمات إضافية لأجهزة Enigma2."),
                ("TeamNitro Control", "wget https://gitlab.com/emilnabil1/teamnitro/-/raw/main/SKIN-teamnitro.sh -O - | /bin/sh", True, "تثبيت سكين TeamNitro Control."),
                ("TheWeather-iet5", "wget https://raw.githubusercontent.com/Saiedf/TheWeatherIet5/main/installer_theweatheriet5_auto.sh -O - | /bin/sh", True, "الطقس"),
                ("TitloviBrowser", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/TitloviBrowser/main/installer.sh -O - | /bin/sh", True, "تثبيت TitloviBrowser."),
                ("TiViMate", "wget -qO- https://raw.githubusercontent.com/opesboy/TiviMateE2/main/install.sh | sh", True, "نسخة محسنة من تجربة TiviMate لأجهزة Enigma2 مع دعم القوائم الحديثة والتنقل السريع."),
                ("TiviMateE2", "wget https://raw.githubusercontent.com/opesboy/TiviMateE2/main/install.sh -O - | /bin/sh", True, "مشغل اشتراكات iptv"),
                ("TMBD", "wget https://raw.githubusercontent.com/biko-73/TMBD/main/installer.sh -O - | /bin/sh", True, "إضافة مرتبطة ببيانات الأفلام والمعلومات الوصفية."),
                ("Tmdb", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/tmdb.sh -O - | /bin/sh", True, "خاص بالترجمة"),
                ("TOKYO2020-FHD", "wget https://raw.githubusercontent.com/emil237/skins-enigma2/main/pli/SKIN-TOKYO2020-FHD-By-Muaath.sh -O - | /bin/sh", True, "تثبيت سكين TOKYO2020-FHD."),
                ("Total90", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/total90.sh -O - | /bin/sh", True, "تثبيت Total90."),
                ("Toys", "wget https://dreambox4u.com/emilnabil237/plugins/xtreamity/installer-skin-toys.sh -O - | /bin/sh", True, "تثبيت سكين Toys."),
                ("Transmission_E2", "wget http://dreambox4u.com/emilnabil237/plugins/Transmission/Transmission_e2.sh -O - | /bin/sh", True, "iptv مجاني"),
                ("Tspanel", "wget https://dreambox4u.com/emilnabil237/plugins/tspanel/installer.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("TvAddon-Panel", "wget https://dreambox4u.com/emilnabil237/plugins/tvaddon/installer.sh -O - | /bin/sh", True, "لوحة تحميل الإضافات"),
                ("TvDream", "wget https://raw.githubusercontent.com/Belfagor2005/tvDream/main/installer.sh -O - | /bin/sh", True, "تثبيت TvDream."),
                ("TvGarden", "wget https://raw.githubusercontent.com/OwnerPlugins/TVGarden/main/installer.sh -O - | /bin/sh", True, "iptv مجاني"),
                ("TvManager", "wget https://raw.githubusercontent.com/Belfagor2005/tvManager/main/installer.sh -O - | /bin/sh", True, "مدير القنوات"),
                ("TvParsa", "wget https://raw.githubusercontent.com/Belfagor2005/tvParsa/main/installer.sh -O - | /bin/sh", True, "تثبيت TvParsa."),
                ("TvRaiPreview", "wget https://raw.githubusercontent.com/Belfagor2005/tvRaiPreview/main/installer.sh -O - | /bin/sh", True, "تثبيت TvRaiPreview."),
                ("UltraAudio", "wget -qO- https://raw.githubusercontent.com/K3bOra/UltraAudio/main/install.sh | /bin/sh", True, "حزمة متكاملة لتحسين وظائف الصوت وتوفير خيارات استماع إضافية داخل الجهاز."),
                ("Ultracam", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/novaler/ultracam.sh -O - | /bin/sh", True, "تثبيت Ultracam."),
                ("UltraStalker", "wget -qO- https://raw.githubusercontent.com/K3bOra/-UltraStalker/main/install.sh | /bin/sh", True, "إضافة متخصصة لدعم بوابات Stalker Portal مع أداء عالٍ واستقرار أثناء المشاهدة."),
                ("vavoo", "wget https://dreambox4u.com/emilnabil237/plugins/vavoo/installer.sh -O - | /bin/sh", True, "تثبيت vavoo."),
                ("Vixbmc-1080-Confluence-FHD", "wget https://dreambox4u.com/emilnabil237/skins/openvix/skins-openvix-vixbmc-1080-confluence.sh -O - | /bin/sh", True, "تثبيت سكين Vixbmc-1080-Confluence-FHD."),
                ("WAR-S-FHD", "wget http://dreambox4u.com/emilnabil237/script/SKIN-PLI-WAR-S-FHD.sh -O - | /bin/sh", True, "تثبيت سكين WAR-S-FHD."),
                ("Waves4_Fire_weather_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/Waves4_Fire_weather_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين Waves4_Fire_weather_OBH."),
                ("Waves4_weather_OBH", "wget https://github.com/emilnabil/skins-obh/raw/refs/heads/main/Waves4_weather_OBH_5.0.sh -O - | /bin/sh", True, "تثبيت سكين Waves4_weather_OBH."),
                ("Weather Plugin", "opkg update && opkg install enigma2-plugin-extensions-weatherplugin", True, "عرض حالة الطقس والتوقعات عبر خدمات ومصادر تدعمها الإضافة."),
                ("WeatherMsn", "wget http://dreambox4u.com/emilnabil237/plugins/weathermsn/installer.sh -O - | /bin/sh", True, "الطقس"),
                ("WebCamE2PrenjSF", "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/WebCamE2PrenjSF/main/installer.sh -O - | /bin/sh", True, "تثبيت WebCamE2PrenjSF."),
                ("Wifi-Manager", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/wifimanager/wifimanager.sh -O - | /bin/sh", True, "مدير الواي فاي"),
                ("Wireguard-Vpn", "wget https://github.com/m4dhouse/Wireguard-Vpn/raw/refs/heads/python-3.13/WireGuard.sh -O - | /bin/sh", True, "تثبيت Wireguard-Vpn."),
                ("WorldCam", "wget https://raw.githubusercontent.com/Belfagor2005/WorldCam/main/installer.sh -O - | /bin/sh", True, "كاميرات حول العالم"),
                ("Xc_Plugin_Forever", "wget https://raw.githubusercontent.com/Belfagor2005/xc_plugin_forever/main/installer.sh -O - | /bin/sh", True, "مشغل iptv"),
                ("XDreamy-FHD (Egami)", "wget https://raw.githubusercontent.com/Insprion80/Skins/main/xDreamy/installer.sh -O - | /bin/sh", True, "تثبيت سكين XDreamy-FHD."),
                ("Xklass-iptv", "wget https://dreambox4u.com/emilnabil237/plugins/xklass/installer.sh -O - | /bin/sh", True, "مشغل iptv"),
                ("XmlUpdate by iet5", "wget https://raw.githubusercontent.com/Saiedf/XMLUpdateByIet5/main/installer_xmlupdatebyiet5_auto.sh -O - | /bin/sh", True, "تحديث الترددات"),
                ("XPortal", "wget -q --no-check-certificate https://raw.githubusercontent.com/azroukarim/XPortal/refs/heads/main/installer.sh -O - | /bin/sh", True, "عميل IPTV متكامل يدعم Stalker وXtream وMac Portal للوصول إلى محتوى IPTV بسهولة."),
                ("Xstreamity", "wget https://raw.githubusercontent.com/biko-73/xstreamity/main/installer.sh -O - | /bin/sh", True, "إضافة IPTV لقوائم Xtream Codes؛ تحقق من توافق الصورة قبل التثبيت."),
                ("Xtraevent_4.6", "wget https://github.com/emil237/download-plugins/raw/main/Xtraevent-v4.6.sh -O - | /bin/sh", True, "لوجو البرامج"),
                ("xtraevent_6.890_All-Python", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/xtraevent-6.890.sh -O - | /bin/sh", True, "لوجو البرامج"),
                ("xtraevent_By-M-Nasr", "wget https://github.com/popking159/xtraeventplugin/raw/main/xtraevent-install.sh -O - | /bin/sh", True, "لوجو البرامج"),
                ("Xtream New", "wget -qO- https://raw.githubusercontent.com/ahmedhussein4342-lgtm/XtreamNew/main/install_xtreamnew.sh | /bin/sh", True, "إضافة IPTV لأجهزة Enigma2؛ راجع صفحة التفاصيل للتعرّف على الوظائف ومصدر المشروع."),
                ("Xtream2Audio", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/Xtream2Audio/Xtream2Audio.sh -O - | /bin/sh", True, "إضافة مرتبطة بتجربة الصوت والمحتوى على Enigma2."),
                ("Youchie-OBH-FHD", "wget https://raw.githubusercontent.com/emilnabil/skins-obh/refs/heads/main/skin-Youchie-OBH-FHD.sh -O - | /bin/sh", True, "تثبيت سكين Youchie-OBH-FHD."),
                ("Youchie-PLI-FHD", "wget https://raw.githubusercontent.com/emilnabil/skins-openpli-9x/refs/heads/main/skin-Youchie-PLI-FHD.sh -O - | /bin/sh", True, "تثبيت سكين Youchie-PLI-FHD."),
                ("YoureWatching", "wget https://github.com/emilnabil/download-plugins/raw/refs/heads/main/YoureWatching/YoureWatching.sh -O - | /bin/sh", True, "معلومات الفيلم"),
                ("Youtube", "wget https://raw.githubusercontent.com/fairbird/Youtube-Opensource-DreamOS/master/installer.sh -O - | /bin/sh", True, "مشاهدة اليوتيوب"),
                ("Zip2Pkg-Converter", "wget https://raw.githubusercontent.com/emilnabil/download-plugins/refs/heads/main/Zip2Pkg/installer.sh -O - | /bin/sh", True, "عمل باكاج للإضافة"),
                ("Zoom_1.1.2-Py3", "wget https://dreambox4u.com/emilnabil237/plugins/zoom/installer.sh -O - | /bin/sh", True, "سيرفرات مجانية"),
                ("ZSkin FHD", "wget -q --no-check-certificate -O - https://raw.githubusercontent.com/emilnabil/download-plugins/main/skins-for-dreambox/ZSkin-FHD.sh | /bin/sh", True, "Skin بدقة FHD. سكربت المصدر يفك الأرشيف إلى نظام الملفات مباشرة؛ تأكد من توافق الصورة وخذ نسخة احتياطية من إعدادات السكين."),
            ])
        ]

        self.current_cat = 0
        self.pending_restart = False

        # Auto-update / background-task state (filled by the worker thread,
        # applied to the UI by _bgTimer on the main thread).
        self._update_remote = None
        self._update_check_done = False
        self._update_prompt_shown = False
        self._speed = {"down": None, "up": None}
        self._speed_done = False
        self._bg_ticks = 0
        self._bgTimer = None

        first_cat_name, first_items = self.categories[0]
        first_item = first_items[0]

        self["logo"] = Pixmap()
        self["clock"] = Label("")
        self["date"] = Label("")
        self["status_top"] = Label("Online4Tech Panel v8.0")
        self["sys_info"] = Label("")

        self["cat_header"] = Label(first_cat_name)
        self["cat_counter"] = Label("جميع العناصر (%d)" % len(first_items))

        self["detail_title"] = Label(first_item[0])
        self["detail_cat"] = Label(first_cat_name)
        self["item_desc"] = Label(first_item[3])
        self["cmd_preview"] = Label(first_item[1])

        self["cat_menu"] = MenuList([c[0] for c in self.categories])
        self["menu"] = MenuList([x[0] for x in first_items])

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
        self.onClose.append(self._stopBgTimer)

    def initUI(self):
        icon = getIconPath()
        if icon and self["logo"].instance:
            self["logo"].instance.setPixmapFromFile(icon)
        try:
            self["clock"].setText(time.strftime("%H:%M"))
            self["date"].setText(time.strftime("%A %d %B"))
        except Exception:
            pass
        self["sys_info"].setText(self.getSystemInfo())
        try:
            self["cat_menu"].moveToIndex(0)
            self["menu"].moveToIndex(0)
        except Exception:
            pass
        self._startBackgroundTasks()

    def getSystemInfo(self):
        py_ver = "%d.%d" % (sys.version_info[0], sys.version_info[1])
        image = "Enigma2"
        try:
            with open("/etc/issue", "r") as f:
                first = f.readline().strip()
            if first:
                image = first[:28]
        except Exception:
            pass
        ip = "Offline"
        net = "Offline"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            net = "Online"
            s.close()
        except Exception:
            pass
        hdd_line = "HDD: —"
        flash_gauge = "[■■■■□□□□□□]"
        try:
            hdd_path = "/media/hdd" if os.path.ismount("/media/hdd") else "/"
            st = os.statvfs(hdd_path)
            total_gb = st.f_blocks * st.f_frsize / 1024.0 ** 3
            free_gb = st.f_bavail * st.f_frsize / 1024.0 ** 3
            used_gb = total_gb - free_gb
            hdd_line = "HDD: %.1fGB / %.1fGB" % (used_gb, total_gb)
            if total_gb > 0:
                used_p = int(round(used_gb / total_gb * 10))
                flash_gauge = "[" + "■" * used_p + "□" * (10 - used_p) + "]"
        except Exception:
            pass
        ram_line = "RAM: —"
        ram_gauge = "[■■■■■□□□□□]"
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1])
            free = int(lines[1].split()[1])
            total_mb = total // 1024
            used_mb = (total - free) // 1024
            ram_line = "RAM: %dMB / %dMB" % (used_mb, total_mb)
            if total > 0:
                used_p = int(round((total - free) / float(total) * 10))
                ram_gauge = "[" + "■" * used_p + "□" * (10 - used_p) + "]"
        except Exception:
            pass
        down = self._speed.get("down")
        up = self._speed.get("up")
        down_txt = ("%.1f Mbps" % down) if down else "—"
        up_txt = ("%.1f Mbps" % up) if up else "—"
        return (
            "Image: %s\n"
            "Python: %s\n"
            "IP: %s\n"
            "Net: %s\n"
            "%s\n"
            "%s\n"
            "RAM  %s\n"
            "Flash %s\n"
            "التنزيل: %s\n"
            "الرفع: %s\n"
            "تنقل بالأسهم يمين/يسار أو CH+/CH-"
        ) % (image, py_ver, ip, net, hdd_line, ram_line, ram_gauge, flash_gauge, down_txt, up_txt)

    # ---------- background tasks: version check + speed probe (never block the UI) ----------
    def _startBackgroundTasks(self):
        try:
            t = threading.Thread(target=self._backgroundTasks)
            t.daemon = True
            t.start()
        except Exception:
            self._update_check_done = True
            self._speed_done = True
            return
        try:
            self._bgTimer = eTimer()
            self._bgTimer.callback.append(self._onBgTimer)
            self._bgTimer.start(500, False)
        except Exception:
            self._bgTimer = None

    def _stopBgTimer(self):
        try:
            if self._bgTimer is not None:
                self._bgTimer.stop()
        except Exception:
            pass
        self._bgTimer = None

    def _backgroundTasks(self):
        # 1) Version check (short timeout; any failure just means "no update").
        try:
            req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "Online4TechPanel/8.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                remote = resp.read().decode("utf-8", "ignore").strip()
            if remote and _isNewer(remote, VERSION):
                self._update_remote = remote
        except Exception:
            pass
        finally:
            self._update_check_done = True
        # 2) Quick speed probe (best effort; failures leave "—" in the panel).
        try:
            down = self._measureDownload()
            if down:
                self._speed["down"] = down
            up = self._measureUpload()
            if up:
                self._speed["up"] = up
        except Exception:
            pass
        finally:
            self._speed_done = True

    def _measureDownload(self):
        # Time a 1 MB download from Cloudflare.
        url = "https://speed.cloudflare.com/__down?bytes=1000000"
        try:
            start = time.time()
            req = urllib.request.Request(url, headers={"User-Agent": "Online4TechPanel/8.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                total = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
            elapsed = time.time() - start
            if elapsed > 0 and total > 0:
                return total * 8 / elapsed / 1000000.0
        except Exception:
            pass
        return None

    def _measureUpload(self):
        # Time a 200 KB POST to Cloudflare.
        url = "https://speed.cloudflare.com/__up"
        try:
            data = b"0" * 200000
            start = time.time()
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "Online4TechPanel/8.0", "Content-Type": "application/octet-stream"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                resp.read()
            elapsed = time.time() - start
            if elapsed > 0:
                return len(data) * 8 / elapsed / 1000000.0
        except Exception:
            pass
        return None

    def _onBgTimer(self):
        # Runs on the main thread: apply background results to the UI.
        self._bg_ticks += 1
        try:
            if self._speed_done or self._bg_ticks in (4, 10, 20):
                self["sys_info"].setText(self.getSystemInfo())
        except Exception:
            pass
        if self._update_check_done and self._update_remote and not self._update_prompt_shown:
            self._update_prompt_shown = True
            try:
                self["status_top"].setText("تحديث جديد: v%s" % self._update_remote)
            except Exception:
                pass
            self.session.openWithCallback(
                self._onUpdateAnswer,
                MessageBox,
                "يوجد إصدار جديد من لوحة Online4Tech (v%s)!\nالإصدار الحالي: v%s\nهل تريد التحديث الآن؟" % (self._update_remote, VERSION),
                MessageBox.TYPE_YESNO
            )
        if (self._update_check_done and self._speed_done) or self._bg_ticks >= 40:
            self._stopBgTimer()

    def _onUpdateAnswer(self, answer):
        if not answer:
            return
        plugin_path = os.path.abspath(__file__)
        cmd = "wget -q --no-check-certificate -O '%s' '%s' && echo 'Online4Tech Panel updated to v%s!'" % (plugin_path, PLUGIN_URL, self._update_remote)
        self.session.openWithCallback(self._onUpdateFinished, Console, title="Online4Tech - تحديث اللوحة", cmdlist=[cmd])

    def _onUpdateFinished(self, result=None):
        try:
            self["sys_info"].setText(self.getSystemInfo())
        except Exception:
            pass
        self.session.openWithCallback(
            self.restartCallback,
            MessageBox,
            "تم تحديث اللوحة بنجاح! هل تريد إعادة تشغيل واجهة Enigma2 الآن؟",
            MessageBox.TYPE_YESNO
        )

    # ---------- navigation / actions (unchanged behavior from v7.0) ----------
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
        self["sys_info"].setText(self.getSystemInfo())
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
            description="Online4Tech Command Dashboard v8.0",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=LoadPixmap(icon_path) if icon_path else None,
            fnc=main
        )
    ]
