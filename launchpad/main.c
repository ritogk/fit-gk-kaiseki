#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <sched.h>
#include <poll.h>
#include <sys/mman.h>
#include <linux/uinput.h>
#include <linux/input-event-codes.h>
#include <alsa/asoundlib.h>

#define MAX_NOTES 128
#define MAX_CC    128

#define COLOR_OFF    0
#define COLOR_RED    5
#define COLOR_ORANGE 9
#define COLOR_YELLOW 13
#define COLOR_GREEN  21
#define COLOR_CYAN   37
#define COLOR_BLUE   45
#define COLOR_PURPLE 53
#define COLOR_BRIGHT 72
#define COLOR_DIM    117
#define COLOR_ACTIVE 21

static snd_rawmidi_t *midi_in;
static snd_rawmidi_t *midi_out;
static int uinput_fd = -1;
static volatile sig_atomic_t running = 1;

static int note_to_key[MAX_NOTES];
static int note_led_idle[MAX_NOTES];
static int note_led_pressed[MAX_NOTES];

static int cc_to_key[MAX_CC];
static int cc_led_idle[MAX_CC];
static int cc_led_pressed[MAX_CC];

static void on_signal(int sig) { (void)sig; running = 0; }

/* ── key name table ── */

struct key_entry { const char *name; int code; };

static const struct key_entry key_table[] = {
    {"KEY_ESC",KEY_ESC},{"KEY_1",KEY_1},{"KEY_2",KEY_2},{"KEY_3",KEY_3},
    {"KEY_4",KEY_4},{"KEY_5",KEY_5},{"KEY_6",KEY_6},{"KEY_7",KEY_7},
    {"KEY_8",KEY_8},{"KEY_9",KEY_9},{"KEY_0",KEY_0},{"KEY_MINUS",KEY_MINUS},
    {"KEY_EQUAL",KEY_EQUAL},{"KEY_BACKSPACE",KEY_BACKSPACE},{"KEY_TAB",KEY_TAB},
    {"KEY_Q",KEY_Q},{"KEY_W",KEY_W},{"KEY_E",KEY_E},{"KEY_R",KEY_R},
    {"KEY_T",KEY_T},{"KEY_Y",KEY_Y},{"KEY_U",KEY_U},{"KEY_I",KEY_I},
    {"KEY_O",KEY_O},{"KEY_P",KEY_P},{"KEY_LEFTBRACE",KEY_LEFTBRACE},
    {"KEY_RIGHTBRACE",KEY_RIGHTBRACE},{"KEY_ENTER",KEY_ENTER},
    {"KEY_LEFTCTRL",KEY_LEFTCTRL},{"KEY_A",KEY_A},{"KEY_S",KEY_S},
    {"KEY_D",KEY_D},{"KEY_F",KEY_F},{"KEY_G",KEY_G},{"KEY_H",KEY_H},
    {"KEY_J",KEY_J},{"KEY_K",KEY_K},{"KEY_L",KEY_L},
    {"KEY_SEMICOLON",KEY_SEMICOLON},{"KEY_APOSTROPHE",KEY_APOSTROPHE},
    {"KEY_GRAVE",KEY_GRAVE},{"KEY_LEFTSHIFT",KEY_LEFTSHIFT},
    {"KEY_BACKSLASH",KEY_BACKSLASH},{"KEY_Z",KEY_Z},{"KEY_X",KEY_X},
    {"KEY_C",KEY_C},{"KEY_V",KEY_V},{"KEY_B",KEY_B},{"KEY_N",KEY_N},
    {"KEY_M",KEY_M},{"KEY_COMMA",KEY_COMMA},{"KEY_DOT",KEY_DOT},
    {"KEY_SLASH",KEY_SLASH},{"KEY_RIGHTSHIFT",KEY_RIGHTSHIFT},
    {"KEY_LEFTALT",KEY_LEFTALT},{"KEY_SPACE",KEY_SPACE},
    {"KEY_CAPSLOCK",KEY_CAPSLOCK},{"KEY_RIGHTCTRL",KEY_RIGHTCTRL},
    {"KEY_RIGHTALT",KEY_RIGHTALT},
    {"KEY_F1",KEY_F1},{"KEY_F2",KEY_F2},{"KEY_F3",KEY_F3},{"KEY_F4",KEY_F4},
    {"KEY_F5",KEY_F5},{"KEY_F6",KEY_F6},{"KEY_F7",KEY_F7},{"KEY_F8",KEY_F8},
    {"KEY_F9",KEY_F9},{"KEY_F10",KEY_F10},{"KEY_F11",KEY_F11},{"KEY_F12",KEY_F12},
    {"KEY_UP",KEY_UP},{"KEY_DOWN",KEY_DOWN},{"KEY_LEFT",KEY_LEFT},{"KEY_RIGHT",KEY_RIGHT},
    {"KEY_PAGEUP",KEY_PAGEUP},{"KEY_PAGEDOWN",KEY_PAGEDOWN},
    {"KEY_HOME",KEY_HOME},{"KEY_END",KEY_END},
    {"KEY_INSERT",KEY_INSERT},{"KEY_DELETE",KEY_DELETE},
    {NULL, 0}
};

static int lookup_keycode(const char *name) {
    for (const struct key_entry *e = key_table; e->name; e++)
        if (strcasecmp(e->name, name) == 0) return e->code;
    return -1;
}

/* ── auto-detect Launchpad ── */

static int find_launchpad(char *dev_in, char *dev_out, size_t len) {
    int card = -1;
    while (snd_card_next(&card) >= 0 && card >= 0) {
        char *name = NULL;
        if (snd_card_get_name(card, &name) < 0) continue;
        int found = (strstr(name, "Launchpad") != NULL);
        free(name);
        if (found) {
            snprintf(dev_in, len, "hw:%d,0,1", card);
            snprintf(dev_out, len, "hw:%d,0,1", card);
            return 0;
        }
    }
    return -1;
}

/* ── uinput ── */

static int setup_uinput(void) {
    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd < 0) { perror("open /dev/uinput"); return -1; }

    ioctl(fd, UI_SET_EVBIT, EV_KEY);
    ioctl(fd, UI_SET_EVBIT, EV_SYN);
    for (const struct key_entry *e = key_table; e->name; e++)
        ioctl(fd, UI_SET_KEYBIT, e->code);

    struct uinput_setup us = {
        .id = { .bustype = BUS_USB, .vendor = 0x1235, .product = 0x0001, .version = 1 },
    };
    strncpy(us.name, "LaunchpadX-KB", sizeof(us.name) - 1);

    if (ioctl(fd, UI_DEV_SETUP, &us) < 0 || ioctl(fd, UI_DEV_CREATE) < 0) {
        perror("uinput setup");
        close(fd);
        return -1;
    }
    usleep(100000);
    return fd;
}

static void emit_key(int keycode, int value) {
    struct input_event ev[2];
    memset(ev, 0, sizeof(ev));
    ev[0].type  = EV_KEY;
    ev[0].code  = keycode;
    ev[0].value = value;
    ev[1].type  = EV_SYN;
    ev[1].code  = SYN_REPORT;
    if (write(uinput_fd, ev, sizeof(ev)) < 0)
        perror("uinput write");
}

/* ── LED ── */

static void set_note_led(int note, int color) {
    if (!midi_out) return;
    unsigned char msg[3] = {0x90, note, color};
    snd_rawmidi_write(midi_out, msg, 3);
}

static void set_cc_led(int cc, int color) {
    if (!midi_out) return;
    unsigned char msg[3] = {0xB0, cc, color};
    snd_rawmidi_write(midi_out, msg, 3);
}

/* ── MIDI parser ── */

enum { ST_WAIT, ST_DATA1, ST_DATA2 };

struct midi_parser {
    int state;
    unsigned char status, data1;
};

static int midi_parse(struct midi_parser *p, unsigned char byte,
                      unsigned char *status, unsigned char *d1, unsigned char *d2) {
    if (byte & 0x80) {
        if (byte >= 0xF0) { p->state = ST_WAIT; return 0; } // skip sysex/realtime
        p->status = byte;
        p->state  = ST_DATA1;
        return 0;
    }
    switch (p->state) {
    case ST_WAIT: return 0;
    case ST_DATA1:
        p->data1  = byte;
        p->state  = ST_DATA2;
        return 0;
    case ST_DATA2:
        *status = p->status;
        *d1     = p->data1;
        *d2     = byte;
        p->state = ST_DATA1; // running status
        return 1;
    }
    return 0;
}

/* ── key category → LED color ── */

static int idle_color_for(int keycode) {
    if ((keycode >= KEY_Q && keycode <= KEY_P) ||
        (keycode >= KEY_A && keycode <= KEY_L) ||
        (keycode >= KEY_Z && keycode <= KEY_M))
        return COLOR_BLUE;
    if ((keycode >= KEY_1 && keycode <= KEY_0))
        return COLOR_GREEN;
    if (keycode == KEY_LEFTSHIFT || keycode == KEY_RIGHTSHIFT ||
        keycode == KEY_LEFTCTRL  || keycode == KEY_RIGHTCTRL  ||
        keycode == KEY_LEFTALT   || keycode == KEY_RIGHTALT   ||
        keycode == KEY_CAPSLOCK)
        return COLOR_RED;
    if (keycode == KEY_UP    || keycode == KEY_DOWN  ||
        keycode == KEY_LEFT  || keycode == KEY_RIGHT ||
        keycode == KEY_PAGEUP|| keycode == KEY_PAGEDOWN ||
        keycode == KEY_HOME  || keycode == KEY_END)
        return COLOR_ORANGE;
    if (keycode >= KEY_F1 && keycode <= KEY_F12)
        return COLOR_PURPLE;
    return COLOR_YELLOW;
}

/* ── default keymap ── */

static void set_note_map(int note, int keycode) {
    note_to_key[note]     = keycode;
    note_led_idle[note]   = idle_color_for(keycode);
    note_led_pressed[note]= COLOR_BRIGHT;
}

static void set_cc_map(int cc, int keycode) {
    cc_to_key[cc]     = keycode;
    cc_led_idle[cc]   = idle_color_for(keycode);
    cc_led_pressed[cc]= COLOR_BRIGHT;
}

static void load_default_keymap(void) {
    /* 8x8 grid — note = row*10 + col  (row 1=bottom, col 1=left) */

    /* row 8 (top): 1 2 3 4 5 6 7 8 */
    int r8[] = {KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8};
    /* row 7: q w e r t y u i */
    int r7[] = {KEY_Q, KEY_W, KEY_E, KEY_R, KEY_T, KEY_Y, KEY_U, KEY_I};
    /* row 6: a s d f g h j k */
    int r6[] = {KEY_A, KEY_S, KEY_D, KEY_F, KEY_G, KEY_H, KEY_J, KEY_K};
    /* row 5: z x c v b n m , */
    int r5[] = {KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B, KEY_N, KEY_M, KEY_COMMA};
    /* row 4: 9 0 o p l ; . / */
    int r4[] = {KEY_9, KEY_0, KEY_O, KEY_P, KEY_L, KEY_SEMICOLON, KEY_DOT, KEY_SLASH};
    /* row 3: - = [ ] ' \ ` backspace */
    int r3[] = {KEY_MINUS, KEY_EQUAL, KEY_LEFTBRACE, KEY_RIGHTBRACE,
                KEY_APOSTROPHE, KEY_BACKSLASH, KEY_GRAVE, KEY_BACKSPACE};
    /* row 2: esc tab shift ctrl alt space enter del */
    int r2[] = {KEY_ESC, KEY_TAB, KEY_LEFTSHIFT, KEY_LEFTCTRL,
                KEY_LEFTALT, KEY_SPACE, KEY_ENTER, KEY_DELETE};
    /* row 1 (bottom): up down left right pgup pgdn home end */
    int r1[] = {KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
                KEY_PAGEUP, KEY_PAGEDOWN, KEY_HOME, KEY_END};

    int *rows[] = {r1, r2, r3, r4, r5, r6, r7, r8};
    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            set_note_map((r+1)*10 + (c+1), rows[r][c]);

    /* top row buttons (CC 91-98): F1-F8 */
    for (int i = 0; i < 8; i++)
        set_cc_map(91 + i, KEY_F1 + i);

    /* right column (CC 89,79,...,19): F9 F10 F11 F12 caps rshift rctrl ralt */
    int right[] = {KEY_F9, KEY_F10, KEY_F11, KEY_F12,
                   KEY_CAPSLOCK, KEY_RIGHTSHIFT, KEY_RIGHTCTRL, KEY_RIGHTALT};
    for (int i = 0; i < 8; i++)
        set_cc_map(89 - i*10, right[i]);
}

/* ── config file (overrides defaults) ── */

static int load_keymap_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;

    char line[256];
    while (fgets(line, sizeof(line), f)) {
        char *p = line;
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '#' || *p == '\n' || *p == '\0') continue;

        char type;
        int num;
        char keyname[64];
        int idle = -1, pressed = -1;

        int n = sscanf(p, " %c %d %63s %d %d", &type, &num, keyname, &idle, &pressed);
        if (n < 3 || num < 0 || num >= 128) continue;

        int kc = lookup_keycode(keyname);
        if (kc < 0) { fprintf(stderr, "unknown key: %s\n", keyname); continue; }

        if (type == 'N' || type == 'n') {
            note_to_key[num]      = kc;
            note_led_idle[num]    = COLOR_ACTIVE;
            note_led_pressed[num] = (n >= 5 && pressed >= 0) ? pressed : COLOR_BRIGHT;
        } else if (type == 'C' || type == 'c') {
            cc_to_key[num]      = kc;
            cc_led_idle[num]    = COLOR_ACTIVE;
            cc_led_pressed[num] = (n >= 5 && pressed >= 0) ? pressed : COLOR_BRIGHT;
        }
    }
    fclose(f);
    return 0;
}

/* ── Launchpad X: enter Programmer mode ── */

static void enter_programmer_mode(void) {
    if (!midi_out) return;
    unsigned char sysex[] = {0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x0E, 0x01, 0xF7};
    snd_rawmidi_write(midi_out, sysex, sizeof(sysex));
}

/* ── realtime priority ── */

static void set_realtime(void) {
    struct sched_param sp = { .sched_priority = 50 };
    if (sched_setscheduler(0, SCHED_FIFO, &sp) < 0)
        fprintf(stderr, "warning: SCHED_FIFO unavailable (run as root for realtime)\n");
    if (mlockall(MCL_CURRENT | MCL_FUTURE) < 0)
        fprintf(stderr, "warning: mlockall failed\n");
}

/* ── LED init / clear ── */

static void paint_all_pads(int color) {
    for (int r = 1; r <= 8; r++)
        for (int c = 1; c <= 8; c++)
            set_note_led(r * 10 + c, color);
    for (int i = 91; i <= 98; i++)
        set_cc_led(i, color);
    int right[] = {19, 29, 39, 49, 59, 69, 79, 89};
    for (int i = 0; i < 8; i++)
        set_cc_led(right[i], color);
}

static void init_leds(void) {
    paint_all_pads(COLOR_DIM);
    for (int i = 0; i < MAX_NOTES; i++)
        if (note_to_key[i]) set_note_led(i, note_led_idle[i]);
    for (int i = 0; i < MAX_CC; i++)
        if (cc_to_key[i]) set_cc_led(i, cc_led_idle[i]);
}

static void clear_leds(void) {
    paint_all_pads(COLOR_OFF);
}

/* ── main ── */

int main(int argc, char **argv) {
    char dev_in[64] = "";
    char dev_out[64] = "";
    const char *keymap_path = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-d") == 0 && i+1 < argc) {
            strncpy(dev_in, argv[++i], sizeof(dev_in)-1);
            strncpy(dev_out, dev_in, sizeof(dev_out)-1);
        }
        else if (strcmp(argv[i], "-m") == 0 && i+1 < argc) keymap_path = argv[++i];
        else {
            fprintf(stderr, "usage: %s [-d hw:X,0,1] [-m keymap.conf]\n", argv[0]);
            return (strcmp(argv[i], "-h") == 0) ? 0 : 1;
        }
    }

    if (!dev_in[0] && find_launchpad(dev_in, dev_out, sizeof(dev_in)) < 0) {
        fprintf(stderr, "Launchpad not found. Connect it or specify -d hw:X,0,1\n");
        return 1;
    }
    printf("midi in:  %s\n", dev_in);
    printf("midi out: %s\n", dev_out);

    if (keymap_path) {
        if (load_keymap_file(keymap_path) < 0) {
            fprintf(stderr, "cannot load %s, falling back to defaults\n", keymap_path);
            load_default_keymap();
        }
    } else {
        load_default_keymap();
    }

    int err;
    if ((err = snd_rawmidi_open(&midi_in, &midi_out, dev_in, SND_RAWMIDI_NONBLOCK)) < 0) {
        fprintf(stderr, "cannot open %s: %s\n", dev_in, snd_strerror(err));
        return 1;
    }

    /* small input buffer for low latency */
    snd_rawmidi_params_t *params;
    snd_rawmidi_params_alloca(&params);
    snd_rawmidi_params_current(midi_in, params);
    snd_rawmidi_params_set_buffer_size(midi_in, params, 32);
    snd_rawmidi_params(midi_in, params);

    /* drain stale data */
    {
        unsigned char junk[64];
        while (snd_rawmidi_read(midi_in, junk, sizeof(junk)) > 0);
    }

    enter_programmer_mode();
    snd_rawmidi_drain(midi_out);
    usleep(200000);

    uinput_fd = setup_uinput();
    if (uinput_fd < 0) { snd_rawmidi_close(midi_in); snd_rawmidi_close(midi_out); return 1; }

    signal(SIGINT,  on_signal);
    signal(SIGTERM, on_signal);

    set_realtime();
    init_leds();
    snd_rawmidi_drain(midi_out);

    printf("ready (ctrl+c to quit)\n");

    struct pollfd pfd;
    snd_rawmidi_poll_descriptors(midi_in, &pfd, 1);

    struct midi_parser parser = {0};
    unsigned char st, d1, d2;

    while (running) {
        if (poll(&pfd, 1, 100) <= 0) continue;

        unsigned char buf[64];
        int n = snd_rawmidi_read(midi_in, buf, sizeof(buf));
        if (n <= 0) continue;

        for (int i = 0; i < n; i++) {
            if (!midi_parse(&parser, buf[i], &st, &d1, &d2)) continue;

            int cmd = st & 0xF0;

            if ((cmd == 0x90 || cmd == 0x80) && d1 < MAX_NOTES && note_to_key[d1]) {
                int press = (cmd == 0x90 && d2 > 0);
                emit_key(note_to_key[d1], press);
                set_note_led(d1, press ? note_led_pressed[d1] : note_led_idle[d1]);
            }
            else if (cmd == 0xB0 && d1 < MAX_CC && cc_to_key[d1]) {
                int press = (d2 > 0);
                emit_key(cc_to_key[d1], press);
                set_cc_led(d1, press ? cc_led_pressed[d1] : cc_led_idle[d1]);
            }
        }
    }

    printf("\nshutting down...\n");
    clear_leds();
    if (midi_out) snd_rawmidi_drain(midi_out);

    ioctl(uinput_fd, UI_DEV_DESTROY);
    close(uinput_fd);
    snd_rawmidi_close(midi_in);
    if (midi_out) snd_rawmidi_close(midi_out);

    return 0;
}
