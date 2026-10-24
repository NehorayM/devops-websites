# -*- coding: utf-8 -*-
from _h import *

CHAPTER = {
 "nm": "Linux", "em": "🐧", "dom": 3, "secs": [21],
 "sub": "דף עזר: ביצועים, תהליכים ו-systemd, דיסק, הרשאות, cron ורשת מהשרת.",
 "topics": [
  {"nm": "Performance", "blocks": [
    CODE("""
uptime                 # load average vs number of cores
top / htop             # us, sy, wa (iowait), st (steal)
vmstat 1               # run queue, si/so (swap), wa
iostat -xz 1           # %util, await per disk
free -m                # look at 'available', not 'free'
dmesg -T | tail        # OOM kills, disk errors
""", cap="60 השניות הראשונות על שרת איטי."),
    TABLE(["תסמין", "חשוד"],
          ["load גבוה, CPU נמוך", "IO: דיסק איטי או עמוס"],
          ["wa גבוה", "דיסק; iotop או pidstat -d"],
          ["si/so גבוהים", "swap thrashing"],
          ["st גבוה", "ה-hypervisor לוקח CPU"],
          ["free נמוך, available גבוה", "page cache. תקין"]),
    KEY("load average סופר גם תהליכים שמחכים לדיסק (מצב D). לכן load גבוה הוא לא בהכרח CPU."),
    ASK("A server is slow. Walk me through your first minute.",
        "What does load average mean?",
        "What do free, buff/cache and available mean?",
        "When does the OOM killer act?"),
  ]},
  {"nm": "Processes & systemd", "blocks": [
    TABLE(["Exit / signal", "משמעות"],
          ["0", "הצלחה"],
          ["137 (128+9)", "SIGKILL; בקונטיינר לרוב OOM"],
          ["143 (128+15)", "SIGTERM; כיבוי רגיל"],
          ["מצב D", "מחכה ל-IO; kill -9 לא עוזר"],
          ["מצב Z", "zombie; ההורה צריך לאסוף"]),
    CODE("""
systemctl status nginx
journalctl -u nginx -b -e
systemctl daemon-reload        # after editing a unit
cat /proc/<pid>/limits         # the limits that really apply
strace -c -p <pid>             # what syscalls is it making?
""", cap="service שלא עולה, ומה תהליך עושה."),
    TRAP("Too many open files: להעלות LimitNOFILE ב-systemd, אבל קודם לבדוק אם זו דליפה (ls /proc/<pid>/fd | wc -l לאורך זמן)."),
    KEY("SIGTERM לפני SIGKILL: נותנים לתהליך לסיים. בקונטיינר, האפליקציה צריכה להיות PID 1 (exec form) כדי לקבל אותו."),
    ASK("A systemd service won't start. How do you debug it?",
        "SIGTERM vs SIGKILL?",
        "An app reports Too many open files. What do you do?",
        "A process ignores kill -9. Why?"),
  ]},
  {"nm": "Disk, permissions, cron & network", "blocks": [
    TABLE(["בעיה", "פקודה"],
          ["איזה FS מלא", "`df -h`, `df -i` ל-inodes"],
          ["איזו תיקייה", "`du -xh --max-depth=1 / | sort -h`"],
          ["df > du", "`lsof +L1`: קבצים שנמחקו ופתוחים"],
          ["מי מאזין על פורט", "`ss -tulpn`"],
          ["פורט פתוח?", "`nc -zv host 443`"],
          ["DNS", "`dig`, `resolvectl status`, `getent hosts`"]),
    TABLE(["הרשאה", "פירוש"],
          ["755 / 644", "תיקיות ו-scripts / קבצים"],
          ["x על תיקייה", "אפשר להיכנס"],
          ["setuid", "רץ עם הרשאות הבעלים. מסוכן"],
          ["sticky (/tmp)", "רק הבעלים מוחק"]),
    KEY("cron רץ עם סביבה מינימלית: PATH אחר, בלי profile. נתיבים מלאים, ופלט ללוג."),
    TRAP("chmod 777 פותח לכולם. מתקנים בעלות או קבוצה."),
    ASK("The disk is full, but du doesn't add up. Why?",
        "A cron job works by hand but not from cron. Why?",
        "Hard link vs symbolic link?",
        "A host can ping IPs but not resolve names. Troubleshoot."),
  ]},
  {"nm": "Linux incident drills", "blocks": [
    P("שלושה תרגילים שחוזרים בראיונות, עם סדר הפקודות שמראה ניסיון."),
    TABLE(["תרחיש", "פקודות לפי הסדר", "מה מחפשים"],
          ["השרת איטי", "`uptime` → `top` → `vmstat 1` → `iostat -xz 1`", "load מול מספר ה-CPUs, wa גבוה, si/so (swap)"],
          ["הדיסק מלא", "`df -h` → `df -i` → `du -xh --max-depth=1` → `lsof +L1`", "קבצים גדולים, inodes, קבצים שנמחקו ופתוחים"],
          ["תהליך נעלם", "`systemctl status` → `journalctl -u svc` → `dmesg -T`", "exit code, OOM killer, segfault"],
          ["פורט לא עונה", "`ss -tlnp` → `curl localhost:PORT` → firewall", "מאזין על 127.0.0.1 בלבד, או לא מאזין"]),
    TABLE(["exit code", "פירוש"],
          ["0", "הצלחה"],
          ["1", "שגיאה כללית של האפליקציה"],
          ["126 / 127", "אין הרשאת הרצה / פקודה לא נמצאה"],
          ["128+N", "נהרג על ידי signal N: 137 = SIGKILL (לרוב OOM), 143 = SIGTERM"]),
    KEY("שירות שמאזין על `127.0.0.1:8080` לא נגיש מבחוץ, גם כשה-firewall פתוח. `ss -tlnp` מראה את הכתובת שעליה הוא מאזין."),
    TRAP("load average של 8 על מכונה עם 16 cores הוא תקין; על מכונה עם 2 cores הוא עומס כבד. תמיד משווים למספר ה-CPUs (`nproc`)."),
    ASK("A server is slow. What do you run first and why?",
        "What does exit code 137 mean?",
        "A service runs but can't be reached from another host. What do you check?"),
  ]},
 ],
 "quiz": [
   QZ("Load is 20 on 4 cores but CPU use is 30%. What does that suggest?",
      "Processes waiting on I/O", "The CPU is overloaded", "Too much free memory", "An idle network",
      x="load כולל תהליכים במצב D שמחכים לדיסק. load גבוה עם CPU נמוך מצביע על IO."),
   QZ("You edited a unit file but the old command still runs. What did you forget?",
      "`systemctl daemon-reload`", "`journalctl --vacuum-time`", "`kill -9 1`", "`ulimit -n`",
      x="systemd מחזיק את ה-units בזיכרון. daemon-reload טוען את השינוי."),
   QZ("`df` shows the disk full but `du` doesn't. Which command finds the cause?",
      "`lsof +L1`", "`chmod 755`", "`uptime`", "`ss -tulpn`",
      x="lsof +L1 מראה קבצים שנמחקו ועדיין פתוחים. המקום יתפנה כשהתהליך יסגור אותם או יופעל מחדש."),
  QZ("A container exits with code 143. What happened?",
      "It was terminated by SIGTERM (128 + 15)", "It ran out of memory", "The command was not found", "It completed successfully",
      x="קודי 128+N מציינים signal. 143 הוא SIGTERM, כלומר כיבוי מסודר; 137 הוא SIGKILL."),
 ],
}
