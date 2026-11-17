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
    <screen name="Online4TechPanel" position="0,0" size="1920,1080" title="Online4Tech Command Center v5.1" backgroundColor="#060d1f" flags="wfNoBorder">
        <!-- Top Header Bar -->
        <eLabel position="0,0" size="1920,105" backgroundColor="#0a1633" zPosition="-1" />
        <eLabel position="0,103" size="1920,3" backgroundColor="#00d4ff" zPosition="1" />
        <widget name="logo" position="45,32" size="100,40" alphatest="blend" zPosition="2" />
        <eLabel text="ONLINE4TECH COMMAND CENTER" position="170,18" size="850,42" font="Regular;34" foregroundColor="#ffffff" backgroundColor="#0a1633" transparent="1" zPosition="2" />
        <eLabel text="Dreambox  •  Vu+  •  Novaler  •  Enigma2 Online Suite" position="170,62" size="850,30" font="Regular;22" foregroundColor="#00d4ff" backgroundColor="#0a1633" transparent="1" zPosition="2" />
        <widget name="status_top" position="1200,35" size="670,36" font="Regular;24" halign="right" foregroundColor="#38bdf8" backgroundColor="#0a1633" transparent="1" zPosition="2" />

        <!-- Left Column: System Info, Description & Command Box (x: 40..480) -->
        <eLabel position="40,130" size="440,840" backgroundColor="#0b1736" zPosition="-1" />
        <eLabel position="40,130" size="440,4" backgroundColor="#00d4ff" zPosition="1" />
        <eLabel text="بيانات النظام الحية" position="60,148" size="400,38" font="Regular;27" halign="center" foregroundColor="#00d4ff" backgroundColor="#0b1736" transparent="1" zPosition="2" />
        <eLabel position="60,195" size="400,2" backgroundColor="#1e3a8a" zPosition="1" />
        <widget name="sys_info" position="60,210" size="400,290" font="Regular;22" foregroundColor="#e2e8f0" backgroundColor="#0b1736" transparent="1" zPosition="2" />

        <eLabel position="60,510" size="400,2" backgroundColor="#1e3a8a" zPosition="1" />
        <eLabel text="تفاصيل العنصر المختار" position="60,525" size="400,36" font="Regular;26" halign="center" foregroundColor="#38bdf8" backgroundColor="#0b1736" transparent="1" zPosition="2" />
        <widget name="item_desc" position="60,575" size="400,230" font="Regular;23" halign="center" foregroundColor="#cbd5e1" backgroundColor="#0b1736" transparent="1" zPosition="2" />

        <!-- Command Preview Box -->
        <eLabel text="ملف التنفيذ السحابي (GitHub)" position="60,820" size="400,30" font="Regular;20" halign="center" foregroundColor="#94a3b8" backgroundColor="#0b1736" transparent="1" zPosition="2" />
        <eLabel position="60,858" size="400,85" backgroundColor="#050b1a" zPosition="0" />
        <widget name="cmd_preview" position="70,872" size="380,60" font="Regular;21" halign="center" foregroundColor="#00d4ff" backgroundColor="#050b1a" transparent="1" zPosition="2" />

        <!-- Center Column: Tools & Scripts List (x: 510..1430) -->
        <eLabel position="510,130" size="920,840" backgroundColor="#0b1736" zPosition="-1" />
        <eLabel position="510,130" size="920,4" backgroundColor="#3b82f6" zPosition="1" />
        <widget name="cat_counter" position="540,150" size="250,42" font="Regular;24" halign="left" foregroundColor="#38bdf8" backgroundColor="#0b1736" transparent="1" zPosition="2" />
        <widget name="cat_header" position="800,150" size="600,42" font="Regular;30" halign="right" foregroundColor="#ffffff" backgroundColor="#0b1736" transparent="1" zPosition="2" />
        <eLabel position="540,200" size="860,2" backgroundColor="#1e3a8a" zPosition="1" />
        <widget name="menu" position="540,220" size="860,720" scrollbarMode="showOnDemand" font="Regular;27" itemHeight="60" foregroundColor="#f8fafc" backgroundColor="#0b1736" backgroundColorSelected="#0284c7" foregroundColorSelected="#ffffff" transparent="1" zPosition="2" />

        <!-- Right Column: Categories Sidebar (x: 1460..1880) -->
        <eLabel position="1460,130" size="420,840" backgroundColor="#0b1736" zPosition="-1" />
        <eLabel position="1460,130" size="420,4" backgroundColor="#00d4ff" zPosition="1" />
        <eLabel text="الأقسام الرئيسية" position="1480,150" size="380,42" font="Regular;30" halign="center" foregroundColor="#00d4ff" backgroundColor="#0b1736" transparent="1" zPosition="2" />
        <eLabel position="1480,200" size="380,2" backgroundColor="#1e3a8a" zPosition="1" />
        <widget name="cat_menu" position="1480,220" size="380,560" scrollbarMode="showNever" font="Regular;26" itemHeight="62" foregroundColor="#cbd5e1" backgroundColor="#0b1736" backgroundColorSelected="#1d4ed8" foregroundColorSelected="#ffffff" transparent="1" zPosition="2" />
        <eLabel text="أسهم يمين / يسار أو CH+/CH-\nللتنقل السريع بين الأقسام" position="1480,835" size="380,90" font="Regular;21" halign="center" foregroundColor="#64748b" backgroundColor="#0b1736" transparent="1" zPosition="2" />

        <!-- Bottom Action Bar -->
        <eLabel position="0,995" size="1920,85" backgroundColor="#0a1633" zPosition="-1" />
        <eLabel position="0,995" size="1920,2" backgroundColor="#1e3a8a" zPosition="1" />
        <ePixmap pixmap="buttons/red.png" position="80,1022" size="35,35" alphatest="on" zPosition="2" />
        <widget name="key_red" position="130,1020" size="220,40" font="Regular;26" foregroundColor="#ffffff" backgroundColor="#0a1633" transparent="1" zPosition="2" />
        <ePixmap pixmap="buttons/green.png" position="480,1022" size="35,35" alphatest="on" zPosition="2" />
        <widget name="key_green" position="530,1020" size="300,40" font="Regular;26" foregroundColor="#ffffff" backgroundColor="#0a1633" transparent="1" zPosition="2" />
        <ePixmap pixmap="buttons/yellow.png" position="950,1022" size="35,35" alphatest="on" zPosition="2" />
        <widget name="key_yellow" position="1000,1020" size="320,40" font="Regular;26" foregroundColor="#ffffff" backgroundColor="#0a1633" transparent="1" zPosition="2" />
        <ePixmap pixmap="buttons/blue.png" position="1440,1022" size="35,35" alphatest="on" zPosition="2" />
        <widget name="key_blue" position="1490,1020" size="350,40" font="Regular;26" foregroundColor="#ffffff" backgroundColor="#0a1633" transparent="1" zPosition="2" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.github_base_url = "https://raw.githubusercontent.com/online4tech/Chanal-List/main/scripts/"

        self.categories = [
            ("القنوات والبيكونات", [
                ("تحديث ملف القنوات الشامل (Online4Tech)", "update_channels.sh", True, "تحميل وتثبيت أحدث ملف قنوات مرتب للنايل سات وكافة الأقمار من سيرفر Online4Tech."),
                ("تثبيت حزمة البيكونات الشفافة (Picons)", "install_picons.sh", False, "تحميل وتثبيت شعارات القنوات الحديثة عالية الجودة في المسار القياسي."),
                ("تثبيت بلجن Chocholousek Picons", "install_chocholousek.sh", True, "تثبيت البلجن الشهير لتحميل وتحديث بيكونات جميع الأقمار تلقائياً."),
                ("تحديث الدليل الإلكتروني (EPG Import)", "update_epg.sh", False, "تثبيت وتحديث مصادر الدليل الإلكتروني للبرامج والقنوات العربية والعالمية.")
            ]),
            ("الإيموهات والسوفتكام", [
                ("تثبيت محاكي OSCam-icam (أحدث إصدار)", "install_oscam.sh", True, "تثبيت أحدث إصدار من محاكي OSCam الداعم لباقات Sky والشفرات الحديثة."),
                ("تثبيت محاكي NCam الرسمي", "install_ncam.sh", True, "تثبيت محاكي NCam السريع والمستقر لتشغيل سطر الشيرنج والـ CCcam/MGcamd."),
                ("تحديث مفاتيح SoftCam.Key أونلاين", "softcam_update.sh", False, "جلب أحدث ملف شفرات BISS و PowerVU وتفعيله داخل مسار الإيمو."),
                ("إعادة تشغيل الإيمو النشط (Restart Softcam)", "restart_emu.sh", False, "إعادة تشغيل فورية لمحاكي OSCam أو NCam لتنشيط السيرفر.")
            ]),
            ("البلجنات الأساسية", [
                ("تثبيت لوحة التحكم AJPanel", "install_ajpanel.sh", True, "تثبيت العملاق AJPanel لإدارة القنوات، السيرفرات، الـ IPTV، والنسخ الاحتياطي."),
                ("تثبيت مشغل الترجمة SubsSupport", "install_subssupport.sh", True, "تثبيت بلجن الترجمة العربية الاحترافي للأفلام والقنوات الأجنبية."),
                ("تثبيت بلجن جدول المباريات FootOnSat", "install_footonsat.sh", True, "عرض مواعيد المباريات اليومية والقنوات الناقلة والترددات مباشرة على الشاشة."),
                ("تثبيت بلجن KeyAdder لإدخال الشفرات", "install_keyadder.sh", True, "إضافة وتعديل شفرات BISS بسهولة عبر الريموت دون الحاجة للكمبيوتر."),
                ("تثبيت لوحة المفاتيح NewVirtualKeyBoard", "install_virtualkb.sh", True, "كيبورد افتراضي حديث يدعم الكتابة بالعربية والإنجليزية والبحث السريع.")
            ]),
            ("بلجنات IPTV والميديا", [
                ("تثبيت مشغل E2iPlayer + TSIPlayer", "install_e2iplayer.sh", True, "أقوى مشغل للمنصات والأفلام والمسلسلات العربية والعالمية أونلاين."),
                ("تثبيت مشغل MultiStalker Pro", "install_multistalker.sh", True, "تشغيل بورتالات الماك أدريس (Stalker MAC Portals) بواجهة عصرية."),
                ("تثبيت مشغل XStreamity IPTV", "install_xstreamity.sh", True, "مشغل اشتراكات Xtream Codes IPTV الرسمي مع دعم VOD و Catchup."),
                ("تثبيت بلجن JediMakerXtream", "install_jedimaker.sh", True, "تحويل اشتراكات الـ IPTV إلى باقات قنوات مدمجة داخل قائمة قنوات الريسفر."),
                ("تثبيت بلجن IPAudio Pro (التعليق العربي)", "install_ipaudio.sh", True, "تركيب الصوتيات والتعليق العربي على القنوات الرياضية الأجنبية بدقة عالية.")
            ]),
            ("السكينات والمظهر", [
                ("تثبيت سكين Aglare FHD العصري", "skin_aglare.sh", True, "تثبيت سكين Aglare Full HD الاحترافي المتوافق مع أغلب صور Enigma2."),
                ("تثبيت سكين Nitro Advance FHD", "skin_nitro.sh", True, "تثبيت سكين نيترو السريع والخفيف بواجهة رياضية أنيقة."),
                ("تثبيت سكين BlackSpirit / Pro FHD", "skin_blackspirit.sh", True, "تثبيت سكين داكن فخم يدعم إظهار البوسترات وحالة التشفير والطقس."),
                ("تثبيت سكين MetrixHD القياسي", "skin_metrix.sh", True, "تثبيت سكين MetrixHD من فيد الصورة الرسمي."),
                ("تثبيت الخطوط العربية الاحترافية", "install_fonts.sh", True, "تحديث خطوط النظام لتحسين قراءة القوائم والـ EPG والترجمة."),
                ("تثبيت بوت لوجو Online4Tech الرسمي", "bootlogo_online4tech.sh", True, "تطبيق شعار Online4Tech كشاشة إقلاع للريسفر وتحديث البيكون الافتراضي.")
            ]),
            ("أدوات النظام والصيانة", [
                ("تثبيت حزمة ServiceApp + Exteplayer3", "install_serviceapp.sh", True, "تثبيت مشغلات الميديا الضرورية لتسريع قنوات الـ IPTV ومنع التقطيع."),
                ("تحديث فيدات الصورة (opkg update)", "opkg_update.sh", False, "تحديث مستودعات الصورة الرسمية لإصلاح مشاكل تثبيت الحزم."),
                ("تنظيف الرام والملفات المؤقتة (Deep Clean)", "clean_system.sh", False, "مسح الكاش وملفات /tmp وتفريغ الرام لتسريع استجابة الريسفر."),
                ("فحص المساحة وحالة الاتصال بالشبكة", "check_net_disk.sh", False, "عرض تقرير مفصل عن مساحة الفلاشة، الهارد، واستقرار الإنترنت."),
                ("استعادة اختصارات الريموت القياسية", "restore_hotkeys.sh", True, "إعادة ضبط أزرار الريموت السريعة للوضع المثالي.")
            ])
        ]

        self.current_cat = 0
        self.pending_restart = False

        self["logo"] = Pixmap()
        self["status_top"] = Label("Online4Tech Cloud  •  25 Tools Ready  •  v5.1")
        self["sys_info"] = Label(self.getSystemInfo())
        self["item_desc"] = Label(self.categories[0][1][0][3])
        self["cmd_preview"] = Label("scripts/" + self.categories[0][1][0][1])
        self["cat_header"] = Label("قسم: " + self.categories[0][0])
        self["cat_counter"] = Label("%d عناصر  |  1/%d" % (len(self.categories[0][1]), len(self.categories)))

        self["cat_menu"] = MenuList([c[0] for c in self.categories])
        self["menu"] = MenuList([x[0] for x in self.categories[0][1]])

        self["key_red"] = Label("خروج")
        self["key_green"] = Label("تثبيت / تشغيل")
        self["key_yellow"] = Label("إعادة تشغيل الواجهة")
        self["key_blue"] = Label("إعادة تشغيل الجهاز")

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions"], {
            "ok": self.runSelectedTool,
            "green": self.runSelectedTool,
            "yellow": self.confirmRestartGUI,
            "blue": self.confirmRebootBox,
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

    def getSystemInfo(self):
        py_ver = "%d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "Offline"

        img_name = "Enigma2"
        if os.path.exists("/etc/issue"):
            try:
                with open("/etc/issue", "r") as f:
                    img_name = f.readline().strip().replace("\n", "").replace("\l", "")[:22]
            except Exception:
                pass

        ram_info = "N/A"
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                total = int(lines[0].split()[1]) // 1024
                free = int(lines[1].split()[1]) // 1024
                ram_info = "%dMB Free / %dMB" % (free, total)
        except Exception:
            pass

        flash_info = "N/A"
        try:
            st = os.statvfs("/")
            free_f = (st.f_bavail * st.f_frsize) // (1024 * 1024)
            total_f = (st.f_blocks * st.f_frsize) // (1024 * 1024)
            flash_info = "%dMB Free / %dMB" % (free_f, total_f)
        except Exception:
            pass

        return (
            "Image: %s\n"
            "Python: %s\n"
            "IP: %s\n"
            "RAM: %s\n"
            "Flash: %s\n"
            "Server: Online4Tech GitHub"
        ) % (img_name, py_ver, ip, ram_info, flash_info)

    def loadCategory(self, cat_idx):
        self.current_cat = cat_idx
        self["cat_menu"].moveToIndex(cat_idx)
        cat_name, items = self.categories[cat_idx]
        self["cat_header"].setText("قسم: " + cat_name)
        self["cat_counter"].setText("%d عناصر  |  %d/%d" % (len(items), cat_idx + 1, len(self.categories)))
        self["menu"].setList([x[0] for x in items])
        self["menu"].moveToIndex(0)
        self.updateDescription()

    def updateDescription(self):
        items = self.categories[self.current_cat][1]
        idx = self["menu"].getSelectedIndex()
        if 0 <= idx < len(items):
            self["item_desc"].setText(items[idx][3])
            self["cmd_preview"].setText("scripts/" + items[idx][1])

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
        items = self.categories[self.current_cat][1]
        idx = self["menu"].getSelectedIndex()
        if 0 <= idx < len(items):
            name, filename, restart_flag, _ = items[idx]
            self.pending_restart = restart_flag
            raw_url = self.github_base_url + filename
            tmp_script = "/tmp/online4tech_run.sh"

            cmd = (
                "echo '==========================================' && "
                "echo '  Online4Tech Cloud Server Connecting...  ' && "
                "echo '==========================================' && "
                "rm -f {tmp} && "
                "wget -q --no-check-certificate -O {tmp} '{url}' && "
                "if [ -s {tmp} ]; then "
                "sed -i 's/\r$//' {tmp} && "
                "chmod 755 {tmp} && "
                "sh {tmp}; "
                "rm -f {tmp}; "
                "else echo 'Error: Script not found on GitHub: {url}'; fi"
            ).format(tmp=tmp_script, url=raw_url)

            self.session.openWithCallback(self.onToolFinished, Console, title="Online4Tech - " + name, cmdlist=[cmd])

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

    def confirmRebootBox(self):
        self.session.openWithCallback(self.rebootBoxCallback, MessageBox, "إعادة تشغيل الريسفر بالكامل الآن؟", MessageBox.TYPE_YESNO)

    def restartCallback(self, answer):
        if answer:
            os.system("killall -9 enigma2")

    def rebootBoxCallback(self, answer):
        if answer:
            os.system("reboot")


def main(session, **kwargs):
    session.open(Online4TechPanel)


def Plugins(**kwargs):
    icon_path = getIconPath()
    return [
        PluginDescriptor(
            name="Online4Tech Panel",
            description="Online4Tech Command Center v5.1 (Plugins, Skins, Softcams)",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=LoadPixmap(icon_path) if icon_path else None,
            fnc=main
        )
    ]
