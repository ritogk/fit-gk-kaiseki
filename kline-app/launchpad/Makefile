CC      = gcc
CFLAGS  = -O2 -Wall -Wextra
LDFLAGS = -lasound
TARGET  = launchpad-kb

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)

install:
	install -m 755 $(TARGET) /usr/local/bin/

.PHONY: clean install
