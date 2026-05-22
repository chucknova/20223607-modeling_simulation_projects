CC      = gcc
CFLAGS  = -Wall -Wextra -std=c11 -O2
LIBS    = -lm
TARGET  = rng
SRC     = rng.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LIBS)

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$(TARGET) 1000 42 10